"""
UniHR 進階知識庫檢索服務 (Advanced Knowledge Base Retriever)

功能：
  - 語意檢索（pgvector + Voyage Embedding）
  - 關鍵字檢索（BM25）
  - 混合檢索（語意 + BM25 + RRF 融合）
  - 相似度閾值過濾
  - 重排序（Voyage Rerank）
  - Redis 查詢快取
  - 批次搜尋
"""

import hashlib
import json
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

import voyageai

from app.config import settings
from app.db.session import create_session
from app.models.document import DocumentChunk, Document
from app.services.circuit_breaker import (
    voyage_breaker,
    pinecone_breaker,
    CircuitOpenError,
)

logger = logging.getLogger(__name__)

# ── 可選依賴 ──
try:
    import redis as redis_lib

    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False

try:
    from rank_bm25 import BM25Okapi

    _HAS_BM25 = True
except ImportError:
    _HAS_BM25 = False

try:
    import jieba

    _HAS_JIEBA = True
except ImportError:
    _HAS_JIEBA = False

try:
    import openai as openai_lib

    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False

try:
    from pinecone import Pinecone as PineconeClient

    _HAS_PINECONE = True
except ImportError:
    _HAS_PINECONE = False

# ── 模組級 BM25 索引快取（跨請求復用，避免每次查詢全量載入）──
import time as _time

_BM25_CACHE: Dict[str, Dict[str, Any]] = {}  # tenant_id → {bm25, chunks, doc_map, built_at}
_BM25_CACHE_TTL = 300  # 5 分鐘 TTL（安全網）


