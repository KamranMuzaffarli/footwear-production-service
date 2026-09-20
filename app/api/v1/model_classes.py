from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.repositories.shoe_model import get_shoe_model_class

from app.schemas.shoe_model import (
    ShoeModelClassRead,
    ShoeModelClassUpdate,
)

from app.services.model_class import (
    update_model_class as service_update_model_class,
)


router = APIRouter(
    prefix="/model-classes",
    tags=["Model Class"],
)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get(
    "/{shoe_model_class_id}",
    response_model=ShoeModelClassRead,
)
async def read_shoe_model_class(
    shoe_model_class_id: int,
    session: DbSession,
):
    model_class = await get_shoe_model_class(
        session,
        shoe_model_class_id,
    )

    if model_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model Class not found",
        )

    return model_class


@router.patch(
    "/{shoe_model_class_id}",
    response_model=ShoeModelClassRead,
)
async def update_model_class(
    shoe_model_class_id: int,
    data: ShoeModelClassUpdate,
    session: DbSession,
):
    return await service_update_model_class(
        session,
        shoe_model_class_id,
        data,
    )
