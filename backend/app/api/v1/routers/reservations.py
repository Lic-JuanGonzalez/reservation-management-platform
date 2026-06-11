from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.dtos.reservation_dtos import (
    AvailabilityRequest,
    AvailableSlotResponse,
    CancelReservationRequest,
    CreateReservationRequest,
    ReservationListResponse,
    ReservationResponse,
)
from app.application.services.reservation_service import ReservationService
from app.core.dependencies import CurrentTenantId, CurrentUser, DBSession, RedisClient
from app.domain.entities.reservation import ReservationStatus
from app.domain.entities.user import UserRole
from app.infrastructure.database.repositories.reservation_repository import (
    ReservationRepositoryImpl,
)
from app.infrastructure.database.repositories.resource_repository import ResourceRepositoryImpl
from app.infrastructure.database.repositories.tenant_repository import TenantRepositoryImpl

router = APIRouter(prefix="/reservations", tags=["Reservations"])


def get_reservation_service(session: DBSession, redis: RedisClient) -> ReservationService:
    return ReservationService(
        ReservationRepositoryImpl(session),
        ResourceRepositoryImpl(session),
        TenantRepositoryImpl(session),
        redis,
    )


@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new reservation",
)
async def create_reservation(
    data: CreateReservationRequest,
    current_user: CurrentUser,
    tenant_id: CurrentTenantId,
    service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> ReservationResponse:
    try:
        return await service.create_reservation(tenant_id, current_user.id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get(
    "",
    response_model=ReservationListResponse,
    summary="List reservations",
)
async def list_reservations(
    current_user: CurrentUser,
    tenant_id: CurrentTenantId,
    service: Annotated[ReservationService, Depends(get_reservation_service)],
    status_filter: ReservationStatus | None = Query(default=None, alias="status"),
    resource_id: uuid.UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> ReservationListResponse:
    return await service.list_reservations(
        tenant_id=tenant_id,
        requester_id=current_user.id,
        requester_role=current_user.role,
        status=status_filter,
        resource_id=resource_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/availability",
    response_model=list[AvailableSlotResponse],
    summary="Get available slots for a resource on a date",
)
async def get_availability(
    resource_id: uuid.UUID,
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    tenant_id: CurrentTenantId = None,  # type: ignore[assignment]
    current_user: CurrentUser = None,  # type: ignore[assignment]
    service: Annotated[ReservationService, Depends(get_reservation_service)] = None,  # type: ignore[assignment]
) -> list[AvailableSlotResponse]:
    try:
        return await service.get_available_slots(tenant_id, resource_id, date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Get reservation by ID",
)
async def get_reservation(
    reservation_id: uuid.UUID,
    current_user: CurrentUser,
    tenant_id: CurrentTenantId,
    service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> ReservationResponse:
    try:
        return await service.get_reservation(
            tenant_id, reservation_id, current_user.id, current_user.role
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post(
    "/{reservation_id}/confirm",
    response_model=ReservationResponse,
    summary="Confirm a reservation (admin/employee only)",
)
async def confirm_reservation(
    reservation_id: uuid.UUID,
    current_user: CurrentUser,
    tenant_id: CurrentTenantId,
    service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> ReservationResponse:
    if current_user.role not in (UserRole.TENANT_ADMIN, UserRole.EMPLOYEE, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    try:
        return await service.confirm_reservation(tenant_id, reservation_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post(
    "/{reservation_id}/cancel",
    response_model=ReservationResponse,
    summary="Cancel a reservation",
)
async def cancel_reservation(
    reservation_id: uuid.UUID,
    data: CancelReservationRequest,
    current_user: CurrentUser,
    tenant_id: CurrentTenantId,
    service: Annotated[ReservationService, Depends(get_reservation_service)],
) -> ReservationResponse:
    try:
        return await service.cancel_reservation(
            tenant_id, reservation_id, current_user.id, current_user.role, data
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
