from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentTenantId, CurrentUser, DBSession, require_roles
from app.domain.entities.reservation import ReservationStatus
from app.domain.entities.user import UserRole
from app.infrastructure.database.models.reservation_model import ReservationModel

router = APIRouter(prefix="/reports", tags=["Reports"])


class DailyReportItem(BaseModel):
    date: str
    total: int
    confirmed: int
    cancelled: int
    pending: int
    completed: int


class OccupancyItem(BaseModel):
    resource_id: uuid.UUID
    resource_name: str
    total_slots: int
    booked_slots: int
    occupancy_rate: float


class ReportSummary(BaseModel):
    period_start: str
    period_end: str
    total_reservations: int
    confirmed: int
    cancelled: int
    completed: int
    cancellation_rate: float


@router.get(
    "/daily",
    response_model=list[DailyReportItem],
    summary="Daily reservation counts",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN, UserRole.EMPLOYEE))],
)
async def daily_report(
    tenant_id: CurrentTenantId,
    current_user: CurrentUser,
    session: DBSession,
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> list[DailyReportItem]:
    if (end_date - start_date).days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 365 days",
        )

    result = await session.execute(
        select(
            func.date(ReservationModel.start_time).label("day"),
            func.count().label("total"),
            func.count(
                ReservationModel.id
            ).filter(ReservationModel.status == ReservationStatus.CONFIRMED.value).label("confirmed"),
            func.count(
                ReservationModel.id
            ).filter(ReservationModel.status == ReservationStatus.CANCELLED.value).label("cancelled"),
            func.count(
                ReservationModel.id
            ).filter(ReservationModel.status == ReservationStatus.PENDING.value).label("pending"),
            func.count(
                ReservationModel.id
            ).filter(ReservationModel.status == ReservationStatus.COMPLETED.value).label("completed"),
        ).where(
            ReservationModel.tenant_id == tenant_id,
            ReservationModel.start_time >= start_date,
            ReservationModel.start_time < end_date + timedelta(days=1),
            ReservationModel.deleted_at.is_(None),
        ).group_by(func.date(ReservationModel.start_time))
        .order_by(func.date(ReservationModel.start_time))
    )

    return [
        DailyReportItem(
            date=str(row.day),
            total=row.total,
            confirmed=row.confirmed,
            cancelled=row.cancelled,
            pending=row.pending,
            completed=row.completed,
        )
        for row in result.all()
    ]


@router.get(
    "/summary",
    response_model=ReportSummary,
    summary="Reservation summary for period",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN, UserRole.EMPLOYEE))],
)
async def summary_report(
    tenant_id: CurrentTenantId,
    current_user: CurrentUser,
    session: DBSession,
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> ReportSummary:
    result = await session.execute(
        select(
            func.count().label("total"),
            func.count(ReservationModel.id).filter(
                ReservationModel.status == ReservationStatus.CONFIRMED.value
            ).label("confirmed"),
            func.count(ReservationModel.id).filter(
                ReservationModel.status == ReservationStatus.CANCELLED.value
            ).label("cancelled"),
            func.count(ReservationModel.id).filter(
                ReservationModel.status == ReservationStatus.COMPLETED.value
            ).label("completed"),
        ).where(
            ReservationModel.tenant_id == tenant_id,
            ReservationModel.start_time >= start_date,
            ReservationModel.start_time < end_date + timedelta(days=1),
            ReservationModel.deleted_at.is_(None),
        )
    )
    row = result.one()
    total = row.total or 0
    cancelled = row.cancelled or 0
    return ReportSummary(
        period_start=str(start_date),
        period_end=str(end_date),
        total_reservations=total,
        confirmed=row.confirmed or 0,
        cancelled=cancelled,
        completed=row.completed or 0,
        cancellation_rate=round(cancelled / total * 100, 2) if total > 0 else 0.0,
    )
