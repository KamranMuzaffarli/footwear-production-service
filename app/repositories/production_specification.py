from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.material import (
    Material,
    MaterialAttributeValue,
    ShoeModelClassMaterial,
)
from app.models.shoe_model import (
    ShoeModel,
    ShoeModelClass,
)


async def get_model_class_specification(
    session: AsyncSession,
    shoe_model_class_id: int,
) -> ShoeModelClass | None:
    statement = (
        select(ShoeModelClass)
        .where(
            ShoeModelClass.shoe_model_class_id
            == shoe_model_class_id
        )
        .options(
            selectinload(
                ShoeModelClass.shoe_model
            ).selectinload(
                ShoeModel.shoe_last
            ),
            selectinload(
                ShoeModelClass.construction_method
            ),
            selectinload(
                ShoeModelClass.compositions.and_(
                    ShoeModelClassMaterial.is_active.is_(True)
                )
            )
            .selectinload(
                ShoeModelClassMaterial.material
            )
            .selectinload(
                Material.category
            ),
            selectinload(
                ShoeModelClass.compositions.and_(
                    ShoeModelClassMaterial.is_active.is_(True)
                )
            )
            .selectinload(
                ShoeModelClassMaterial.material
            )
            .selectinload(
                Material.attribute_values
            )
            .selectinload(
                MaterialAttributeValue.attribute
            ),
            selectinload(
                ShoeModelClass.compositions.and_(
                    ShoeModelClassMaterial.is_active.is_(True)
                )
            )
            .selectinload(
                ShoeModelClassMaterial.usage_role
            ),
        )
    )

    result = await session.execute(statement)

    return result.scalar_one_or_none()
