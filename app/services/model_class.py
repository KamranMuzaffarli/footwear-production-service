from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    EntityNotFoundError,
)
from app.models.shoe_model import ShoeModelClass
from app.repositories.shoe_model import (
    create_shoe_model_class as repository_create_shoe_model_class,
    get_construction_method,
    get_shoe_model,
    get_shoe_model_class,
    get_shoe_model_class_by_code,
    update_shoe_model_class as repository_update_shoe_model_class,
)
from app.schemas.shoe_model import (
    ShoeModelClassCreate,
    ShoeModelClassUpdate,
)


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
        raise ConflictError(
            "Model Class code already exists for this Shoe Model"
        )


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
        raise ConflictError(
            "Model Class conflicts with existing data"
        ) from exc

    except Exception:
        await session.rollback()
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
        raise ConflictError(
            "Model Class conflicts with existing data"
        ) from exc

    except Exception:
        await session.rollback()
        raise

    await session.refresh(shoe_model_class)

    return shoe_model_class
