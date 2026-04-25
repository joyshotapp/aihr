from __future__ import annotations

import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.config import settings

logger = logging.getLogger(__name__)
_initialized_services: set[str] = set()


def init_sentry(service_name: str) -> None:
    if service_name in _initialized_services:
        return
    if not settings.SENTRY_DSN:
        logger.info("SENTRY_DSN 未設定，跳過 %s Sentry 初始化", service_name)
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT or settings.APP_ENV,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
        enable_tracing=True,
        integrations=[
            FastApiIntegration(),
            CeleryIntegration(),
        ],
    )
    sentry_sdk.set_tag("service", service_name)
    _initialized_services.add(service_name)
    logger.info("Sentry 已啟用 (%s)", service_name)
