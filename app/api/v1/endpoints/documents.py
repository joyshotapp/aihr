import os
import asyncio
import zipfile
import io
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
import boto3

from app.api import deps
from app.api.deps_permissions import (
    check_document_permission,
    can_access_document_by_department,
)
from app.crud import crud_document
from app.models.user import User
from app.models.document import Document as DocumentModel
from app.schemas.document import Document, DocumentCreate
from app.config import settings
from app.services.file_scan import FileScanError, MalwareDetectedError, scan_bytes
from app.tasks.document_tasks import process_document_task
from app.services.quota_enforcement import enforce_document_quota

router = APIRouter()


def _get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


@router.get("/", response_model=List[Document])
def list_documents(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    獲取當前租戶的文件列表，可依部門篩選
    """
    if department_id:
        if not can_access_document_by_department(current_user, department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="無權限存取此部門的文件",
            )
        documents = (
            db.query(DocumentModel)
            .filter(
                DocumentModel.tenant_id == current_user.tenant_id,
                DocumentModel.department_id == department_id,
            )
            .order_by(DocumentModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:
        if current_user.is_superuser or current_user.role in ["owner", "admin", "hr"]:
            documents = crud_document.get_by_tenant(db, tenant_id=current_user.tenant_id, skip=skip, limit=limit)
        else:
            q = db.query(DocumentModel).filter(DocumentModel.tenant_id == current_user.tenant_id)
            if current_user.department_id is None:
                q = q.filter(DocumentModel.department_id.is_(None))
            else:
                q = q.filter(
                    or_(
                        DocumentModel.department_id.is_(None),
                        DocumentModel.department_id == current_user.department_id,
                    )
                )
            documents = q.order_by(DocumentModel.created_at.desc()).offset(skip).limit(limit).all()
    return documents


@router.post("/upload", response_model=Document)
async def upload_document(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
    _quota: None = Depends(enforce_document_quota),
) -> Any:
    """
    上傳文件
    - 支援 PDF(文字/掃描/表格)、DOCX、DOC、TXT、Excel、CSV、HTML、Markdown、RTF、JSON、圖片
    - 非同步處理：解析、切片、向量化
    - 權限：owner, admin, hr
    """
    # 權限檢查
    check_document_permission(current_user, "create")

    # 1. 驗證文件類型（支援所有 Phase 0-2 格式）
    from app.services.document_parser import DocumentParser, SUPPORTED_FORMATS

    allowed_extensions = set(SUPPORTED_FORMATS.keys())
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支援的文件類型: {file_ext}。支援的類型: {', '.join(sorted(allowed_extensions))}",
        )

    # 2. 偵測文件類型
    try:
        file_type = DocumentParser.detect_file_type(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 3. Streaming 讀取並檢查文件大小（避免大檔案一次載入記憶體）
    CHUNK_READ_SIZE = 1024 * 1024  # 1MB per read
    chunks_buffer = []
    file_size = 0
    while True:
        chunk = await file.read(CHUNK_READ_SIZE)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件過大（超過 {settings.MAX_FILE_SIZE / 1024 / 1024:.0f} MB 上限）",
            )
        chunks_buffer.append(chunk)

    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件為空")

    loop = asyncio.get_event_loop()
    file_content = b"".join(chunks_buffer)
    del chunks_buffer  # 釋放暫存

    # 4. 惡意檔案掃描
    try:
        await loop.run_in_executor(None, lambda: scan_bytes(file_content, file.filename))
    except MalwareDetectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"檔案未通過安全掃描: {exc.signature}",
        )
    except FileScanError:
        if settings.CLAMAV_FAIL_CLOSED:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="檔案安全掃描服務暫時不可用，請稍後再試",
            )

    # 5. 建立文件記錄
    doc_in = DocumentCreate(filename=file.filename, file_type=file_type)

    document = crud_document.create(
        db,
        obj_in=doc_in,
        tenant_id=current_user.tenant_id,
        uploaded_by=current_user.id,
        file_size=file_size,
    )

    # 6. 上传文件到 Cloudflare R2
    r2_key = f"{current_user.tenant_id}/{document.id}{file_ext}"
    await loop.run_in_executor(
        None,
        lambda: _get_r2_client().put_object(
            Bucket=settings.R2_BUCKET,
            Key=r2_key,
            Body=file_content,
        ),
    )

    # 7. 觸發背景任務處理（按檔案大小選擇佇列）
    queue_name = "bulk" if file_size > 5 * 1024 * 1024 else "celery"
    process_document_task.apply_async(
        kwargs={
            "document_id": str(document.id),
            "file_path": r2_key,
            "tenant_id": str(current_user.tenant_id),
        },
        queue=queue_name,
    )

    return document


@router.get("/{document_id}", response_model=Document)
def get_document(
    *,
    db: Session = Depends(deps.get_db),
    document_id: UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    獲取文件詳情
    """
    document = (
        crud_document.get(db, document_id=document_id, _internal=True)
        if current_user.is_superuser
        else crud_document.get_for_tenant(
            db,
            document_id=document_id,
            tenant_id=current_user.tenant_id,
        )
    )

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    return document


@router.delete("/{document_id}")
def delete_document(
    *,
    db: Session = Depends(deps.get_db),
    document_id: UUID,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    刪除文件
    - 刪除 Pinecone 向量
    - 刪除 PostgreSQL chunks（BM25 文字）
    - 刪除 R2 原始檔案
    - 刪除資料庫記錄
    - 權限：owner, admin, hr
    """
    # 權限檢查
    check_document_permission(current_user, "delete")

    document = (
        crud_document.get(db, document_id=document_id, _internal=True)
        if current_user.is_superuser
        else crud_document.get_for_tenant(
            db,
            document_id=document_id,
            tenant_id=current_user.tenant_id,
        )
    )

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    # 取得 chunks（供 Pinecone 刪除和 DB 清除用）
    chunks = (
        crud_document.get_chunks(db, document_id=document_id)
        if current_user.is_superuser
        else crud_document.get_chunks_for_tenant(
            db,
            document_id=document_id,
            tenant_id=current_user.tenant_id,
        )
    )

    # 刪除向量（Pinecone）
    try:
        vector_ids = [c.vector_id for c in chunks if c.vector_id]
        if vector_ids:
            from pinecone import Pinecone

            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            idx = pc.Index(settings.PINECONE_INDEX_NAME)
            idx.delete(ids=vector_ids, namespace=str(document.tenant_id))
    except Exception as e:
        print(f"刪除 Pinecone 向量失敗: {e}")

    # 刪除 PostgreSQL chunks
    try:
        for chunk in chunks:
            db.delete(chunk)
        db.commit()
    except Exception as e:
        print(f"刪除向量 chunks 失敗: {e}")

    # 刪除 R2 文件
    try:
        file_ext = os.path.splitext(document.filename)[1]
        r2_key = f"{document.tenant_id}/{document.id}{file_ext}"
        _get_r2_client().delete_object(Bucket=settings.R2_BUCKET, Key=r2_key)
    except Exception as e:
        print(f"刪除 R2 文件失敗: {e}")

    # 刪除資料庫記錄
    if current_user.is_superuser:
        crud_document.delete(db, document_id=document_id, tenant_id=document.tenant_id)
    else:
        crud_document.delete_for_tenant(
            db,
            document_id=document_id,
            tenant_id=current_user.tenant_id,
        )

    return {"message": "文件已刪除", "document_id": str(document_id)}


# ── Response schemas ──


class BatchUploadResult(BaseModel):
    total: int
    accepted: int
    rejected: int
    documents: List[Document]
    errors: List[Dict[str, str]]


class BatchProgressResponse(BaseModel):
    total: int
    completed: int
    failed: int
    in_progress: int
    pending: int
    documents: List[Document]


# ── Batch upload (P0) ──

MAX_BATCH_FILES = 100  # 單次批量上限


async def _process_single_upload(
    file_content: bytes,
    filename: str,
    db: Session,
    current_user: User,
) -> Document:
    """處理單一檔案上傳（共用邏輯）— 驗證、掃描、R2、Celery"""
    from app.services.document_parser import DocumentParser, SUPPORTED_FORMATS

    allowed_extensions = set(SUPPORTED_FORMATS.keys())
    file_ext = os.path.splitext(filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise ValueError(f"不支援的文件類型: {file_ext}。支援的類型: {', '.join(sorted(allowed_extensions))}")

    file_type = DocumentParser.detect_file_type(filename)

    if len(file_content) == 0:
        raise ValueError("文件為空")
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise ValueError(f"文件過大（超過 {settings.MAX_FILE_SIZE / 1024 / 1024:.0f} MB 上限）")

    loop = asyncio.get_event_loop()

    # 惡意檔案掃描
    try:
        await loop.run_in_executor(None, lambda: scan_bytes(file_content, filename))
    except MalwareDetectedError as exc:
        raise ValueError(f"檔案未通過安全掃描: {exc.signature}")
    except FileScanError:
        if settings.CLAMAV_FAIL_CLOSED:
            raise ValueError("檔案安全掃描服務暫時不可用")

    doc_in = DocumentCreate(filename=filename, file_type=file_type)
    document = crud_document.create(
        db,
        obj_in=doc_in,
        tenant_id=current_user.tenant_id,
        uploaded_by=current_user.id,
        file_size=len(file_content),
    )

    r2_key = f"{current_user.tenant_id}/{document.id}{file_ext}"
    await loop.run_in_executor(
        None,
        lambda: _get_r2_client().put_object(
            Bucket=settings.R2_BUCKET,
            Key=r2_key,
            Body=file_content,
        ),
    )

    # 按檔案大小選擇佇列
    queue_name = "bulk" if len(file_content) > 5 * 1024 * 1024 else "celery"
    process_document_task.apply_async(
        kwargs={
            "document_id": str(document.id),
            "file_path": r2_key,
            "tenant_id": str(current_user.tenant_id),
        },
        queue=queue_name,
    )

    return document


@router.post("/batch-upload", response_model=BatchUploadResult)
async def batch_upload_documents(
    *,
    db: Session = Depends(deps.get_db),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(deps.get_current_active_user),
    _quota: None = Depends(enforce_document_quota),
) -> Any:
    """
    批量上傳文件（最多 100 個檔案）。
    - 支援多個 UploadFile 或單一 .zip 檔案。
    - 每個檔案獨立驗證、掃描、觸發非同步處理。
    """
    check_document_permission(current_user, "create")

    pending_files: List[tuple] = []  # (filename, bytes)

    # ZIP 自動解壓
    if len(files) == 1 and files[0].filename and files[0].filename.lower().endswith(".zip"):
        zip_data = await files[0].read()
        if len(zip_data) > settings.MAX_FILE_SIZE * 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ZIP 檔案過大",
            )
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                for info in zf.infolist():
                    if info.is_dir() or info.filename.startswith("__MACOSX"):
                        continue
                    basename = os.path.basename(info.filename)
                    if not basename or basename.startswith("."):
                        continue
                    pending_files.append((basename, zf.read(info.name)))
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的 ZIP 檔案",
            )
    else:
        for f in files:
            content = await f.read()
            pending_files.append((f.filename or "unknown", content))

    if len(pending_files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批量上傳上限 {MAX_BATCH_FILES} 個檔案，本次有 {len(pending_files)} 個",
        )

    accepted: List[Document] = []
    errors: List[Dict[str, str]] = []

    for filename, content in pending_files:
        try:
            doc = await _process_single_upload(content, filename, db, current_user)
            accepted.append(Document.model_validate(doc))
        except (ValueError, Exception) as e:
            errors.append({"filename": filename, "error": str(e)})

    return BatchUploadResult(
        total=len(pending_files),
        accepted=len(accepted),
        rejected=len(errors),
        documents=accepted,
        errors=errors,
    )


# ── Batch progress tracking (P1) ──


@router.post("/batch-progress", response_model=BatchProgressResponse)
def batch_progress(
    *,
    db: Session = Depends(deps.get_db),
    document_ids: List[UUID],
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    查詢一批文件的處理進度。
    前端可輪詢此 API 觀察批量上傳的即時進度。
    """
    docs = (
        db.query(DocumentModel)
        .filter(
            DocumentModel.tenant_id == current_user.tenant_id,
            DocumentModel.id.in_(document_ids),
        )
        .all()
    )

    completed = sum(1 for d in docs if d.status == "completed")
    failed = sum(1 for d in docs if d.status == "failed")
    in_progress = sum(1 for d in docs if d.status in ("parsing", "embedding"))
    pending = sum(1 for d in docs if d.status == "pending")

    return BatchProgressResponse(
        total=len(docs),
        completed=completed,
        failed=failed,
        in_progress=in_progress,
        pending=pending,
        documents=[Document.model_validate(d) for d in docs],
    )


# ── Per-document processing progress (real-time via Redis) ──


class DocumentProgress(BaseModel):
    document_id: str
    status: str
    pct: int = 0
    detail: str = ""


@router.get("/{document_id}/progress", response_model=DocumentProgress)
def document_progress(
    document_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """查詢單一文件的即時處理進度"""
    doc = (
        db.query(DocumentModel)
        .filter(
            DocumentModel.tenant_id == current_user.tenant_id,
            DocumentModel.id == document_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")

    pct = 0
    detail = ""

    if doc.status == "completed":
        pct, detail = 100, "處理完成"
    elif doc.status == "failed":
        pct, detail = 0, doc.error_message or "處理失敗"
    else:
        try:
            import json
            from app.core.redis_client import get_redis_client

            r = get_redis_client()
            if r:
                data = r.get(f"doc_progress:{str(document_id)}")
                if data:
                    info = json.loads(data)
                    pct = info.get("pct", 0)
                    detail = info.get("detail", "")
        except Exception:
            pass

    return DocumentProgress(
        document_id=str(document_id),
        status=doc.status,
        pct=pct,
        detail=detail,
    )
