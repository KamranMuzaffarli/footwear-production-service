from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.construction import ShoeConstructionMethod
from app.models.material import MaterialCategory, MaterialUsageRole


async def list_construction_methods(
    session: AsyncSession,
) -> list[ShoeConstructionMethod]:
    statement = select(ShoeConstructionMethod).order_by(
        ShoeConstructionMethod.construction_method_id
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


async def list_material_categories(
    session: AsyncSession,
) -> list[MaterialCategory]:
    statement = select(MaterialCategory).order_by(MaterialCategory.material_category_id)

    result = await session.execute(statement)

    return list(result.scalars().all())


async def list_material_usage_roles(
    session: AsyncSession,
) -> list[MaterialUsageRole]:
    statement = select(MaterialUsageRole).order_by(
        MaterialUsageRole.material_usage_role_id
    )

    result = await session.execute(statement)

    return list(result.scalars().all())
