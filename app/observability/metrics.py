from __future__ import annotations

import re
import time
from collections import deque
from threading import Lock
from typing import Any

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUEST_COUNTER = Counter(
    "unihr_http_requests_total",
    "Total HTTP requests handled by UniHR",
    ["service", "method", "path", "status_family"],
)
REQUEST_LATENCY = Histogram(
    "unihr_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
)
IN_PROGRESS = Gauge(
    "unihr_http_requests_in_progress",
    "Current in-flight HTTP requests",
    ["service"],
)
UNHANDLED_EXCEPTIONS = Counter(
    "unihr_http_unhandled_exceptions_total",
    "Unhandled HTTP exceptions",
    ["service", "method", "path"],
)

_RECENT_REQUESTS_MAX = 5000
_recent_requests: deque[dict[str, Any]] = deque(maxlen=_RECENT_REQUESTS_MAX)
_recent_lock = Lock()
_uuid_pattern = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(?=/|$)"
)
_numeric_pattern = re.compile(r"/\d+(?=/|$)")


def normalize_path(path: str) -> str:
    normalized = _uuid_pattern.sub("/:id", path)
    normalized = _numeric_pattern.sub("/:id", normalized)
    return normalized or "/"


def observe_request(service: str, method: str, path: str, status_code: int, latency_ms: float) -> None:
    normalized_path = normalize_path(path)
    status_family = f"{status_code // 100}xx"
    REQUEST_COUNTER.labels(service, method, normalized_path, status_family).inc()
    REQUEST_LATENCY.labels(service, method, normalized_path).observe(max(latency_ms, 0) / 1000)

    with _recent_lock:
        _recent_requests.append(
            {
                "ts": time.time(),
                "service": service,
                "method": method,
                "path": normalized_path,
                "status_code": status_code,
                "latency_ms": latency_ms,
            }
        )


def record_unhandled_exception(service: str, method: str, path: str) -> None:
    UNHANDLED_EXCEPTIONS.labels(service, method, normalize_path(path)).inc()


def track_in_progress(service: str, delta: int) -> None:
    IN_PROGRESS.labels(service).inc(delta)


def render_metrics() -> bytes:
    return generate_latest()


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST


def snapshot(service: str, window_seconds: int = 3600) -> dict[str, Any]:
    cutoff = time.time() - window_seconds
    with _recent_lock:
        recent = [item for item in _recent_requests if item["service"] == service and item["ts"] >= cutoff]

    total = len(recent)
    server_errors = sum(1 for item in recent if item["status_code"] >= 500)
    client_errors = sum(1 for item in recent if 400 <= item["status_code"] < 500)
    latencies = sorted(float(item["latency_ms"]) for item in recent)

    avg_latency_ms = round(sum(latencies) / total, 2) if total else 0.0
    p95_latency_ms = _percentile(latencies, 0.95)

    return {
        "window_seconds": window_seconds,
        "requests": total,
        "server_errors": server_errors,
        "client_errors": client_errors,
        "error_rate_5xx": round(server_errors / total, 4) if total else 0.0,
        "error_rate_4xx": round(client_errors / total, 4) if total else 0.0,
        "avg_latency_ms": avg_latency_ms,
        "p95_latency_ms": p95_latency_ms,
    }


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    index = min(int((len(values) - 1) * percentile), len(values) - 1)
    return round(values[index], 2)
