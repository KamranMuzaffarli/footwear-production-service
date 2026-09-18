from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.repositories.shoe_model import (
    get_shoe_model,
    list_shoe_model_classes,
    list_shoe_models,
    shoe_model_exists,
)
from app.schemas.shoe_model import (
    ShoeModelClassRead,
    ShoeModelDetailRead,
    ShoeModelRead,
)


router = APIRouter(prefix="/models", tags=["Shoe Model"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=list[ShoeModelRead])
async def read_shoe_models(
    session: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    footwear_category: str | None = Query(default=None),
    footwear_type: str | None = Query(default=None),
    target_group: str | None = Query(default=None),
    shoe_last_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
):
    return await list_shoe_models(
        session,
        limit=limit,
        offset=offset,
        footwear_category=footwear_category,
        footwear_type=footwear_type,
        target_group=target_group,
        shoe_last_id=shoe_last_id,
        is_active=is_active,
    )


@router.get("/{shoe_model_id}", response_model=ShoeModelDetailRead)
async def read_shoe_model(
    shoe_model_id: int,
    session: DbSession,
):
    shoe_model = await get_shoe_model(session, shoe_model_id)

    if shoe_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shoe Model not found",
        )

    return shoe_model


@router.get(
    "/{shoe_model_id}/classes",
    response_model=list[ShoeModelClassRead],
)
async def read_shoe_model_classes(
    shoe_model_id: int,
    session: DbSession,
):
    if not await shoe_model_exists(session, shoe_model_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shoe Model not found",
        )

    return await list_shoe_model_classes(
        session,
        shoe_model_id,
    )
