from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.repositories.reference import (
    list_construction_methods,
    list_material_categories,
    list_material_usage_roles,
)
from app.schemas.reference import (
    ConstructionMethodRead,
    MaterialCategoryRead,
    MaterialUsageRoleRead,
)


router = APIRouter(tags=["Reference Data"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get(
    "/construction-methods",
    response_model=list[ConstructionMethodRead],
)
async def read_construction_methods(
    session: DbSession,
):
    return await list_construction_methods(session)


@router.get(
    "/material-categories",
    response_model=list[MaterialCategoryRead],
)
async def read_material_categories(
    session: DbSession,
):
    return await list_material_categories(session)


@router.get(
    "/material-usage-roles",
    response_model=list[MaterialUsageRoleRead],
)
async def read_material_usage_roles(
    session: DbSession,
):
    return await list_material_usage_roles(session)