class KnowledgeBaseRetriever:
    """
    進階知識庫檢索服務。

    支援三種檢索模式：
      1. ``semantic``  – 純語意向量檢索（預設）
      2. ``keyword``   – 純 BM25 關鍵字檢索
      3. ``hybrid``    – 語意 + BM25 + RRF 融合 + 重排序
    """

    def __init__(self):
        if not settings.VOYAGE_API_KEY:
            raise ValueError("VOYAGE_API_KEY 未設定")

        self.voyage_client = voyageai.Client(api_key=settings.VOYAGE_API_KEY)

        # Gemini client（用於 HyDE 查詢擴展，透過 OpenAI 相容端點）
        self._openai = None
        gemini_key = getattr(settings, "GEMINI_API_KEY", "")
        if _HAS_OPENAI and gemini_key:
            self._openai = openai_lib.OpenAI(
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )

        # Redis 快取
        self._redis = None
        if _HAS_REDIS and getattr(settings, "REDIS_HOST", None):
            try:
                self._redis = redis_lib.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=getattr(settings, "REDIS_PASSWORD", None) or None,
                    db=1,  # 用 db=1 做檢索快取（db=0 給 Celery）
                    decode_responses=True,
                    socket_connect_timeout=2,
                )
                self._redis.ping()
            except Exception:
                logger.warning("Redis 連線失敗，檢索快取已停用")
                self._redis = None
        # Pinecone 索引（語意向量檢索）
        self._pinecone_index = None
        if _HAS_PINECONE and getattr(settings, "PINECONE_API_KEY", ""):
            try:
                pc = PineconeClient(api_key=settings.PINECONE_API_KEY)
                self._pinecone_index = pc.Index(settings.PINECONE_INDEX_NAME)
            except Exception as e:
                logger.warning(f"Pinecone 初始化失敗: {e}")

    # ─────────────────────────────────────────────
    # 公開 API
    # ─────────────────────────────────────────────

    def search(
        self,
        tenant_id: UUID,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid",
        min_score: float = settings.RETRIEVAL_MIN_SCORE,
        rerank: bool = True,
        use_cache: bool = True,
        filter_dict: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        在租戶知識庫中搜尋相關內容。

        Args:
            tenant_id: 租戶 ID
            query: 查詢問題
            top_k: 返回結果數量
            mode: 檢索模式 (semantic / keyword / hybrid)
            min_score: 相似度閾值（0.0 ~ 1.0）
            rerank: 是否使用重排序
            use_cache: 是否使用 Redis 快取
            filter_dict: 額外的 metadata 過濾條件

        Returns:
            匹配結果列表，每個包含 content / score / metadata 等。
        """
        # 1. 快取檢查
        if use_cache and self._redis:
            cached = self._cache_get(tenant_id, query, mode, top_k, min_score)
            if cached is not None:
                return cached

        # 1.5 Query Expansion（HyDE 假設文件生成）
        expanded_query = None
        if mode in {"semantic", "hybrid"}:
            expanded_query = self._expand_query(query)

        # 2. 執行檢索（語意使用擴展查詢，BM25 保持原始 query）
        if mode == "keyword":
            results = self._keyword_search(tenant_id, query, top_k=top_k * 2)
        elif mode == "hybrid":
            semantic_query = expanded_query or query
            results = self._hybrid_search(
                tenant_id,
                semantic_query=semantic_query,
                keyword_query=query,
                top_k=top_k * 2,
                filter_dict=filter_dict,
            )
        else:  # semantic
            search_query = expanded_query or query
            results = self._semantic_search(
                tenant_id,
                search_query,
                top_k=top_k * 2,
                filter_dict=filter_dict,
            )

        # 3. 閾值過濾
        if min_score > 0:
            results = [r for r in results if r.get("score", 0) >= min_score]

        # 4. 重排序
        if rerank and len(results) > 1:
            results = self._rerank(query, results, top_k=top_k)
        else:
            results = results[:top_k]

        # 5. 寫入快取
        if use_cache and self._redis:
            self._cache_set(tenant_id, query, mode, top_k, min_score, results)

        return results

    def batch_search(
        self,
        tenant_id: UUID,
        queries: List[str],
        top_k: int = 5,
        mode: str = "hybrid",
    ) -> List[List[Dict[str, Any]]]:
        """批次搜尋"""
        return [self.search(tenant_id, q, top_k=top_k, mode=mode) for q in queries]

    def get_stats(self, tenant_id: UUID) -> Dict[str, Any]:
        """獲取租戶知識庫統計資訊（Pinecone namespace stats）"""
        if self._pinecone_index:
            try:
                stats = self._pinecone_index.describe_index_stats()
                ns_stats = stats.namespaces.get(str(tenant_id), {})
                vector_count = getattr(ns_stats, "vector_count", 0)
                return {
                    "exists": vector_count > 0,
                    "vector_count": vector_count,
                    "total_chunks": vector_count,
                    "dimension": settings.EMBEDDING_DIMENSION,
                    "backend": "pinecone",
                }
            except Exception as e:
                logger.warning(f"Pinecone stats 查詢失敗: {e}")

        # Fallback: PostgreSQL chunk count
        db = create_session(tenant_id=tenant_id)
        try:
            total_chunks = db.query(DocumentChunk).filter(DocumentChunk.tenant_id == tenant_id).count()
            return {
                "exists": total_chunks > 0,
                "vector_count": 0,
                "total_chunks": total_chunks,
                "dimension": settings.EMBEDDING_DIMENSION,
                "backend": "pinecone",
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}
        finally:
            db.close()

    # ─────────────────────────────────────────────
    # 語意檢索
    # ─────────────────────────────────────────────

    def _semantic_search(
        self,
        tenant_id: UUID,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """使用 Pinecone 進行語意向量檢索，Pinecone 不可用時降級至 pgvector"""
        try:
            # 1. 取得查詢向量
            embed_result = voyage_breaker.call(
                self.voyage_client.embed,
                [query],
                model=settings.VOYAGE_MODEL,
                input_type="query",
            )
            query_embedding = embed_result.embeddings[0]

            # ── Langfuse: 記錄 Voyage query embedding token 數 ──
            from app.services.langfuse_client import get_langfuse

            lf = get_langfuse()
            if lf:
                total_tokens = getattr(embed_result, "total_tokens", None) or 0
                lf.generation(
                    name="voyage_embed_query",
                    model=settings.VOYAGE_MODEL,
                    input=query[:200],
                    metadata={"input_type": "query", "total_tokens": total_tokens},
                    usage={"total_tokens": total_tokens} if total_tokens else None,
                )
        except Exception as e:
            logger.error(f"Voyage 嵌入查詢失敗，語意檢索不可用: {e}")
            return []

        # 2. 嘗試 Pinecone
        if self._pinecone_index:
            try:
                pinecone_filter: Dict = {}
                if filter_dict:
                    for k, v in filter_dict.items():
                        pinecone_filter[k] = {"$in": [str(i) for i in v]} if isinstance(v, list) else {"$eq": str(v)}

                response = pinecone_breaker.call(
                    self._pinecone_index.query,
                    vector=query_embedding,
                    top_k=top_k,
                    namespace=str(tenant_id),
                    include_metadata=True,
                    filter=pinecone_filter if pinecone_filter else None,
                )

                results = []
                for match in response.matches:
                    meta = match.metadata or {}
                    results.append(
                        {
                            "id": match.id,
                            "score": round(float(match.score), 4),
                            "content": meta.get("text", ""),
                            "document_id": meta.get("document_id", ""),
                            "filename": meta.get("filename", ""),
                            "chunk_index": int(meta.get("chunk_index", 0)),
                            "metadata": meta,
                            "source": "semantic",
                        }
                    )
                return results
            except CircuitOpenError:
                logger.warning("Pinecone 斷路器開啟，降級至 pgvector 語意檢索")
            except Exception as e:
                logger.warning(f"Pinecone 查詢失敗，降級至 pgvector: {e}")
        else:
            logger.info("Pinecone 未初始化，使用 pgvector 語意檢索")

        # 3. Fallback: pgvector cosine similarity
        return self._pgvector_semantic_search(
            tenant_id,
            query_embedding,
            top_k,
            filter_dict,
        )

    def _pgvector_semantic_search(
        self,
        tenant_id: UUID,
        query_embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """使用 PostgreSQL pgvector 進行語意向量檢索（Pinecone fallback）"""
        db = create_session(tenant_id=tenant_id)
        try:
            # cosine_distance 回傳 0~2，轉換為 similarity = 1 - distance
            distance_col = DocumentChunk.embedding.cosine_distance(query_embedding)

            query_obj = db.query(DocumentChunk, distance_col.label("distance")).filter(
                DocumentChunk.tenant_id == tenant_id,
                DocumentChunk.embedding.isnot(None),
            )

            if filter_dict:
                if "document_id" in filter_dict:
                    val = filter_dict["document_id"]
                    if isinstance(val, list):
                        query_obj = query_obj.filter(DocumentChunk.document_id.in_([UUID(str(v)) for v in val]))
                    else:
                        query_obj = query_obj.filter(DocumentChunk.document_id == UUID(str(val)))

            rows = query_obj.order_by(distance_col.asc()).limit(top_k).all()

            # 取得文件名映射
            doc_ids = list({row[0].document_id for row in rows})
            doc_map: Dict = {}
            if doc_ids:
                docs = (
                    db.query(Document)
                    .filter(
                        Document.id.in_(doc_ids),
                        Document.tenant_id == tenant_id,
                    )
                    .all()
                )
                doc_map = {d.id: d.filename for d in docs}

            results = []
            for chunk, distance in rows:
                similarity = max(0.0, 1.0 - float(distance))
                results.append(
                    {
                        "id": str(chunk.id),
                        "score": round(similarity, 4),
                        "content": chunk.text or "",
                        "document_id": str(chunk.document_id),
                        "filename": doc_map.get(chunk.document_id, ""),
                        "chunk_index": chunk.chunk_index,
                        "metadata": chunk.metadata_json or {},
                        "source": "semantic_pgvector",
                    }
                )

            logger.info("pgvector 語意檢索完成: %d 筆結果", len(results))
            return results
        except Exception as e:
            logger.error(f"pgvector 語意檢索失敗: {e}")
            return []
        finally:
            db.close()

    # ─────────────────────────────────────────────
    # BM25 關鍵字檢索
    # ─────────────────────────────────────────────

    def _keyword_search(
        self,
        tenant_id: UUID,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """使用 BM25 在 DB chunks 上做關鍵字檢索（帶模組級快取）"""
        if not _HAS_BM25:
            logger.warning("rank_bm25 未安裝，關鍵字檢索不可用")
            return []

        try:
            cache_key = str(tenant_id)
            now = _time.monotonic()
            cached = _BM25_CACHE.get(cache_key)

            if cached and (now - cached["built_at"]) < _BM25_CACHE_TTL:
                bm25 = cached["bm25"]
                chunks = cached["chunks"]
                doc_map = cached["doc_map"]
            else:
                # 重建 BM25 索引
                db = create_session(tenant_id=tenant_id)
                try:
                    chunks = db.query(DocumentChunk).filter(DocumentChunk.tenant_id == tenant_id).all()
                    if not chunks:
                        return []

                    doc_ids = list({c.document_id for c in chunks})
                    docs = (
                        db.query(Document)
                        .filter(
                            Document.id.in_(doc_ids),
                            Document.tenant_id == tenant_id,
                        )
                        .all()
                    )
                    doc_map = {d.id: d.filename for d in docs}
                finally:
                    db.close()

                corpus = [self._tokenize(c.text or "") for c in chunks]
                bm25 = BM25Okapi(corpus)

                _BM25_CACHE[cache_key] = {
                    "bm25": bm25,
                    "chunks": chunks,
                    "doc_map": doc_map,
                    "built_at": now,
                }
                logger.debug("BM25 索引已重建: tenant=%s, chunks=%d", tenant_id, len(chunks))

            query_tokens = self._tokenize(query)
            scores = bm25.get_scores(query_tokens)

            ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

            results = []
            max_score = max(scores) if max(scores) > 0 else 1.0
            for idx, score in ranked:
                if score <= 0:
                    continue
                chunk = chunks[idx]
                results.append(
                    {
                        "id": str(chunk.id),
                        "score": round(score / max_score, 4),
                        "content": chunk.text or "",
                        "document_id": str(chunk.document_id),
                        "filename": doc_map.get(chunk.document_id, ""),
                        "chunk_index": chunk.chunk_index,
                        "metadata": {},
                        "source": "keyword",
                    }
                )
            return results
        except Exception as e:
            logger.error(f"BM25 關鍵字檢索錯誤: {e}")
            return []

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """中英文混合分詞（jieba 詞級分詞 + 英文空格分詞）"""
        if _HAS_JIEBA:
            # jieba 精確模式：「勞動基準法」→「勞動」「基準」「法」
            # 比逐字分詞精確度高很多
            tokens = list(jieba.cut(text, cut_all=False))
            return [t.strip().lower() for t in tokens if t.strip() and len(t.strip()) > 0]

        # Fallback：逐字 + 英文按詞
        tokens: List[str] = []
        current_word = ""
        for char in text:
            if "\u4e00" <= char <= "\u9fff":
                if current_word:
                    tokens.append(current_word.lower())
                    current_word = ""
                tokens.append(char)
            elif char.isalnum():
                current_word += char
            else:
                if current_word:
                    tokens.append(current_word.lower())
                    current_word = ""
        if current_word:
            tokens.append(current_word.lower())
        return [t for t in tokens if len(t.strip()) > 0]

    # ─────────────────────────────────────────────
    # 混合檢索（RRF 融合）
    # ─────────────────────────────────────────────

    def _hybrid_search(
        self,
        tenant_id: UUID,
        semantic_query: str,
        keyword_query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict] = None,
        rrf_k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        混合檢索：語意 + BM25，使用 Reciprocal Rank Fusion (RRF) 合併。

        RRF 公式: score = Σ 1 / (k + rank)
        """
        semantic_results = self._semantic_search(tenant_id, semantic_query, top_k=top_k, filter_dict=filter_dict)
        keyword_results = self._keyword_search(tenant_id, keyword_query, top_k=top_k)

        # 如果只有一種來源有結果，直接返回
        if not keyword_results:
            return semantic_results
        if not semantic_results:
            return keyword_results

        # RRF 融合 — 使用 document_id:chunk_index 作為統一 key
        rrf_scores: Dict[str, float] = {}
        result_map: Dict[str, Dict[str, Any]] = {}

        def _canonical_key(r: Dict[str, Any], fallback: str) -> str:
            doc_id = r.get("document_id", "")
            ci = r.get("chunk_index")
            if doc_id and ci is not None:
                return f"{doc_id}:{ci}"
            return r.get("id", fallback)

        for rank, r in enumerate(semantic_results):
            key = _canonical_key(r, f"sem-{rank}")
            rrf_scores[key] = rrf_scores.get(key, 0) + 1.0 / (rrf_k + rank + 1)
            result_map[key] = r

        for rank, r in enumerate(keyword_results):
            key = _canonical_key(r, f"kw-{rank}")
            rrf_scores[key] = rrf_scores.get(key, 0) + 1.0 / (rrf_k + rank + 1)
            if key not in result_map:
                result_map[key] = r

        # 按 RRF 分數排序
        sorted_keys = sorted(rrf_scores, key=lambda k: rrf_scores[k], reverse=True)

        merged: List[Dict[str, Any]] = []
        for key in sorted_keys[:top_k]:
            item = result_map[key].copy()
            item["score"] = round(rrf_scores[key], 6)
            item["source"] = "hybrid"
            merged.append(item)

        return merged

    # ─────────────────────────────────────────────
    # 重排序（Voyage Rerank）
    # ─────────────────────────────────────────────

    def _rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        使用 Voyage AI Rerank API 重新排序結果。
        若 API 不可用則回退到原始排序。
        """
        if not results:
            return results

        try:
            documents = [r.get("content", "")[:2000] for r in results]

            reranked = voyage_breaker.call(
                self.voyage_client.rerank,
                query=query,
                documents=documents,
                model="rerank-2",
                top_k=min(top_k, len(documents)),
            )

            reranked_results: List[Dict[str, Any]] = []
            for item in reranked.results:
                original = results[item.index].copy()
                original["score"] = round(item.relevance_score, 4)
                original["reranked"] = True
                reranked_results.append(original)

            # ── Langfuse: 記錄 rerank token 數 ──
            from app.services.langfuse_client import get_langfuse

            lf = get_langfuse()
            if lf:
                total_tokens = getattr(reranked, "total_tokens", None) or 0
                lf.generation(
                    name="voyage_rerank",
                    model="rerank-2",
                    input=query[:200],
                    metadata={
                        "num_documents": len(documents),
                        "top_k": top_k,
                        "total_tokens": total_tokens,
                    },
                    usage={"total_tokens": total_tokens} if total_tokens else None,
                )

            return reranked_results

        except Exception as e:
            logger.warning(f"重排序失敗，回退到原始排序: {e}")
            return results[:top_k]

    # ─────────────────────────────────────────────
    # Redis 快取
    # ─────────────────────────────────────────────

    _CACHE_TTL = 300  # 5 分鐘

    def _cache_key(self, tenant_id: UUID, query: str, mode: str, top_k: int, min_score: float) -> str:
        raw = f"{tenant_id}:{query}:{mode}:{top_k}:{min_score}"
        h = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"kb:search:{tenant_id}:{h}"

    def _cache_get(
        self, tenant_id: UUID, query: str, mode: str, top_k: int, min_score: float
    ) -> Optional[List[Dict[str, Any]]]:
        if not self._redis:
            return None
        try:
            key = self._cache_key(tenant_id, query, mode, top_k, min_score)
            cached = self._redis.get(key)
            if cached:
                logger.debug(f"快取命中: {key}")
                return json.loads(cached)
        except Exception:
            pass
        return None

    def _cache_set(
        self,
        tenant_id: UUID,
        query: str,
        mode: str,
        top_k: int,
        min_score: float,
        results: List[Dict[str, Any]],
    ):
        if not self._redis:
            return
        try:
            key = self._cache_key(tenant_id, query, mode, top_k, min_score)
            self._redis.setex(key, self._CACHE_TTL, json.dumps(results, default=str))
        except Exception:
            pass

    def invalidate_cache(self, tenant_id: UUID):
        """清除租戶的所有檢索快取（文件新增/刪除時呼叫）"""
        # 清除 BM25 模組級快取
        _BM25_CACHE.pop(str(tenant_id), None)

        if not self._redis:
            return
        try:
            cursor = 0
            match_pattern = f"kb:search:{tenant_id}:*"
            while True:
                cursor, keys = self._redis.scan(cursor, match=match_pattern, count=100)
                if keys:
                    self._redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            pass

    # ─────────────────────────────────────────────
    # HyDE 查詢擴展（Hypothetical Document Embeddings）
    # ─────────────────────────────────────────────

    def _expand_query(self, query: str) -> Optional[str]:
        """
        HyDE 查詢擴展（已停用）。

        效能分析：此方法為同步阻塞 OpenAI 呼叫（~1.1s），且 search() 是
        同步函式，在 asyncio.gather() 中無法真正並行，導致每次問答
        額外增加 2.2s 延遲。在 voyage-4-lite + rerank 已有效的情況下，
        HyDE 的精度增益不足以抵消延遲代價，故停用。
        """
        return None
