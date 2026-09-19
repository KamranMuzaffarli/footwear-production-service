from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.repositories.material import get_material, list_materials
from app.schemas.material import MaterialDetailRead, MaterialRead


router = APIRouter(prefix="/materials", tags=["Material"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=list[MaterialRead])
async def read_materials(
    session: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
):
    return await list_materials(
        session,
        limit=limit,
        offset=offset,
        category=category,
        is_active=is_active,
        search=search,
    )


@router.get("/{material_id}", response_model=MaterialDetailRead)
async def read_material(
    material_id: int,
    session: DbSession,
):
    material = await get_material(session, material_id)

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    return material
