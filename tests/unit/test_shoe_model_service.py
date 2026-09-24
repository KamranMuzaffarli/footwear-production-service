from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.shoe_model as service
from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    EntityNotFoundError,
)
from app.schemas.shoe_model import (
    ShoeModelCreate,
    ShoeModelUpdate,
)


def make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def make_create_data() -> ShoeModelCreate:
    return ShoeModelCreate(
        shoe_last_id=1,
        model_code="UNIT_MODEL",
        model_name="Unit Model",
        footwear_category="casual",
        footwear_type="shoe",
        target_group="adult",
        description="Unit test model",
        is_active=True,
    )


async def test_create_shoe_model_rejects_missing_shoe_last(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_last",
        AsyncMock(return_value=None),
    )

    with pytest.raises(EntityNotFoundError):
        await service.create_shoe_model(
            session,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_shoe_model_rejects_inactive_shoe_last(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_last",
        AsyncMock(return_value=SimpleNamespace(is_active=False)),
    )

    with pytest.raises(BusinessRuleError):
        await service.create_shoe_model(
            session,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_shoe_model_rejects_duplicate_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_last",
        AsyncMock(return_value=SimpleNamespace(is_active=True)),
    )
    monkeypatch.setattr(
        service,
        "get_shoe_model_by_code",
        AsyncMock(return_value=SimpleNamespace(shoe_model_id=99)),
    )

    with pytest.raises(ConflictError):
        await service.create_shoe_model(
            session,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_shoe_model_commits_successful_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()
    created_model = SimpleNamespace(shoe_model_id=10)

    monkeypatch.setattr(
        service,
        "get_shoe_last",
        AsyncMock(return_value=SimpleNamespace(is_active=True)),
    )
    monkeypatch.setattr(
        service,
        "get_shoe_model_by_code",
        AsyncMock(return_value=None),
    )

    repository_create = AsyncMock(return_value=created_model)
    monkeypatch.setattr(
        service,
        "repository_create_shoe_model",
        repository_create,
    )

    result = await service.create_shoe_model(
        session,
        make_create_data(),
    )

    assert result is created_model

    repository_create.assert_awaited_once_with(
        session,
        make_create_data().model_dump(),
    )
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(created_model)
    session.rollback.assert_not_awaited()


async def test_create_shoe_model_rolls_back_integrity_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_last",
        AsyncMock(return_value=SimpleNamespace(is_active=True)),
    )
    monkeypatch.setattr(
        service,
        "get_shoe_model_by_code",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        service,
        "repository_create_shoe_model",
        AsyncMock(
            side_effect=IntegrityError(
                "INSERT",
                {},
                Exception("duplicate"),
            )
        ),
    )

    with pytest.raises(ConflictError):
        await service.create_shoe_model(
            session,
            make_create_data(),
        )

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


async def test_update_shoe_model_rejects_missing_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_model",
        AsyncMock(return_value=None),
    )

    with pytest.raises(EntityNotFoundError):
        await service.update_shoe_model(
            session,
            999,
            ShoeModelUpdate(model_name="Updated"),
        )

    session.commit.assert_not_awaited()


async def test_update_shoe_model_validates_new_shoe_last(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()
    model = SimpleNamespace(shoe_model_id=10)

    get_shoe_last = AsyncMock(return_value=SimpleNamespace(is_active=True))
    repository_update = AsyncMock(return_value=model)

    monkeypatch.setattr(
        service,
        "get_shoe_model",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        service,
        "get_shoe_last",
        get_shoe_last,
    )
    monkeypatch.setattr(
        service,
        "repository_update_shoe_model",
        repository_update,
    )

    await service.update_shoe_model(
        session,
        10,
        ShoeModelUpdate(shoe_last_id=2),
    )

    get_shoe_last.assert_awaited_once_with(
        session,
        2,
    )
    repository_update.assert_awaited_once_with(
        session,
        model,
        {"shoe_last_id": 2},
    )
    session.commit.assert_awaited_once()


async def test_update_shoe_model_rejects_conflicting_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()
    model = SimpleNamespace(shoe_model_id=10)

    monkeypatch.setattr(
        service,
        "get_shoe_model",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        service,
        "get_shoe_model_by_code",
        AsyncMock(return_value=SimpleNamespace(shoe_model_id=11)),
    )

    with pytest.raises(ConflictError):
        await service.update_shoe_model(
            session,
            10,
            ShoeModelUpdate(model_code="OTHER_CODE"),
        )

    session.commit.assert_not_awaited()


async def test_update_shoe_model_passes_only_explicit_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()
    model = SimpleNamespace(shoe_model_id=10)

    repository_update = AsyncMock(return_value=model)

    monkeypatch.setattr(
        service,
        "get_shoe_model",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        service,
        "repository_update_shoe_model",
        repository_update,
    )

    result = await service.update_shoe_model(
        session,
        10,
        ShoeModelUpdate(
            model_name="Updated Name",
        ),
    )

    assert result is model

    repository_update.assert_awaited_once_with(
        session,
        model,
        {"model_name": "Updated Name"},
    )
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(model)
