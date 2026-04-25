from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.api import api_router
from app.api.v2.api import api_v2_router
from app.middleware.versioning import APIVersionMiddleware, API_VERSIONS
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.ip_whitelist import AdminIPWhitelistMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.custom_domain import CustomDomainMiddleware
from app.middleware.csrf import CSRFMiddleware
from app.logging_config import setup_logging
from app.observability.metrics import metrics_content_type, render_metrics, snapshot
from app.observability.sentry import init_sentry
from app.services.cloud_provisioning import provision_cloud_resources
import logging

# ── Initialize structured logging ──
setup_logging()
init_sentry("backend-api")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    for result in provision_cloud_resources(create_missing=settings.AUTO_PROVISION_CLOUD_RESOURCES):
        logger.info("Cloud resource status: %s", result)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
cors_origins: list[str] = []
if not settings.is_production:
    cors_origins.extend(
        [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:8000",
        ]
    )
if settings.BACKEND_CORS_ORIGINS:
    if isinstance(settings.BACKEND_CORS_ORIGINS, str):
        cors_origins.extend([origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",") if origin.strip()])
    else:
        cors_origins.extend([str(origin) for origin in settings.BACKEND_CORS_ORIGINS])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "X-Requested-With"],
)

# API versioning middleware – adds deprecation headers to v1 responses
app.add_middleware(APIVersionMiddleware)

# Admin API IP whitelist (T4-4) – blocks non-whitelisted IPs from admin endpoints
app.add_middleware(AdminIPWhitelistMiddleware)

# Request logging middleware (T4-12) – request ID, timing, context
app.add_middleware(RequestLoggingMiddleware)

# Custom domain resolution middleware (T4-6) – resolves tenant from Host header
app.add_middleware(CustomDomainMiddleware)

# CSRF middleware – validates double-submit token for cookie-authenticated unsafe requests
app.add_middleware(CSRFMiddleware)

# Rate limiting middleware (only in non-development or when explicitly enabled)
if settings.RATE_LIMIT_ENABLED and not settings.is_development:
    app.add_middleware(RateLimitMiddleware)

# Mount API v1 & v2
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_v2_router, prefix="/api/v2")


@app.get("/")
def root():
    return {"message": "Welcome to UniHR SaaS API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/api/versions")
def api_versions():
    """Return supported API versions and their status."""
    return API_VERSIONS


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(content=render_metrics(), media_type=metrics_content_type())


@app.get("/internal/observability/summary", include_in_schema=False)
def observability_summary():
    return {
        "service": "backend-api",
        "api_metrics": snapshot("backend-api"),
        "sentry_enabled": bool(settings.SENTRY_DSN),
        "langfuse_enabled": bool(
            settings.LANGFUSE_ENABLED and settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY
        ),
    }
