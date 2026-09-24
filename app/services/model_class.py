import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    EntityNotFoundError,
)
from app.models.shoe_model import ShoeModelClass
from app.repositories.production_composition import (
    create_composition as repository_create_composition,
)
from app.repositories.production_composition import (
    list_active_compositions,
)
from app.repositories.shoe_model import (
    create_shoe_model_class as repository_create_shoe_model_class,
)
from app.repositories.shoe_model import (
    get_construction_method,
    get_shoe_model,
    get_shoe_model_class,
    get_shoe_model_class_by_code,
)
from app.repositories.shoe_model import (
    update_shoe_model_class as repository_update_shoe_model_class,
)
from app.schemas.shoe_model import (
    ShoeModelClassClone,
    ShoeModelClassCreate,
    ShoeModelClassUpdate,
)

logger = logging.getLogger(__name__)


async def _validate_construction_method(
    session: AsyncSession,
    construction_method_id: int,
) -> None:
    construction_method = await get_construction_method(
        session,
        construction_method_id,
    )

    if construction_method is None:
        raise EntityNotFoundError("Construction Method not found")

    if not construction_method.is_active:
        raise BusinessRuleError("Construction Method is not active")


async def _validate_class_code(
    session: AsyncSession,
    shoe_model_id: int,
    class_code: str,
) -> None:
    existing_class = await get_shoe_model_class_by_code(
        session,
        shoe_model_id,
        class_code,
    )

    if existing_class is not None:
        raise ConflictError("Model Class code already exists for this Shoe Model")


async def create_model_class(
    session: AsyncSession,
    shoe_model_id: int,
    data: ShoeModelClassCreate,
) -> ShoeModelClass:
    shoe_model = await get_shoe_model(
        session,
        shoe_model_id,
    )

    if shoe_model is None:
        raise EntityNotFoundError("Shoe Model not found")

    await _validate_construction_method(
        session,
        data.construction_method_id,
    )

    await _validate_class_code(
        session,
        shoe_model_id,
        data.class_code,
    )

    try:
        shoe_model_class = await repository_create_shoe_model_class(
            session,
            shoe_model_id=shoe_model_id,
            data=data.model_dump(),
        )

        await session.commit()

    except IntegrityError as exc:
        await session.rollback()
        logger.warning(
            "Model Class create transaction rolled back after integrity error"
        )
        raise ConflictError("Model Class conflicts with existing data") from exc

    except Exception:
        await session.rollback()
        logger.exception("Model Class create transaction failed; changes rolled back")
        raise

    await session.refresh(shoe_model_class)

    return shoe_model_class


async def update_model_class(
    session: AsyncSession,
    shoe_model_class_id: int,
    data: ShoeModelClassUpdate,
) -> ShoeModelClass:
    shoe_model_class = await get_shoe_model_class(
        session,
        shoe_model_class_id,
    )

    if shoe_model_class is None:
        raise EntityNotFoundError("Model Class not found")

    update_data = data.model_dump(exclude_unset=True)

    if "construction_method_id" in update_data:
        await _validate_construction_method(
            session,
            update_data["construction_method_id"],
        )

    if not update_data:
        return shoe_model_class

    try:
        shoe_model_class = await repository_update_shoe_model_class(
            session,
            shoe_model_class,
            update_data,
        )

        await session.commit()

    except IntegrityError as exc:
        await session.rollback()
        logger.warning(
            "Model Class update transaction rolled back after integrity error"
        )
        raise ConflictError("Model Class conflicts with existing data") from exc

    except Exception:
        await session.rollback()
        logger.exception("Model Class update transaction failed; changes rolled back")
        raise

    await session.refresh(shoe_model_class)

    return shoe_model_class


async def clone_model_class(
    session: AsyncSession,
    shoe_model_class_id: int,
    data: ShoeModelClassClone,
) -> ShoeModelClass:
    source = await get_shoe_model_class(
        session,
        shoe_model_class_id,
    )

    if source is None:
        raise EntityNotFoundError("Model Class not found")

    await _validate_class_code(
        session,
        source.shoe_model_id,
        data.class_code,
    )

    source_compositions = await list_active_compositions(
        session,
        shoe_model_class_id,
    )

    class_data = {
        "construction_method_id": source.construction_method_id,
        "class_code": data.class_code,
        "class_name": data.class_name,
        "quality_level": source.quality_level,
        "warranty_months": source.warranty_months,
        "description": source.description,
        "is_active": source.is_active,
    }

    try:
        cloned_class = await repository_create_shoe_model_class(
            session,
            shoe_model_id=source.shoe_model_id,
            data=class_data,
        )

        for source_composition in source_compositions:
            composition_data = {
                "material_id": source_composition.material_id,
                "material_usage_role_id": source_composition.material_usage_role_id,
                "consumption_quantity": source_composition.consumption_quantity,
                "consumption_unit": source_composition.consumption_unit,
                "is_required": source_composition.is_required,
                "description": source_composition.description,
                "is_active": True,
            }

            await repository_create_composition(
                session,
                shoe_model_class_id=(cloned_class.shoe_model_class_id),
                data=composition_data,
            )

        await session.commit()

    except IntegrityError as exc:
        await session.rollback()
        logger.warning(
            "Model Class clone transaction rolled back after integrity error"
        )
        raise ConflictError("Model Class clone conflicts with existing data") from exc

    except Exception:
        await session.rollback()
        logger.exception("Model Class clone transaction failed; changes rolled back")
        raise

    await session.refresh(cloned_class)

    return cloned_class
