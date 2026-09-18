from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.shoe_model import ShoeModel, ShoeModelClass


async def list_shoe_models(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    footwear_category: str | None = None,
    footwear_type: str | None = None,
    target_group: str | None = None,
    shoe_last_id: int | None = None,
    is_active: bool | None = None,
) -> list[ShoeModel]:
    statement = select(ShoeModel)

    if footwear_category is not None:
        statement = statement.where(
            ShoeModel.footwear_category == footwear_category
        )

    if footwear_type is not None:
        statement = statement.where(
            ShoeModel.footwear_type == footwear_type
        )

    if target_group is not None:
        statement = statement.where(
            ShoeModel.target_group == target_group
        )

    if shoe_last_id is not None:
        statement = statement.where(
            ShoeModel.shoe_last_id == shoe_last_id
        )

    if is_active is not None:
        statement = statement.where(
            ShoeModel.is_active == is_active
        )

    statement = (
        statement
        .order_by(ShoeModel.shoe_model_id)
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


async def get_shoe_model(
    session: AsyncSession,
    shoe_model_id: int,
) -> ShoeModel | None:
    statement = (
        select(ShoeModel)
        .where(ShoeModel.shoe_model_id == shoe_model_id)
        .options(selectinload(ShoeModel.shoe_last))
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def shoe_model_exists(
    session: AsyncSession,
    shoe_model_id: int,
) -> bool:
    statement = select(ShoeModel.shoe_model_id).where(
        ShoeModel.shoe_model_id == shoe_model_id
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none() is not None


async def list_shoe_model_classes(
    session: AsyncSession,
    shoe_model_id: int,
) -> list[ShoeModelClass]:
    statement = (
        select(ShoeModelClass)
        .where(ShoeModelClass.shoe_model_id == shoe_model_id)
        .order_by(ShoeModelClass.shoe_model_class_id)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


async def get_shoe_model_class(
    session: AsyncSession,
    shoe_model_class_id: int,
) -> ShoeModelClass | None:
    statement = select(ShoeModelClass).where(
        ShoeModelClass.shoe_model_class_id == shoe_model_class_id
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()
