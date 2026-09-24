import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    EntityNotFoundError,
)
from app.models.material import ShoeModelClassMaterial
from app.repositories.production_composition import (
    create_composition as repository_create_composition,
)
from app.repositories.production_composition import (
    deactivate_composition as repository_deactivate_composition,
)
from app.repositories.production_composition import (
    get_composition,
    get_composition_by_combination,
    get_material,
    get_model_class,
    get_usage_role,
    list_active_compositions,
)
from app.repositories.production_composition import (
    update_composition as repository_update_composition,
)
from app.schemas.production_composition import (
    ProductionCompositionCreate,
    ProductionCompositionUpdate,
)

logger = logging.getLogger(__name__)


async def _validate_model_class(
    session: AsyncSession,
    shoe_model_class_id: int,
) -> None:
    model_class = await get_model_class(
        session,
        shoe_model_class_id,
    )

    if model_class is None:
        raise EntityNotFoundError("Model Class not found")


async def _validate_material(
    session: AsyncSession,
    material_id: int,
) -> None:
    material = await get_material(
        session,
        material_id,
    )

    if material is None:
        raise EntityNotFoundError("Material not found")

    if not material.is_active:
        raise BusinessRuleError("Material is not active")


async def _validate_usage_role(
    session: AsyncSession,
    material_usage_role_id: int,
) -> None:
    usage_role = await get_usage_role(
        session,
        material_usage_role_id,
    )

    if usage_role is None:
        raise EntityNotFoundError("Material Usage Role not found")

    if not usage_role.is_active:
        raise BusinessRuleError("Material Usage Role is not active")


async def _get_owned_composition(
    session: AsyncSession,
    shoe_model_class_id: int,
    composition_id: int,
) -> ShoeModelClassMaterial:
    composition = await get_composition(
        session,
        composition_id,
    )

    if composition is None or composition.shoe_model_class_id != shoe_model_class_id:
        raise EntityNotFoundError("Production Composition not found")

    return composition


async def list_production_compositions(
    session: AsyncSession,
    shoe_model_class_id: int,
) -> list[ShoeModelClassMaterial]:
    await _validate_model_class(
        session,
        shoe_model_class_id,
    )

    return await list_active_compositions(
        session,
        shoe_model_class_id,
    )


async def create_production_composition(
    session: AsyncSession,
    shoe_model_class_id: int,
    data: ProductionCompositionCreate,
) -> ShoeModelClassMaterial:
    await _validate_model_class(
        session,
        shoe_model_class_id,
    )

    await _validate_material(
        session,
        data.material_id,
    )

    await _validate_usage_role(
        session,
        data.material_usage_role_id,
    )

    existing_composition = await get_composition_by_combination(
        session,
        shoe_model_class_id=shoe_model_class_id,
        material_id=data.material_id,
        material_usage_role_id=data.material_usage_role_id,
    )

    if existing_composition is not None and existing_composition.is_active:
        raise ConflictError("Production Composition already exists")

    try:
        if existing_composition is not None:
            reactivation_data = data.model_dump(
                exclude_unset=True,
                exclude={
                    "material_id",
                    "material_usage_role_id",
                },
            )
            reactivation_data["is_active"] = True

            composition = await repository_update_composition(
                session,
                existing_composition,
                reactivation_data,
            )

        else:
            composition = await repository_create_composition(
                session,
                shoe_model_class_id=shoe_model_class_id,
                data=data.model_dump(),
            )

        await session.commit()

    except IntegrityError as exc:
        await session.rollback()
        logger.warning(
            "Production Composition create transaction rolled back "
            "after integrity error"
        )
        raise ConflictError(
            "Production Composition conflicts with existing data"
        ) from exc

    except Exception:
        await session.rollback()
        logger.exception(
            "Production Composition create transaction failed; changes rolled back"
        )
        raise

    reloaded_composition = await get_composition(
        session,
        composition.shoe_model_class_material_id,
    )

    assert reloaded_composition is not None

    return reloaded_composition


async def update_production_composition(
    session: AsyncSession,
    shoe_model_class_id: int,
    composition_id: int,
    data: ProductionCompositionUpdate,
) -> ShoeModelClassMaterial:
    await _validate_model_class(
        session,
        shoe_model_class_id,
    )

    composition = await _get_owned_composition(
        session,
        shoe_model_class_id,
        composition_id,
    )

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        return composition

    try:
        composition = await repository_update_composition(
            session,
            composition,
            update_data,
        )

        await session.commit()

    except IntegrityError as exc:
        await session.rollback()
        logger.warning(
            "Production Composition update transaction rolled back "
            "after integrity error"
        )
        raise ConflictError(
            "Production Composition conflicts with existing data"
        ) from exc

    except Exception:
        await session.rollback()
        logger.exception(
            "Production Composition update transaction failed; changes rolled back"
        )
        raise

    reloaded_composition = await get_composition(
        session,
        composition.shoe_model_class_material_id,
    )

    assert reloaded_composition is not None

    return reloaded_composition


async def deactivate_production_composition(
    session: AsyncSession,
    shoe_model_class_id: int,
    composition_id: int,
) -> None:
    await _validate_model_class(
        session,
        shoe_model_class_id,
    )

    composition = await _get_owned_composition(
        session,
        shoe_model_class_id,
        composition_id,
    )

    try:
        await repository_deactivate_composition(
            session,
            composition,
        )

        await session.commit()

    except Exception:
        await session.rollback()
        logger.exception(
            "Production Composition deactivation transaction failed; "
            "changes rolled back"
        )
        raise
