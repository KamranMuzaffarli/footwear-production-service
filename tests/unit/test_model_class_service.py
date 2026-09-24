from types import SimpleNamespace
from unittest.mock import AsyncMock, call

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.model_class as service
from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    EntityNotFoundError,
)
from app.schemas.shoe_model import (
    ShoeModelClassClone,
    ShoeModelClassCreate,
    ShoeModelClassUpdate,
)


def make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def make_create_data() -> ShoeModelClassCreate:
    return ShoeModelClassCreate(
        class_code="UNIT_CLASS",
        class_name="Unit Class",
        construction_method_id=2,
        quality_level="standard",
        warranty_months=12,
        description="Unit test class",
        is_active=True,
    )


async def test_create_model_class_rejects_missing_parent_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_model",
        AsyncMock(return_value=None),
    )

    with pytest.raises(EntityNotFoundError):
        await service.create_model_class(
            session,
            10,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_model_class_rejects_missing_construction_method(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_model",
        AsyncMock(return_value=SimpleNamespace(shoe_model_id=10)),
    )
    monkeypatch.setattr(
        service,
        "get_construction_method",
        AsyncMock(return_value=None),
    )

    with pytest.raises(EntityNotFoundError):
        await service.create_model_class(
            session,
            10,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_model_class_rejects_inactive_construction_method(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_model",
        AsyncMock(return_value=SimpleNamespace(shoe_model_id=10)),
    )
    monkeypatch.setattr(
        service,
        "get_construction_method",
        AsyncMock(return_value=SimpleNamespace(is_active=False)),
    )

    with pytest.raises(BusinessRuleError):
        await service.create_model_class(
            session,
            10,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_model_class_rejects_duplicate_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_model",
        AsyncMock(return_value=SimpleNamespace(shoe_model_id=10)),
    )
    monkeypatch.setattr(
        service,
        "get_construction_method",
        AsyncMock(return_value=SimpleNamespace(is_active=True)),
    )
    monkeypatch.setattr(
        service,
        "get_shoe_model_class_by_code",
        AsyncMock(return_value=SimpleNamespace(shoe_model_class_id=20)),
    )

    with pytest.raises(ConflictError):
        await service.create_model_class(
            session,
            10,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_model_class_commits_successful_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()
    created_class = SimpleNamespace(shoe_model_class_id=20)

    monkeypatch.setattr(
        service,
        "get_shoe_model",
        AsyncMock(return_value=SimpleNamespace(shoe_model_id=10)),
    )
    monkeypatch.setattr(
        service,
        "get_construction_method",
        AsyncMock(return_value=SimpleNamespace(is_active=True)),
    )
    monkeypatch.setattr(
        service,
        "get_shoe_model_class_by_code",
        AsyncMock(return_value=None),
    )

    repository_create = AsyncMock(return_value=created_class)
    monkeypatch.setattr(
        service,
        "repository_create_shoe_model_class",
        repository_create,
    )

    data = make_create_data()

    result = await service.create_model_class(
        session,
        10,
        data,
    )

    assert result is created_class

    repository_create.assert_awaited_once_with(
        session,
        shoe_model_id=10,
        data=data.model_dump(),
    )
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(created_class)
    session.rollback.assert_not_awaited()


async def test_update_model_class_rejects_missing_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_shoe_model_class",
        AsyncMock(return_value=None),
    )

    with pytest.raises(EntityNotFoundError):
        await service.update_model_class(
            session,
            999,
            ShoeModelClassUpdate(quality_level="premium"),
        )

    session.commit.assert_not_awaited()


async def test_update_model_class_rejects_inactive_new_construction_method(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()
    model_class = SimpleNamespace(shoe_model_class_id=20)

    monkeypatch.setattr(
        service,
        "get_shoe_model_class",
        AsyncMock(return_value=model_class),
    )
    monkeypatch.setattr(
        service,
        "get_construction_method",
        AsyncMock(return_value=SimpleNamespace(is_active=False)),
    )

    with pytest.raises(BusinessRuleError):
        await service.update_model_class(
            session,
            20,
            ShoeModelClassUpdate(construction_method_id=3),
        )

    session.commit.assert_not_awaited()


async def test_update_model_class_validates_method_and_commits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()
    model_class = SimpleNamespace(shoe_model_class_id=20)

    get_construction_method = AsyncMock(return_value=SimpleNamespace(is_active=True))
    repository_update = AsyncMock(return_value=model_class)

    monkeypatch.setattr(
        service,
        "get_shoe_model_class",
        AsyncMock(return_value=model_class),
    )
    monkeypatch.setattr(
        service,
        "get_construction_method",
        get_construction_method,
    )
    monkeypatch.setattr(
        service,
        "repository_update_shoe_model_class",
        repository_update,
    )

    result = await service.update_model_class(
        session,
        20,
        ShoeModelClassUpdate(
            construction_method_id=3,
            quality_level="premium",
        ),
    )

    assert result is model_class

    get_construction_method.assert_awaited_once_with(
        session,
        3,
    )
    repository_update.assert_awaited_once_with(
        session,
        model_class,
        {
            "construction_method_id": 3,
            "quality_level": "premium",
        },
    )
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(model_class)


async def test_clone_model_class_copies_active_compositions_and_commits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    source = SimpleNamespace(
        shoe_model_class_id=20,
        shoe_model_id=10,
        construction_method_id=2,
        quality_level="premium",
        warranty_months=24,
        description="Source class",
        is_active=True,
    )

    source_compositions = [
        SimpleNamespace(
            material_id=100,
            material_usage_role_id=1,
            consumption_quantity=1.5,
            consumption_unit="pair",
            is_required=True,
            description="First",
        ),
        SimpleNamespace(
            material_id=101,
            material_usage_role_id=2,
            consumption_quantity=0.5,
            consumption_unit="meter",
            is_required=False,
            description="Second",
        ),
    ]

    cloned_class = SimpleNamespace(shoe_model_class_id=30)

    monkeypatch.setattr(
        service,
        "get_shoe_model_class",
        AsyncMock(return_value=source),
    )
    monkeypatch.setattr(
        service,
        "get_shoe_model_class_by_code",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        service,
        "list_active_compositions",
        AsyncMock(return_value=source_compositions),
    )

    repository_create_class = AsyncMock(return_value=cloned_class)
    repository_create_composition = AsyncMock()

    monkeypatch.setattr(
        service,
        "repository_create_shoe_model_class",
        repository_create_class,
    )
    monkeypatch.setattr(
        service,
        "repository_create_composition",
        repository_create_composition,
    )

    result = await service.clone_model_class(
        session,
        20,
        ShoeModelClassClone(
            class_code="CLONE_UNIT",
            class_name="Clone Unit",
        ),
    )

    assert result is cloned_class

    repository_create_class.assert_awaited_once_with(
        session,
        shoe_model_id=10,
        data={
            "construction_method_id": 2,
            "class_code": "CLONE_UNIT",
            "class_name": "Clone Unit",
            "quality_level": "premium",
            "warranty_months": 24,
            "description": "Source class",
            "is_active": True,
        },
    )

    assert repository_create_composition.await_args_list == [
        call(
            session,
            shoe_model_class_id=30,
            data={
                "material_id": 100,
                "material_usage_role_id": 1,
                "consumption_quantity": 1.5,
                "consumption_unit": "pair",
                "is_required": True,
                "description": "First",
                "is_active": True,
            },
        ),
        call(
            session,
            shoe_model_class_id=30,
            data={
                "material_id": 101,
                "material_usage_role_id": 2,
                "consumption_quantity": 0.5,
                "consumption_unit": "meter",
                "is_required": False,
                "description": "Second",
                "is_active": True,
            },
        ),
    ]

    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(cloned_class)
