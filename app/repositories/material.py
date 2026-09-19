from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.material import (
    Material,
    MaterialAttributeValue,
    MaterialCategory,
)


async def list_materials(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    category: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> list[Material]:
    statement = select(Material)

    if category is not None:
        statement = (
            statement
            .join(Material.category)
            .where(
                MaterialCategory.material_category_code == category
            )
        )

    if is_active is not None:
        statement = statement.where(
            Material.is_active == is_active
        )

    if search is not None:
        search_pattern = f"%{search}%"

        statement = statement.where(
            or_(
                Material.material_code.ilike(search_pattern),
                Material.material_name.ilike(search_pattern),
            )
        )

    statement = (
        statement
        .order_by(Material.material_id)
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


async def get_material(
    session: AsyncSession,
    material_id: int,
) -> Material | None:
    statement = (
        select(Material)
        .where(Material.material_id == material_id)
        .options(
            selectinload(Material.category),
            selectinload(Material.attribute_values)
            .selectinload(MaterialAttributeValue.attribute),
        )
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()
