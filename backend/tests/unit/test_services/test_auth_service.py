"""Unit tests for AuthService."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.dtos.auth_dtos import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
)
from app.application.services.auth_service import AuthService
from app.core.security import hash_password
from app.domain.entities.user import User, UserRole, UserStatus


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.setex = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=True)
    redis.keys = AsyncMock(return_value=[])
    redis.exists = AsyncMock(return_value=0)
    return redis


@pytest.fixture
def auth_service(mock_user_repo, mock_redis):
    return AuthService(mock_user_repo, mock_redis)


@pytest.fixture
def active_user():
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("ValidPass@123"),
        first_name="John",
        last_name="Doe",
        role=UserRole.CUSTOMER,
        tenant_id=uuid.uuid4(),
        status=UserStatus.ACTIVE,
        email_verified=True,
    )


class TestRegister:
    async def test_register_new_user_success(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.save.return_value = User(
            id=uuid.uuid4(),
            email="new@example.com",
            hashed_password=hash_password("ValidPass@123"),
            first_name="Jane",
            last_name="Smith",
            role=UserRole.CUSTOMER,
            status=UserStatus.PENDING_VERIFICATION,
        )

        with patch("app.application.services.auth_service.send_email_verification_task") as mock_task:
            mock_task.delay = MagicMock()
            result = await auth_service.register(
                RegisterRequest(
                    email="new@example.com",
                    password="ValidPass@123",
                    first_name="Jane",
                    last_name="Smith",
                )
            )

        assert result.email == "new@example.com"
        mock_task.delay.assert_called_once()

    async def test_register_duplicate_email_raises(self, auth_service, mock_user_repo, active_user):
        mock_user_repo.get_by_email.return_value = active_user

        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register(
                RegisterRequest(
                    email="test@example.com",
                    password="ValidPass@123",
                    first_name="John",
                    last_name="Doe",
                )
            )


class TestLogin:
    async def test_login_success(self, auth_service, mock_user_repo, active_user):
        mock_user_repo.get_by_email.return_value = active_user

        result = await auth_service.login(
            LoginRequest(email="test@example.com", password="ValidPass@123")
        )

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    async def test_login_wrong_password_raises(self, auth_service, mock_user_repo, active_user):
        mock_user_repo.get_by_email.return_value = active_user

        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login(
                LoginRequest(email="test@example.com", password="WrongPass@123")
            )

    async def test_login_nonexistent_user_raises(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login(
                LoginRequest(email="nobody@example.com", password="ValidPass@123")
            )

    async def test_login_suspended_user_raises(self, auth_service, mock_user_repo, active_user):
        active_user.status = UserStatus.SUSPENDED
        mock_user_repo.get_by_email.return_value = active_user

        with pytest.raises(PermissionError, match="suspended"):
            await auth_service.login(
                LoginRequest(email="test@example.com", password="ValidPass@123")
            )

    async def test_login_unverified_user_raises(self, auth_service, mock_user_repo, active_user):
        active_user.status = UserStatus.PENDING_VERIFICATION
        mock_user_repo.get_by_email.return_value = active_user

        with pytest.raises(PermissionError, match="Email not verified"):
            await auth_service.login(
                LoginRequest(email="test@example.com", password="ValidPass@123")
            )


class TestChangePassword:
    async def test_change_password_success(self, auth_service, mock_user_repo, active_user):
        mock_user_repo.get_by_id.return_value = active_user
        mock_user_repo.save.return_value = active_user

        await auth_service.change_password(
            active_user.id,
            ChangePasswordRequest(
                current_password="ValidPass@123",
                new_password="NewValid@456",
            ),
        )

        mock_user_repo.save.assert_called_once()

    async def test_change_password_wrong_current_raises(self, auth_service, mock_user_repo, active_user):
        mock_user_repo.get_by_id.return_value = active_user

        with pytest.raises(ValueError, match="Current password is incorrect"):
            await auth_service.change_password(
                active_user.id,
                ChangePasswordRequest(
                    current_password="WrongPass@123",
                    new_password="NewValid@456",
                ),
            )
