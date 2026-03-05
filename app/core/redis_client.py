"""
共用 Redis 連線工廠（T15 Redis SPOF 輕量化防護）

功能：
  - 集中管理連線參數（keepalive、timeout、health_check_interval）
  - 連線失敗時自動 reset，下次呼叫重新建立（circuit-breaker lite）
  - 失敗時回傳 None，呼叫端負責 graceful degradation
"""
import logging
import threading
from typing import Optional

import redis

from app.config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    取得共用 Redis 連線（thread-safe singleton）。
    若連線不可用，回傳 None（呼叫端應視為快取 miss 或放行）。
    """
    global _client
    with _lock:
        if _client is not None:
            try:
                _client.ping()
                return _client
            except Exception:
                logger.warning("Redis ping failed, resetting connection")
                _client = None

        # 重新建立連線
        try:
            url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
            client = redis.Redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=getattr(settings, "REDIS_SOCKET_CONNECT_TIMEOUT", 2),
                socket_timeout=getattr(settings, "REDIS_SOCKET_TIMEOUT", 2),
                socket_keepalive=getattr(settings, "REDIS_SOCKET_KEEPALIVE", True),
                health_check_interval=getattr(settings, "REDIS_HEALTH_CHECK_INTERVAL", 30),
                retry_on_timeout=True,
            )
            client.ping()
            _client = client
            logger.debug("Redis connection established")
            return _client
        except Exception as exc:
            logger.warning("Redis unavailable: %s", exc)
            _client = None
            return None


def reset_redis_client() -> None:
    """強制重置連線（測試用 / 手動觸發重連）"""
    global _client
    with _lock:
        _client = None
