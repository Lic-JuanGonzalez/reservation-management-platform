from __future__ import annotations

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.report_tasks.generate_daily_report", bind=True, max_retries=3)  # type: ignore[misc]
def generate_daily_report(self, tenant_id: str, date: str) -> dict:  # type: ignore[type-arg]
    logger.info("generate_daily_report_started", tenant_id=tenant_id, date=date)
    return {"status": "completed", "tenant_id": tenant_id, "date": date}


@celery_app.task(name="app.workers.report_tasks.generate_monthly_summary", bind=True, max_retries=3)  # type: ignore[misc]
def generate_monthly_summary(self, tenant_id: str, year: int, month: int) -> dict:  # type: ignore[type-arg]
    logger.info("generate_monthly_summary_started", tenant_id=tenant_id, year=year, month=month)
    return {"status": "completed", "tenant_id": tenant_id, "year": year, "month": month}
