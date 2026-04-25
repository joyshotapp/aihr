"""
UniHR Admin API 微服務（T4-18）
================================

獨立 FastAPI 應用，將 /admin/* 和 /analytics/* 從主服務拆出。

特性：
- 獨立 Docker 容器，只監聽內網
- 可指向 PostgreSQL Read Replica（讀副本）
- 獨立 Redis 快取實例
- 內部 service token 認證

啟動方式：
    uvicorn admin_service.main:app --host 0.0.0.0 --port 8001
"""

import os
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from app.observability.metrics import (
    metrics_content_type,
    observe_request,
    record_unhandled_exception,
    render_metrics,
    track_in_progress,
)
from app.observability.sentry import init_sentry

logger = logging.getLogger("unihr.admin_service")
SERVICE_NAME = "admin-api"
init_sentry(SERVICE_NAME)

# ---------------------------------------------------------------------------
# Service Token 認證（內部服務間通訊）
# ---------------------------------------------------------------------------
ADMIN_SERVICE_TOKEN = os.getenv("ADMIN_SERVICE_TOKEN", "")


async def verify_service_token(request: Request):
    """
    驗證內部 service token。
    Admin 微服務不直接暴露給外部，由 API Gateway 轉發並附帶 service token。
    """
    if not ADMIN_SERVICE_TOKEN:
        return  # 開發環境不驗證

    token = request.headers.get("X-Service-Token", "")
    if token != ADMIN_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid service token",
        )


def _is_token_check_required(request: Request) -> bool:
    if not ADMIN_SERVICE_TOKEN:
        return False
    if request.method == "OPTIONS":
        return False
    path = request.url.path
    return not (
        path == "/health"
        or path == "/"
        or path == "/metrics"
        or path.startswith("/docs")
        or path.startswith("/openapi.json")
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Admin Service starting...")
    yield
    logger.info("🛑 Admin Service shutting down...")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="UniHR Admin Service",
    description="平台管理 API 微服務（內部使用）",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def enforce_service_token(request: Request, call_next):
    start = time.perf_counter()
    track_in_progress(SERVICE_NAME, 1)
    if _is_token_check_required(request):
        await verify_service_token(request)
    try:
        response = await call_next(request)
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        record_unhandled_exception(SERVICE_NAME, request.method, request.url.path)
        observe_request(SERVICE_NAME, request.method, request.url.path, 500, elapsed)
        raise
    finally:
        track_in_progress(SERVICE_NAME, -1)

    elapsed = (time.perf_counter() - start) * 1000
    observe_request(SERVICE_NAME, request.method, request.url.path, response.status_code, elapsed)
    return response

# CORS（僅允許 admin frontend）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("ADMIN_FRONTEND_URL", "http://localhost:3002"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 路由掛載
# ---------------------------------------------------------------------------
# 微服務化後，直接 import 原有的 admin 和 analytics router。
# 當部署為獨立服務時，主服務 (app/main.py) 的 /admin /analytics
# 會改為 reverse proxy 到此服務。

from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.analytics import router as analytics_router

app.include_router(admin_router, prefix="/api/v1/admin", tags=["platform-admin"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["cost-analytics"])


# ---------------------------------------------------------------------------
# 健康檢查
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {
        "service": "admin-api",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "service": "UniHR Admin API Microservice",
        "docs": "/docs",
    }


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(content=render_metrics(), media_type=metrics_content_type())
