from celery import Celery
from app.config import settings

# 使用 settings 中的配置，確保從環境變數讀取
celery_app = Celery(
    "unihr",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.broker_connection_retry_on_startup = True

celery_app.conf.task_routes = {
    "app.tasks.*": {"queue": "celery"},
}

# Priority queue: 'bulk' queue for large files dispatched by batch-upload
celery_app.conf.task_queues = {
    "celery": {"exchange": "celery", "routing_key": "celery"},
    "bulk": {"exchange": "celery", "routing_key": "bulk"},
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=getattr(settings, "CELERY_TASK_ACKS_LATE", True),
    task_reject_on_worker_lost=getattr(settings, "CELERY_TASK_REJECT_ON_WORKER_LOST", True),
    worker_prefetch_multiplier=getattr(settings, "CELERY_WORKER_PREFETCH_MULTIPLIER", 1),
    worker_max_tasks_per_child=getattr(settings, "CELERY_WORKER_MAX_TASKS_PER_CHILD", 100),
    worker_max_memory_per_child=getattr(settings, "CELERY_WORKER_MAX_MEMORY_PER_CHILD_KB", 524288),
    task_soft_time_limit=getattr(settings, "CELERY_TASK_SOFT_TIME_LIMIT_SECONDS", 300),
    task_time_limit=getattr(settings, "CELERY_TASK_TIME_LIMIT_SECONDS", 360),
    task_track_started=True,
)

# Auto-discover tasks so that @celery_app.task decorators in app/tasks/ get registered
celery_app.autodiscover_tasks(['app.tasks'])

# Explicitly import tasks to ensure they are registered
import app.tasks.document_tasks  # noqa: F401, E402
