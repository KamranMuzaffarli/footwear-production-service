from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.production_composition import (
    ProductionCompositionCreate,
    ProductionCompositionRead,
    ProductionCompositionUpdate,
)
from app.services.production_composition import (
    create_production_composition,
    deactivate_production_composition,
    list_production_compositions,
    update_production_composition,
)

router = APIRouter(
    prefix="/model-classes",
    tags=["Production Composition"],
)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get(
    "/{shoe_model_class_id}/materials",
    response_model=list[ProductionCompositionRead],
)
async def read_production_compositions(
    shoe_model_class_id: int,
    session: DbSession,
):
    return await list_production_compositions(
        session,
        shoe_model_class_id,
    )


@router.post(
    "/{shoe_model_class_id}/materials",
    response_model=ProductionCompositionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_composition(
    shoe_model_class_id: int,
    data: ProductionCompositionCreate,
    session: DbSession,
):
    return await create_production_composition(
        session,
        shoe_model_class_id,
        data,
    )


@router.patch(
    "/{shoe_model_class_id}/materials/{composition_id}",
    response_model=ProductionCompositionRead,
)
async def update_composition(
    shoe_model_class_id: int,
    composition_id: int,
    data: ProductionCompositionUpdate,
    session: DbSession,
):
    return await update_production_composition(
        session,
        shoe_model_class_id,
        composition_id,
        data,
    )


@router.delete(
    "/{shoe_model_class_id}/materials/{composition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_composition(
    shoe_model_class_id: int,
    composition_id: int,
    session: DbSession,
) -> Response:
    await deactivate_production_composition(
        session,
        shoe_model_class_id,
        composition_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
