"""Unit tests for ReservationService."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dtos.reservation_dtos import (
    CancelReservationRequest,
    CreateReservationRequest,
)
from app.application.services.reservation_service import ReservationService
from app.domain.entities.reservation import Reservation, ReservationStatus
from app.domain.entities.resource import Resource, ResourceStatus, ResourceType, WorkingHours
from app.domain.entities.tenant import Tenant, TenantSettings, TenantStatus, BusinessType
from app.domain.entities.user import UserRole
from app.domain.value_objects.time_slot import TimeSlot


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


@pytest.fixture
def resource_id():
    return uuid.uuid4()


@pytest.fixture
def customer_id():
    return uuid.uuid4()


@pytest.fixture
def mock_tenant(tenant_id):
    tenant = MagicMock(spec=Tenant)
    tenant.id = tenant_id
    tenant.is_active = True
    tenant.settings = TenantSettings(
        min_advance_booking_hours=1,
        max_advance_booking_days=90,
        max_reservations_per_customer=5,
        cancellation_hours_before=24,
    )
    return tenant


@pytest.fixture
def mock_resource(tenant_id, resource_id):
    resource = MagicMock(spec=Resource)
    resource.id = resource_id
    resource.tenant_id = tenant_id
    resource.is_available = True
    resource.slot_duration_minutes = 60
    resource.buffer_minutes = 0
    resource.working_hours = WorkingHours(
        monday=[{"start": "09:00", "end": "17:00"}],
        tuesday=[{"start": "09:00", "end": "17:00"}],
        wednesday=[{"start": "09:00", "end": "17:00"}],
        thursday=[{"start": "09:00", "end": "17:00"}],
        friday=[{"start": "09:00", "end": "17:00"}],
    )
    return resource


@pytest.fixture
def future_slot():
    start = datetime.now(UTC) + timedelta(hours=2)
    end = start + timedelta(hours=1)
    return start, end


@pytest.fixture
def mock_reservation_repo(tenant_id, resource_id, customer_id):
    repo = AsyncMock()
    repo.find_overlapping.return_value = []
    repo.get_customer_active_count.return_value = 0
    repo.generate_reference_number.return_value = "ABCDEF-00001234"

    reservation = MagicMock(spec=Reservation)
    reservation.id = uuid.uuid4()
    reservation.tenant_id = tenant_id
    reservation.resource_id = resource_id
    reservation.customer_id = customer_id
    reservation.reference_number = "ABCDEF-00001234"
    reservation.status = ReservationStatus.PENDING
    reservation.is_cancellable = True
    reservation.pop_events.return_value = []
    repo.save.return_value = reservation
    return repo


@pytest.fixture
def mock_resource_repo(mock_resource):
    repo = AsyncMock()
    repo.get_by_id.return_value = mock_resource
    return repo


@pytest.fixture
def mock_tenant_repo(mock_tenant):
    repo = AsyncMock()
    repo.get_by_id.return_value = mock_tenant
    return repo


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def reservation_service(
    mock_reservation_repo, mock_resource_repo, mock_tenant_repo, mock_redis
):
    return ReservationService(
        mock_reservation_repo, mock_resource_repo, mock_tenant_repo, mock_redis
    )


class TestCreateReservation:
    async def test_create_reservation_success(
        self, reservation_service, tenant_id, customer_id, resource_id, future_slot
    ):
        start, end = future_slot
        result = await reservation_service.create_reservation(
            tenant_id=tenant_id,
            customer_id=customer_id,
            data=CreateReservationRequest(
                resource_id=resource_id,
                start_time=start,
                end_time=end,
            ),
        )
        assert result.reference_number == "ABCDEF-00001234"

    async def test_create_reservation_overlap_rejected(
        self,
        reservation_service,
        mock_reservation_repo,
        tenant_id,
        customer_id,
        resource_id,
        future_slot,
    ):
        existing = MagicMock(spec=Reservation)
        mock_reservation_repo.find_overlapping.return_value = [existing]
        start, end = future_slot

        with pytest.raises(ValueError, match="not available"):
            await reservation_service.create_reservation(
                tenant_id=tenant_id,
                customer_id=customer_id,
                data=CreateReservationRequest(
                    resource_id=resource_id,
                    start_time=start,
                    end_time=end,
                ),
            )

    async def test_create_reservation_customer_limit_exceeded(
        self,
        reservation_service,
        mock_reservation_repo,
        tenant_id,
        customer_id,
        resource_id,
        future_slot,
    ):
        mock_reservation_repo.get_customer_active_count.return_value = 5
        start, end = future_slot

        with pytest.raises(ValueError, match="Maximum"):
            await reservation_service.create_reservation(
                tenant_id=tenant_id,
                customer_id=customer_id,
                data=CreateReservationRequest(
                    resource_id=resource_id,
                    start_time=start,
                    end_time=end,
                ),
            )

    async def test_create_reservation_in_past_rejected(
        self,
        reservation_service,
        tenant_id,
        customer_id,
        resource_id,
    ):
        past_start = datetime.now(UTC) - timedelta(hours=2)
        past_end = past_start + timedelta(hours=1)

        with pytest.raises(ValueError):
            await reservation_service.create_reservation(
                tenant_id=tenant_id,
                customer_id=customer_id,
                data=CreateReservationRequest(
                    resource_id=resource_id,
                    start_time=past_start,
                    end_time=past_end,
                ),
            )


class TestCancelReservation:
    async def test_cancel_own_reservation_success(
        self,
        reservation_service,
        mock_reservation_repo,
        tenant_id,
        customer_id,
        resource_id,
    ):
        reservation = MagicMock(spec=Reservation)
        reservation.id = uuid.uuid4()
        reservation.tenant_id = tenant_id
        reservation.customer_id = customer_id
        reservation.resource_id = resource_id
        reservation.is_cancellable = True
        reservation.status = ReservationStatus.PENDING
        reservation.time_slot = TimeSlot(
            datetime.now(UTC) + timedelta(hours=48),
            datetime.now(UTC) + timedelta(hours=49),
        )
        reservation.pop_events.return_value = []
        mock_reservation_repo.get_by_id.return_value = reservation
        mock_reservation_repo.save.return_value = reservation

        result = await reservation_service.cancel_reservation(
            tenant_id=tenant_id,
            reservation_id=reservation.id,
            canceller_id=customer_id,
            canceller_role=UserRole.CUSTOMER,
            data=CancelReservationRequest(reason="Changed plans"),
        )

        reservation.cancel.assert_called_once()

    async def test_cancel_other_customer_reservation_denied(
        self,
        reservation_service,
        mock_reservation_repo,
        tenant_id,
        resource_id,
    ):
        owner_id = uuid.uuid4()
        other_id = uuid.uuid4()
        reservation = MagicMock(spec=Reservation)
        reservation.tenant_id = tenant_id
        reservation.customer_id = owner_id
        reservation.is_cancellable = True
        mock_reservation_repo.get_by_id.return_value = reservation

        with pytest.raises(PermissionError, match="Cannot cancel"):
            await reservation_service.cancel_reservation(
                tenant_id=tenant_id,
                reservation_id=uuid.uuid4(),
                canceller_id=other_id,
                canceller_role=UserRole.CUSTOMER,
                data=CancelReservationRequest(),
            )
