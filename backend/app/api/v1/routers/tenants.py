from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.dtos.auth_dtos import UserResponse
from app.application.dtos.tenant_dtos import (
    CreateTenantRequest,
    TenantListResponse,
    TenantResponse,
    UpdateTenantRequest,
    UpdateTenantSettingsRequest,
)
from app.application.services.auth_service import AuthService
from app.core.dependencies import CurrentUser, DBSession, RedisClient, require_roles
from app.domain.entities.tenant import BusinessType, Tenant, TenantSettings
from app.domain.entities.user import UserRole
from app.infrastructure.database.repositories.tenant_repository import TenantRepositoryImpl
from app.infrastructure.database.repositories.user_repository import UserRepository

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def get_tenant_repo(session: DBSession) -> TenantRepositoryImpl:
    return TenantRepositoryImpl(session)


@router.post(
    "",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant (super admin only)",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def create_tenant(
    data: CreateTenantRequest,
    current_user: CurrentUser,
    repo: Annotated[TenantRepositoryImpl, Depends(get_tenant_repo)],
    session: DBSession,
    redis: RedisClient,
) -> TenantResponse:
    existing = await repo.get_by_slug(data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with slug '{data.slug}' already exists",
        )

    tenant = Tenant(
        name=data.name,
        slug=data.slug,
        business_type=BusinessType(data.business_type),
        owner_email=data.owner_email,
        phone=data.phone,
        website=data.website,
        address=data.address,
        created_by=current_user.id,
    )
    tenant = await repo.save(tenant)

    from app.application.dtos.auth_dtos import RegisterRequest
    auth_service = AuthService(UserRepository(session), redis)
    from app.core.security import validate_password_strength
    errors = validate_password_strength(data.owner_password)
    if errors:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="; ".join(errors))

    await auth_service.register(
        RegisterRequest(
            email=data.owner_email,
            password=data.owner_password,
            first_name=data.owner_first_name,
            last_name=data.owner_last_name,
        ),
        tenant_id=tenant.id,
        role=UserRole.TENANT_ADMIN,
    )

    return TenantResponse.model_validate(tenant)


@router.get(
    "",
    response_model=TenantListResponse,
    summary="List all tenants (super admin only)",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN))],
)
async def list_tenants(
    current_user: CurrentUser,
    repo: Annotated[TenantRepositoryImpl, Depends(get_tenant_repo)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> TenantListResponse:
    items, total = await repo.list(offset=offset, limit=limit)
    return TenantListResponse(
        items=[TenantResponse.model_validate(t) for t in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant by ID",
)
async def get_tenant(
    tenant_id: uuid.UUID,
    current_user: CurrentUser,
    repo: Annotated[TenantRepositoryImpl, Depends(get_tenant_repo)],
) -> TenantResponse:
    if current_user.role != UserRole.SUPER_ADMIN and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    tenant = await repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return TenantResponse.model_validate(tenant)


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant",
)
async def update_tenant(
    tenant_id: uuid.UUID,
    data: UpdateTenantRequest,
    current_user: CurrentUser,
    repo: Annotated[TenantRepositoryImpl, Depends(get_tenant_repo)],
) -> TenantResponse:
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    if current_user.role == UserRole.TENANT_ADMIN and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    tenant = await repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if data.name:
        tenant.name = data.name
    if data.logo_url is not None:
        tenant.logo_url = data.logo_url
    if data.website is not None:
        tenant.website = data.website
    if data.phone is not None:
        tenant.phone = data.phone
    if data.address is not None:
        tenant.address = data.address
    tenant.touch(current_user.id)

    saved = await repo.save(tenant)
    return TenantResponse.model_validate(saved)


@router.patch(
    "/{tenant_id}/settings",
    response_model=TenantResponse,
    summary="Update tenant settings",
)
async def update_tenant_settings(
    tenant_id: uuid.UUID,
    data: UpdateTenantSettingsRequest,
    current_user: CurrentUser,
    repo: Annotated[TenantRepositoryImpl, Depends(get_tenant_repo)],
) -> TenantResponse:
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    if current_user.role == UserRole.TENANT_ADMIN and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    tenant = await repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    tenant.update_settings(**data.model_dump(exclude_none=True))
    saved = await repo.save(tenant)
    return TenantResponse.model_validate(saved)
