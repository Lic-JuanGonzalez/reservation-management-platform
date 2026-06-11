from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

from app.application.dtos.auth_dtos import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis_client import RedisKeys
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_token,
    hash_password,
    verify_password,
)
from app.domain.entities.user import User, UserRole, UserStatus
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.workers.notification_tasks import (
    send_email_verification_task,
    send_password_reset_task,
    send_welcome_email_task,
)

logger = get_logger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository, redis: Redis) -> None:
        self._user_repo = user_repo
        self._redis = redis

    async def register(
        self,
        data: RegisterRequest,
        tenant_id: uuid.UUID | None = None,
        role: UserRole = UserRole.CUSTOMER,
    ) -> UserResponse:
        existing = await self._user_repo.get_by_email(
            data.email, tenant_id=tenant_id
        )
        if existing:
            raise ValueError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role=role,
            tenant_id=tenant_id,
            phone=data.phone,
            status=UserStatus.PENDING_VERIFICATION,
        )
        user = await self._user_repo.save(user)

        verification_token = generate_token()
        await self._redis.setex(
            RedisKeys.email_verification(verification_token),
            3600,  # 1 hour
            str(user.id),
        )

        send_email_verification_task.delay(
            user_id=str(user.id),
            email=user.email,
            name=user.full_name,
            token=verification_token,
        )

        logger.info("user_registered", user_id=str(user.id), email=user.email)
        return UserResponse.model_validate(user)

    async def login(self, data: LoginRequest, tenant_id: uuid.UUID | None = None) -> TokenResponse:
        user = await self._user_repo.get_by_email(data.email, tenant_id=tenant_id)
        if not user or not verify_password(data.password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if user.status == UserStatus.SUSPENDED:
            raise PermissionError("Account is suspended")

        if user.status == UserStatus.PENDING_VERIFICATION:
            raise PermissionError("Email not verified. Please check your inbox.")

        access_token, access_jti = create_access_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else "",
            role=user.role.value,
        )
        refresh_token, refresh_jti = create_refresh_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else "",
        )

        await self._redis.setex(
            RedisKeys.refresh_token(str(user.id), refresh_jti),
            settings.refresh_token_expire_seconds,
            str(user.id),
        )

        logger.info("user_logged_in", user_id=str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_seconds,
        )

    async def refresh_tokens(self, data: RefreshTokenRequest) -> TokenResponse:
        try:
            payload = decode_refresh_token(data.refresh_token)
        except ValueError as exc:
            raise ValueError("Invalid refresh token") from exc

        user_id = payload["sub"]
        jti = payload["jti"]
        tenant_id = payload.get("tenant_id", "")

        stored = await self._redis.get(RedisKeys.refresh_token(user_id, jti))
        if not stored:
            raise ValueError("Refresh token expired or revoked")

        # Rotate — invalidate old, issue new
        await self._redis.delete(RedisKeys.refresh_token(user_id, jti))

        user = await self._user_repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        access_token, _ = create_access_token(
            subject=user_id,
            tenant_id=str(user.tenant_id) if user.tenant_id else tenant_id,
            role=user.role.value,
        )
        new_refresh_token, new_refresh_jti = create_refresh_token(
            subject=user_id,
            tenant_id=str(user.tenant_id) if user.tenant_id else tenant_id,
        )

        await self._redis.setex(
            RedisKeys.refresh_token(user_id, new_refresh_jti),
            settings.refresh_token_expire_seconds,
            user_id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_seconds,
        )

    async def logout(self, access_token: str, user_id: str) -> None:
        try:
            payload = decode_access_token(access_token)
            jti = payload["jti"]
            exp = payload["exp"]
            ttl = max(0, int(exp - datetime.now(UTC).timestamp()))
            await self._redis.setex(
                RedisKeys.access_token_blacklist(jti), ttl, "1"
            )
        except ValueError:
            pass  # Already invalid token

        # Revoke all refresh tokens for this user (logout all devices)
        pattern = RedisKeys.refresh_token(user_id, "*")
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)

        logger.info("user_logged_out", user_id=user_id)

    async def verify_email(self, token: str) -> None:
        user_id = await self._redis.get(RedisKeys.email_verification(token))
        if not user_id:
            raise ValueError("Invalid or expired verification token")

        user = await self._user_repo.get_by_id(uuid.UUID(user_id))
        if not user:
            raise ValueError("User not found")

        user.verify_email()
        await self._user_repo.save(user)
        await self._redis.delete(RedisKeys.email_verification(token))

        send_welcome_email_task.delay(
            user_id=str(user.id),
            email=user.email,
            name=user.full_name,
        )

        logger.info("email_verified", user_id=user_id)

    async def forgot_password(self, email: str, tenant_id: uuid.UUID | None = None) -> None:
        user = await self._user_repo.get_by_email(email, tenant_id=tenant_id)
        if not user:
            return  # Silently succeed to prevent email enumeration

        reset_token = generate_token()
        await self._redis.setex(
            RedisKeys.password_reset(reset_token),
            3600,
            str(user.id),
        )

        send_password_reset_task.delay(
            user_id=str(user.id),
            email=user.email,
            name=user.full_name,
            token=reset_token,
        )

    async def reset_password(self, data: ResetPasswordRequest) -> None:
        user_id = await self._redis.get(RedisKeys.password_reset(data.token))
        if not user_id:
            raise ValueError("Invalid or expired reset token")

        user = await self._user_repo.get_by_id(uuid.UUID(user_id))
        if not user:
            raise ValueError("User not found")

        user.update_password(hash_password(data.new_password))
        await self._user_repo.save(user)
        await self._redis.delete(RedisKeys.password_reset(data.token))

        # Invalidate all sessions
        pattern = RedisKeys.refresh_token(str(user.id), "*")
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)

        logger.info("password_reset", user_id=user_id)

    async def change_password(
        self,
        user_id: uuid.UUID,
        data: ChangePasswordRequest,
    ) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not verify_password(data.current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        user.update_password(hash_password(data.new_password))
        await self._user_repo.save(user)

        # Invalidate all refresh tokens (force re-login on other devices)
        pattern = RedisKeys.refresh_token(str(user_id), "*")
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)

        logger.info("password_changed", user_id=str(user_id))
