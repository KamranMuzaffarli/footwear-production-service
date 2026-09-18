from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.shoe_last import ShoeLast


async def list_shoe_lasts(
    session: AsyncSession,
    *,
    last_type: str | None = None,
    gender_category: str | None = None,
    size_system: str | None = None,
) -> list[ShoeLast]:
    statement = select(ShoeLast)

    if last_type is not None:
        statement = statement.where(ShoeLast.last_type == last_type)

    if gender_category is not None:
        statement = statement.where(
            ShoeLast.gender_category == gender_category
        )

    if size_system is not None:
        statement = statement.where(
            ShoeLast.size_system == size_system
        )

    result = await session.execute(statement)

    return list(result.scalars().all())


async def get_shoe_last(
    session: AsyncSession,
    shoe_last_id: int,
) -> ShoeLast | None:
    statement = (
        select(ShoeLast)
        .where(ShoeLast.shoe_last_id == shoe_last_id)
        .options(selectinload(ShoeLast.sizes))
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()
