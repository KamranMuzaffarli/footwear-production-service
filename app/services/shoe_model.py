import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    EntityNotFoundError,
)
from app.models.shoe_model import ShoeModel
from app.repositories.shoe_model import (
    create_shoe_model as repository_create_shoe_model,
)
from app.repositories.shoe_model import (
    get_shoe_last,
    get_shoe_model,
    get_shoe_model_by_code,
)
from app.repositories.shoe_model import (
    update_shoe_model as repository_update_shoe_model,
)
from app.schemas.shoe_model import ShoeModelCreate, ShoeModelUpdate

logger = logging.getLogger(__name__)


async def _validate_shoe_last(
    session: AsyncSession,
    shoe_last_id: int,
) -> None:
    shoe_last = await get_shoe_last(session, shoe_last_id)

    if shoe_last is None:
        raise EntityNotFoundError("Shoe Last not found")

    if not shoe_last.is_active:
        raise BusinessRuleError("Shoe Last is not active")


async def _validate_model_code(
    session: AsyncSession,
    model_code: str,
    *,
    current_model_id: int | None = None,
) -> None:
    existing_model = await get_shoe_model_by_code(
        session,
        model_code,
    )

    if existing_model is not None and existing_model.shoe_model_id != current_model_id:
        raise ConflictError("Shoe Model code already exists")


async def create_shoe_model(
    session: AsyncSession,
    data: ShoeModelCreate,
) -> ShoeModel:
    await _validate_shoe_last(
        session,
        data.shoe_last_id,
    )

    await _validate_model_code(
        session,
        data.model_code,
    )

    try:
        shoe_model = await repository_create_shoe_model(
            session,
            data.model_dump(),
        )

        await session.commit()

    except IntegrityError as exc:
        await session.rollback()
        logger.warning(
            "Shoe Model create transaction rolled back after integrity error"
        )
        raise ConflictError("Shoe Model conflicts with existing data") from exc

    except Exception:
        await session.rollback()
        logger.exception("Shoe Model create transaction failed; changes rolled back")
        raise

    await session.refresh(shoe_model)

    return shoe_model


async def update_shoe_model(
    session: AsyncSession,
    shoe_model_id: int,
    data: ShoeModelUpdate,
) -> ShoeModel:
    shoe_model = await get_shoe_model(
        session,
        shoe_model_id,
    )

    if shoe_model is None:
        raise EntityNotFoundError("Shoe Model not found")

    update_data = data.model_dump(exclude_unset=True)

    if "shoe_last_id" in update_data:
        await _validate_shoe_last(
            session,
            update_data["shoe_last_id"],
        )

    if "model_code" in update_data:
        await _validate_model_code(
            session,
            update_data["model_code"],
            current_model_id=shoe_model.shoe_model_id,
        )

    if not update_data:
        return shoe_model

    try:
        shoe_model = await repository_update_shoe_model(
            session,
            shoe_model,
            update_data,
        )

        await session.commit()

    except IntegrityError as exc:
        await session.rollback()
        logger.warning(
            "Shoe Model update transaction rolled back after integrity error"
        )
        raise ConflictError("Shoe Model conflicts with existing data") from exc

    except Exception:
        await session.rollback()
        logger.exception("Shoe Model update transaction failed; changes rolled back")
        raise

    await session.refresh(shoe_model)

    return shoe_model
