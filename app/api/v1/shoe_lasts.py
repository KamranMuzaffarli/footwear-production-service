from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.repositories.shoe_last import get_shoe_last, list_shoe_lasts
from app.schemas.shoe_last import ShoeLastDetailRead, ShoeLastRead

router = APIRouter(prefix="/shoe-lasts", tags=["Shoe Last"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=list[ShoeLastRead])
async def read_shoe_lasts(
    session: DbSession,
    last_type: str | None = Query(default=None),
    gender_category: str | None = Query(default=None),
    size_system: str | None = Query(default=None),
):
    return await list_shoe_lasts(
        session,
        last_type=last_type,
        gender_category=gender_category,
        size_system=size_system,
    )


@router.get("/{shoe_last_id}", response_model=ShoeLastDetailRead)
async def read_shoe_last(
    shoe_last_id: int,
    session: DbSession,
):
    shoe_last = await get_shoe_last(session, shoe_last_id)

    if shoe_last is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shoe Last not found",
        )

    return shoe_last
