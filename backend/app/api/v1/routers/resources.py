from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.dtos.resource_dtos import (
    CreateResourceRequest,
    ResourceListResponse,
    ResourceResponse,
    UpdateResourceRequest,
)
from app.core.dependencies import CurrentTenantId, CurrentUser, DBSession, require_roles
from app.domain.entities.resource import Resource, ResourceStatus, ResourceType, WorkingHours
from app.domain.entities.user import UserRole
from app.infrastructure.database.repositories.resource_repository import ResourceRepositoryImpl

router = APIRouter(prefix="/resources", tags=["Resources"])


def get_resource_repo(session: DBSession) -> ResourceRepositoryImpl:
    return ResourceRepositoryImpl(session)


@router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new resource",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN))],
)
async def create_resource(
    data: CreateResourceRequest,
    tenant_id: CurrentTenantId,
    current_user: CurrentUser,
    repo: Annotated[ResourceRepositoryImpl, Depends(get_resource_repo)],
) -> ResourceResponse:
    wh_data = data.working_hours
    working_hours = WorkingHours(
        monday=[{"start": s.start, "end": s.end} for s in wh_data.monday],
        tuesday=[{"start": s.start, "end": s.end} for s in wh_data.tuesday],
        wednesday=[{"start": s.start, "end": s.end} for s in wh_data.wednesday],
        thursday=[{"start": s.start, "end": s.end} for s in wh_data.thursday],
        friday=[{"start": s.start, "end": s.end} for s in wh_data.friday],
        saturday=[{"start": s.start, "end": s.end} for s in wh_data.saturday],
        sunday=[{"start": s.start, "end": s.end} for s in wh_data.sunday],
    )
    resource = Resource(
        tenant_id=tenant_id,
        name=data.name,
        resource_type=data.resource_type,
        description=data.description,
        capacity=data.capacity,
        working_hours=working_hours,
        amenities=data.amenities,
        slot_duration_minutes=data.slot_duration_minutes,
        buffer_minutes=data.buffer_minutes,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    saved = await repo.save(resource)
    return ResourceResponse.model_validate(saved)


@router.get(
    "",
    response_model=ResourceListResponse,
    summary="List resources for current tenant",
)
async def list_resources(
    tenant_id: CurrentTenantId,
    current_user: CurrentUser,
    repo: Annotated[ResourceRepositoryImpl, Depends(get_resource_repo)],
    resource_type: ResourceType | None = None,
    resource_status: ResourceStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> ResourceListResponse:
    filters: dict[str, object] = {"tenant_id": tenant_id}
    if resource_type:
        filters["resource_type"] = resource_type
    if resource_status:
        filters["status"] = resource_status

    items, total = await repo.list(offset=offset, limit=limit, **filters)
    return ResourceListResponse(
        items=[ResourceResponse.model_validate(r) for r in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{resource_id}",
    response_model=ResourceResponse,
    summary="Get resource by ID",
)
async def get_resource(
    resource_id: uuid.UUID,
    tenant_id: CurrentTenantId,
    current_user: CurrentUser,
    repo: Annotated[ResourceRepositoryImpl, Depends(get_resource_repo)],
) -> ResourceResponse:
    resource = await repo.get_by_id(resource_id)
    if not resource or resource.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return ResourceResponse.model_validate(resource)


@router.patch(
    "/{resource_id}",
    response_model=ResourceResponse,
    summary="Update resource",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN))],
)
async def update_resource(
    resource_id: uuid.UUID,
    data: UpdateResourceRequest,
    tenant_id: CurrentTenantId,
    current_user: CurrentUser,
    repo: Annotated[ResourceRepositoryImpl, Depends(get_resource_repo)],
) -> ResourceResponse:
    resource = await repo.get_by_id(resource_id)
    if not resource or resource.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    resource.update(
        name=data.name,
        description=data.description,
        capacity=data.capacity,
        amenities=data.amenities,
        slot_duration_minutes=data.slot_duration_minutes,
        buffer_minutes=data.buffer_minutes,
        updated_by=current_user.id,
    )
    if data.status:
        resource.status = data.status
        resource.touch(current_user.id)

    if data.working_hours:
        wh = data.working_hours
        resource.working_hours = WorkingHours(
            monday=[{"start": s.start, "end": s.end} for s in wh.monday],
            tuesday=[{"start": s.start, "end": s.end} for s in wh.tuesday],
            wednesday=[{"start": s.start, "end": s.end} for s in wh.wednesday],
            thursday=[{"start": s.start, "end": s.end} for s in wh.thursday],
            friday=[{"start": s.start, "end": s.end} for s in wh.friday],
            saturday=[{"start": s.start, "end": s.end} for s in wh.saturday],
            sunday=[{"start": s.start, "end": s.end} for s in wh.sunday],
        )

    saved = await repo.save(resource)
    return ResourceResponse.model_validate(saved)


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete resource (soft delete)",
    dependencies=[Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN))],
)
async def delete_resource(
    resource_id: uuid.UUID,
    tenant_id: CurrentTenantId,
    current_user: CurrentUser,
    repo: Annotated[ResourceRepositoryImpl, Depends(get_resource_repo)],
) -> None:
    resource = await repo.get_by_id(resource_id)
    if not resource or resource.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    resource.soft_delete(deleted_by=current_user.id)
    await repo.save(resource)
