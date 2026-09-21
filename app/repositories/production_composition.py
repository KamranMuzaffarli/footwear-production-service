from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.material import (
    Material,
    MaterialUsageRole,
    ShoeModelClassMaterial,
)
from app.models.shoe_model import ShoeModelClass


async def get_model_class(
    session: AsyncSession,
    shoe_model_class_id: int,
) -> ShoeModelClass | None:
    return await session.get(
        ShoeModelClass,
        shoe_model_class_id,
    )


async def get_material(
    session: AsyncSession,
    material_id: int,
) -> Material | None:
    return await session.get(
        Material,
        material_id,
    )


async def get_usage_role(
    session: AsyncSession,
    material_usage_role_id: int,
) -> MaterialUsageRole | None:
    return await session.get(
        MaterialUsageRole,
        material_usage_role_id,
    )


async def get_composition(
    session: AsyncSession,
    composition_id: int,
) -> ShoeModelClassMaterial | None:
    statement = (
        select(ShoeModelClassMaterial)
        .where(
            ShoeModelClassMaterial.shoe_model_class_material_id
            == composition_id
        )
        .options(
            selectinload(ShoeModelClassMaterial.material),
            selectinload(ShoeModelClassMaterial.usage_role),
        )
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def get_composition_by_combination(
    session: AsyncSession,
    *,
    shoe_model_class_id: int,
    material_id: int,
    material_usage_role_id: int,
) -> ShoeModelClassMaterial | None:
    statement = select(ShoeModelClassMaterial).where(
        ShoeModelClassMaterial.shoe_model_class_id
        == shoe_model_class_id,
        ShoeModelClassMaterial.material_id == material_id,
        ShoeModelClassMaterial.material_usage_role_id
        == material_usage_role_id,
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()


async def list_active_compositions(
    session: AsyncSession,
    shoe_model_class_id: int,
) -> list[ShoeModelClassMaterial]:
    statement = (
        select(ShoeModelClassMaterial)
        .where(
            ShoeModelClassMaterial.shoe_model_class_id
            == shoe_model_class_id,
            ShoeModelClassMaterial.is_active.is_(True),
        )
        .options(
            selectinload(ShoeModelClassMaterial.material),
            selectinload(ShoeModelClassMaterial.usage_role),
        )
        .order_by(
            ShoeModelClassMaterial.shoe_model_class_material_id
        )
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


async def create_composition(
    session: AsyncSession,
    *,
    shoe_model_class_id: int,
    data: dict,
) -> ShoeModelClassMaterial:
    composition = ShoeModelClassMaterial(
        shoe_model_class_id=shoe_model_class_id,
        **data,
    )

    session.add(composition)

    await session.flush()

    return composition


async def update_composition(
    session: AsyncSession,
    composition: ShoeModelClassMaterial,
    data: dict,
) -> ShoeModelClassMaterial:
    for field, value in data.items():
        setattr(composition, field, value)

    await session.flush()

    return composition


async def deactivate_composition(
    session: AsyncSession,
    composition: ShoeModelClassMaterial,
) -> ShoeModelClassMaterial:
    composition.is_active = False

    await session.flush()

    return composition
