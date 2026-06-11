from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.dtos.auth_dtos import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.application.services.auth_service import AuthService
from app.core.dependencies import CurrentUser, DBSession, RedisClient
from app.infrastructure.database.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)


def get_auth_service(session: DBSession, redis: RedisClient) -> AuthService:
    return AuthService(UserRepository(session), redis)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
)
async def register(
    data: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    try:
        return await service.register(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain JWT tokens",
)
async def login(
    data: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        return await service.login(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token using refresh token",
)
async def refresh_tokens(
    data: RefreshTokenRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        return await service.refresh_tokens(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate current tokens",
)
async def logout(
    current_user: CurrentUser,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    await service.logout(token, str(current_user.id))


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify email address with token",
)
async def verify_email(
    data: VerifyEmailRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    try:
        await service.verify_email(data.token)
        return {"message": "Email verified successfully"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset email",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    await service.forgot_password(data.email)
    return {"message": "If the email exists, a reset link has been sent"}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password using reset token",
)
async def reset_password(
    data: ResetPasswordRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    try:
        await service.reset_password(data)
        return {"message": "Password reset successfully"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password (authenticated)",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    try:
        await service.change_password(current_user.id, data)
        return {"message": "Password changed successfully"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
