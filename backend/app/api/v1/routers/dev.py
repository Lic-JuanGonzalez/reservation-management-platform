from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update

from app.core.config import settings
from app.core.dependencies import DBSession, RedisClient
from app.core.security import hash_password
from app.domain.entities.user import User, UserRole, UserStatus
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.repositories.user_repository import UserRepository

router = APIRouter(prefix="/dev", tags=["Dev"])


def require_dev_key(x_dev_key: str = Header(...)) -> None:
    if x_dev_key != settings.DEV_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid dev API key")

SUPER_ADMIN_EMAIL = "superadmin@test.com"
SUPER_ADMIN_PASSWORD = "SuperAdmin1234!"


class DevSetupResponse(BaseModel):
    message: str
    super_admin_email: str
    super_admin_password: str


class ActivateAllResponse(BaseModel):
    message: str
    activated_count: int


class VerificationTokenResponse(BaseModel):
    email: str
    token: str


@router.post(
    "/setup",
    response_model=DevSetupResponse,
    summary="[DEV ONLY] Create super admin user for testing",
    dependencies=[Depends(require_dev_key)],
)
async def dev_setup(session: DBSession, redis: RedisClient) -> DevSetupResponse:
    repo = UserRepository(session)
    existing = await repo.get_by_email(SUPER_ADMIN_EMAIL)
    if existing:
        existing.status = UserStatus.ACTIVE
        existing.email_verified = True
        existing.role = UserRole.SUPER_ADMIN
        await repo.save(existing)
        return DevSetupResponse(
            message="Super admin already existed — status reset to active",
            super_admin_email=SUPER_ADMIN_EMAIL,
            super_admin_password=SUPER_ADMIN_PASSWORD,
        )

    user = User(
        email=SUPER_ADMIN_EMAIL,
        hashed_password=hash_password(SUPER_ADMIN_PASSWORD),
        first_name="Super",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    await repo.save(user)
    return DevSetupResponse(
        message="Super admin created",
        super_admin_email=SUPER_ADMIN_EMAIL,
        super_admin_password=SUPER_ADMIN_PASSWORD,
    )


@router.post(
    "/activate-all",
    response_model=ActivateAllResponse,
    summary="[DEV ONLY] Activate all pending users (skip email verification for testing)",
    dependencies=[Depends(require_dev_key)],
)
async def activate_all_users(session: DBSession) -> ActivateAllResponse:
    result = await session.execute(
        update(UserModel)
        .where(UserModel.status == UserStatus.PENDING_VERIFICATION.value)
        .values(status=UserStatus.ACTIVE.value, email_verified=True)
        .returning(UserModel.id)
    )
    activated = result.fetchall()
    await session.commit()
    return ActivateAllResponse(
        message="All pending users activated",
        activated_count=len(activated),
    )


@router.get(
    "/verification-token",
    response_model=VerificationTokenResponse,
    summary="[DEV ONLY] Get email verification token for a user",
    dependencies=[Depends(require_dev_key)],
)
async def get_verification_token(email: str, session: DBSession, redis: RedisClient) -> VerificationTokenResponse:
    from fastapi import HTTPException
    repo = UserRepository(session)
    user = await repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id_str = str(user.id)
    keys = await redis.keys("email:verify:*")
    for key in keys:
        key_str = key.decode() if isinstance(key, bytes) else key
        stored = await redis.get(key_str)
        stored_str = stored.decode() if isinstance(stored, bytes) else stored
        if stored_str == user_id_str:
            token = key_str.split("email:verify:")[-1]
            return VerificationTokenResponse(email=email, token=token)
    raise HTTPException(status_code=404, detail="No verification token found — user may already be verified")


@router.get(
    "/reset-token",
    response_model=VerificationTokenResponse,
    summary="[DEV ONLY] Get password reset token for a user",
    dependencies=[Depends(require_dev_key)],
)
async def get_reset_token(email: str, session: DBSession, redis: RedisClient) -> VerificationTokenResponse:
    from fastapi import HTTPException
    repo = UserRepository(session)
    user = await repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id_str = str(user.id)
    keys = await redis.keys("password:reset:*")
    for key in keys:
        key_str = key.decode() if isinstance(key, bytes) else key
        stored = await redis.get(key_str)
        stored_str = stored.decode() if isinstance(stored, bytes) else stored
        if stored_str == user_id_str:
            token = key_str.split("password:reset:")[-1]
            return VerificationTokenResponse(email=email, token=token)
    raise HTTPException(status_code=404, detail="No reset token found — call forgot-password first")
