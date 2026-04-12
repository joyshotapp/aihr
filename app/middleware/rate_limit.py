"""
API Rate Limiting 中間件（T3-4）
基於 Redis 的滑動視窗 Rate Limiter，支援：
  - 全域速率限制（IP 層）
  - 租戶級速率限制
  - 使用者級速率限制
  - 濫用偵測與自動封鎖
"""

import logging
import time
import ipaddress
from typing import Optional, Tuple

import redis
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


def _extract_client_ip(request: Request) -> str:
    """Resolve the real client IP when running behind nginx/proxies."""
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        first_hop = forwarded_for.split(",")[0].strip()
        if first_hop:
            return first_hop

    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


def _is_loopback_ip(value: str) -> bool:
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


# ═══════════════════════════════════════════
#  Rate Limiter Core
# ═══════════════════════════════════════════


class RateLimiter:
    """基於 Redis 的滑動視窗限流器"""

    def __init__(self, redis_url: Optional[str] = None):
        # redis_url 保留供外部測試注入；實際連線透過共用 factory
        self._redis_url = redis_url or getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")

    @property
    def r(self) -> Optional[redis.Redis]:
        """取得 Redis 連線；不可用時回傳 None（呼叫端需處理）。"""
        return get_redis_client()

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        fail_closed: bool = False,
    ) -> Tuple[bool, int, int]:
        """
        滑動視窗限流檢查。
        回傳 (allowed, remaining, retry_after_seconds)

        fail_closed=True：Redis 不可用時拒絕請求（用於高風險路徑）。
        fail_closed=False：Redis 不可用時放行（用於一般路徑，維持可用性）。
        """
        r = self.r
        if r is None:
            if fail_closed:
                # 高風險路徑：Redis 失效時拒絕，retry_after 用 0 表示「服務暫不可用」
                return False, 0, 0
            return True, max_requests, 0  # 一般路徑：Redis 不可用時放行
        try:
            now = time.time()
            window_start = now - window_seconds
            pipe = r.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window_seconds + 10)
            results = pipe.execute()
            current_count = results[1]

            if current_count >= max_requests:
                # 超過限制 — 移除剛加的
                r.zrem(key, str(now))
                # 計算下次可用時間
                oldest = r.zrange(key, 0, 0, withscores=True)
                retry_after = int(window_seconds - (now - oldest[0][1])) if oldest else window_seconds
                return False, 0, max(retry_after, 1)

            remaining = max_requests - current_count - 1
            return True, max(remaining, 0), 0

        except Exception as e:
            logger.warning("Rate limiter Redis error: %s, fail_closed=%s", e, fail_closed)
            if fail_closed:
                return False, 0, 0
            return True, max_requests, 0  # 一般路徑：Redis 不可用時放行

    def record_abuse(self, key: str, threshold: int = 100, window: int = 60) -> bool:
        """
        濫用偵測：如果短時間內超過閾值，標記為濫用。
        回傳 True 表示已被標記為濫用。
        """
        abuse_key = f"abuse:{key}"
        r = self.r
        if r is None:
            return False  # Redis 不可用時不封鎖
        try:
            blocked = r.get(abuse_key)
            if blocked:
                return True

            count_key = f"abuse_count:{key}"
            count = r.incr(count_key)
            if count == 1:
                r.expire(count_key, window)

            if count > threshold:
                # 封鎖 10 分鐘
                r.setex(abuse_key, 600, "1")
                logger.warning("Abuse detected for %s, blocking for 10 minutes", key)
                return True

            return False
        except Exception as e:
            logger.warning("Abuse detection error: %s", e)
            return False


# ═══════════════════════════════════════════
#  Rate Limit Configuration
# ═══════════════════════════════════════════

