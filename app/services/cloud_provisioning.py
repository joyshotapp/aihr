from __future__ import annotations

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def ensure_pinecone_index(create_missing: bool = False) -> dict[str, Any]:
    api_key = getattr(settings, "PINECONE_API_KEY", "")
    index_name = getattr(settings, "PINECONE_INDEX_NAME", "aihr-vectors")
    dimension = getattr(settings, "EMBEDDING_DIMENSION", 1024)
    if not api_key:
        return {"resource": "pinecone_index", "status": "skipped", "reason": "missing_api_key"}

    try:
        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=api_key)
        existing = [idx.name for idx in pc.list_indexes()]
        if index_name in existing:
            return {"resource": "pinecone_index", "status": "exists", "name": index_name}
        if not create_missing:
            logger.warning("Pinecone 索引 '%s' 不存在，請先執行 provision 腳本", index_name)
            return {"resource": "pinecone_index", "status": "missing", "name": index_name}

        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logger.info("Pinecone 索引 '%s' 建立完成", index_name)
        return {"resource": "pinecone_index", "status": "created", "name": index_name}
    except Exception as exc:  # pragma: no cover - network/API dependent
        logger.warning("Pinecone 索引檢查/建立失敗: %s", exc)
        return {"resource": "pinecone_index", "status": "error", "reason": str(exc)}


def ensure_r2_bucket(create_missing: bool = False) -> dict[str, Any]:
    endpoint = getattr(settings, "R2_ENDPOINT", "")
    access_key = getattr(settings, "R2_ACCESS_KEY_ID", "")
    secret_key = getattr(settings, "R2_SECRET_ACCESS_KEY", "")
    bucket = getattr(settings, "R2_BUCKET", "aihr-uploads")
    if not all([endpoint, access_key, secret_key]):
        return {"resource": "r2_bucket", "status": "skipped", "reason": "missing_credentials"}

    try:
        import boto3

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )
        existing = [item["Name"] for item in s3.list_buckets().get("Buckets", [])]
        if bucket in existing:
            return {"resource": "r2_bucket", "status": "exists", "name": bucket}
        if not create_missing:
            logger.warning("R2 bucket '%s' 不存在，請先執行 provision 腳本", bucket)
            return {"resource": "r2_bucket", "status": "missing", "name": bucket}

        s3.create_bucket(Bucket=bucket)
        logger.info("R2 bucket '%s' 建立完成", bucket)
        return {"resource": "r2_bucket", "status": "created", "name": bucket}
    except Exception as exc:  # pragma: no cover - network/API dependent
        logger.warning("R2 bucket 檢查/建立失敗: %s", exc)
        return {"resource": "r2_bucket", "status": "error", "reason": str(exc)}


def provision_cloud_resources(create_missing: bool) -> list[dict[str, Any]]:
    return [
        ensure_pinecone_index(create_missing=create_missing),
        ensure_r2_bucket(create_missing=create_missing),
    ]