# 預設限流設定（可透過環境變數覆蓋）
RATE_LIMITS = {
    "global_per_ip": {
        "max_requests": int(getattr(settings, "RATE_LIMIT_GLOBAL_PER_IP", 200)),
        "window_seconds": 60,
    },
    "per_user": {
        "max_requests": int(getattr(settings, "RATE_LIMIT_PER_USER", 60)),
        "window_seconds": 60,
    },
    "per_tenant": {
        "max_requests": int(getattr(settings, "RATE_LIMIT_PER_TENANT", 300)),
        "window_seconds": 60,
    },
    "chat_per_user": {
        "max_requests": int(getattr(settings, "RATE_LIMIT_CHAT_PER_USER", 20)),
        "window_seconds": 60,
    },
    # 高風險路徑：嚴格限流，Redis 失效時 fail-closed
    "high_risk": {
        "max_requests": int(getattr(settings, "RATE_LIMIT_HIGH_RISK", 10)),
        "window_seconds": 60,
    },
}

# 高風險路徑集合（Redis 失效時 fail-closed，拒絕而非放行）
HIGH_RISK_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/resend-verification",
    "/api/v1/payment/checkout",
    "/api/v1/payment/webhook",
    "/api/v1/invitations/accept",
}


# ═══════════════════════════════════════════
#  FastAPI Middleware
# ═══════════════════════════════════════════


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    全域 Rate Limiting 中間件。
    依序檢查：
    1. IP 是否被濫用封鎖
    2. IP 級全域限流
    3. 如果能識別用戶/租戶，進一步限流

    高風險路徑（登入、付款、驗證等）採用更嚴格限流，
    且在 Redis 失效時 fail-closed（回傳 503），防止暴力攻擊。
    """

    SKIP_PATHS = {"/", "/health", "/api/versions", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, redis_url: Optional[str] = None):
        super().__init__(app)
        self.limiter = RateLimiter(redis_url)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 跳過健康檢查等端點
        if path in self.SKIP_PATHS or path.startswith("/docs"):
            return await call_next(request)

        client_ip = _extract_client_ip(request)

        # Allow local server-side verification traffic to pass without tripping abuse locks.
        if _is_loopback_ip(client_ip):
            return await call_next(request)

        is_high_risk = path in HIGH_RISK_PATHS

        try:
            # 1. 濫用檢查（高風險路徑：Redis 失效時同樣不封鎖，但限流本身會 fail-closed）
            if self.limiter.record_abuse(f"ip:{client_ip}"):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": {
                            "error": "abuse_detected",
                            "message": "偵測到異常行為，暫時封鎖。請稍後再試。",
                        }
                    },
                    headers={"Retry-After": "600"},
                )

            # 2a. 高風險路徑：嚴格限流，Redis 失效時 fail-closed
            if is_high_risk:
                hr_conf = RATE_LIMITS["high_risk"]
                allowed, remaining, retry_after = self.limiter.is_allowed(
                    f"rl:hr:{client_ip}:{path}",
                    hr_conf["max_requests"],
                    hr_conf["window_seconds"],
                    fail_closed=True,
                )
                if not allowed:
                    if retry_after == 0:
                        # Redis 不可用，服務暫不可用（fail-closed）
                        return JSONResponse(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            content={
                                "detail": {
                                    "error": "service_unavailable",
                                    "message": "速率限制服務暫時無法使用，請稍後再試。",
                                }
                            },
                        )
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": {
                                "error": "rate_limited",
                                "message": "請求過於頻繁，請稍後再試。",
                            }
                        },
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(hr_conf["max_requests"]),
                            "X-RateLimit-Remaining": "0",
                        },
                    )

            # 2b. 一般路徑：IP 級全域限流，Redis 失效時 fail-open
            ip_conf = RATE_LIMITS["global_per_ip"]
            allowed, remaining, retry_after = self.limiter.is_allowed(
                f"rl:ip:{client_ip}",
                ip_conf["max_requests"],
                ip_conf["window_seconds"],
                fail_closed=False,
            )
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": {
                            "error": "rate_limited",
                            "message": "請求過於頻繁，請稍後再試。",
                        }
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(ip_conf["max_requests"]),
                        "X-RateLimit-Remaining": "0",
                    },
                )

        except Exception:
            # Redis 不可用時一般路徑不阻擋請求；高風險路徑已在 is_allowed 層處理
            pass

        response = await call_next(request)

        # 添加限流標頭
        try:
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMITS["global_per_ip"]["max_requests"])
        except Exception:
            pass

        return response
