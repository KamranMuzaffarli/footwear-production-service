from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.production_composition as service
from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    EntityNotFoundError,
)
from app.schemas.production_composition import (
    ProductionCompositionCreate,
    ProductionCompositionUpdate,
)


def make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def make_create_data() -> ProductionCompositionCreate:
    return ProductionCompositionCreate(
        material_id=100,
        material_usage_role_id=5,
        consumption_quantity=Decimal("1.500"),
        consumption_unit="pair",
        is_required=True,
        description="Unit composition",
    )


def patch_valid_create_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_id=20
            )
        ),
    )
    monkeypatch.setattr(
        service,
        "get_material",
        AsyncMock(
            return_value=SimpleNamespace(is_active=True)
        ),
    )
    monkeypatch.setattr(
        service,
        "get_usage_role",
        AsyncMock(
            return_value=SimpleNamespace(is_active=True)
        ),
    )


async def test_create_composition_rejects_missing_model_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(return_value=None),
    )

    with pytest.raises(EntityNotFoundError):
        await service.create_production_composition(
            session,
            20,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_composition_rejects_missing_material(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_id=20
            )
        ),
    )
    monkeypatch.setattr(
        service,
        "get_material",
        AsyncMock(return_value=None),
    )

    with pytest.raises(EntityNotFoundError):
        await service.create_production_composition(
            session,
            20,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_composition_rejects_inactive_material(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_id=20
            )
        ),
    )
    monkeypatch.setattr(
        service,
        "get_material",
        AsyncMock(
            return_value=SimpleNamespace(is_active=False)
        ),
    )

    with pytest.raises(BusinessRuleError):
        await service.create_production_composition(
            session,
            20,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_composition_rejects_missing_usage_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_id=20
            )
        ),
    )
    monkeypatch.setattr(
        service,
        "get_material",
        AsyncMock(
            return_value=SimpleNamespace(is_active=True)
        ),
    )
    monkeypatch.setattr(
        service,
        "get_usage_role",
        AsyncMock(return_value=None),
    )

    with pytest.raises(EntityNotFoundError):
        await service.create_production_composition(
            session,
            20,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_composition_rejects_inactive_usage_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_id=20
            )
        ),
    )
    monkeypatch.setattr(
        service,
        "get_material",
        AsyncMock(
            return_value=SimpleNamespace(is_active=True)
        ),
    )
    monkeypatch.setattr(
        service,
        "get_usage_role",
        AsyncMock(
            return_value=SimpleNamespace(is_active=False)
        ),
    )

    with pytest.raises(BusinessRuleError):
        await service.create_production_composition(
            session,
            20,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_composition_conflicts_with_active_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    patch_valid_create_dependencies(monkeypatch)

    existing = SimpleNamespace(
        shoe_model_class_material_id=30,
        is_active=True,
    )

    monkeypatch.setattr(
        service,
        "get_composition_by_combination",
        AsyncMock(return_value=existing),
    )

    with pytest.raises(ConflictError):
        await service.create_production_composition(
            session,
            20,
            make_create_data(),
        )

    session.commit.assert_not_awaited()


async def test_create_composition_reactivates_inactive_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    patch_valid_create_dependencies(monkeypatch)

    existing = SimpleNamespace(
        shoe_model_class_material_id=30,
        is_active=False,
    )
    reloaded = SimpleNamespace(
        shoe_model_class_material_id=30,
        is_active=True,
    )

    monkeypatch.setattr(
        service,
        "get_composition_by_combination",
        AsyncMock(return_value=existing),
    )

    repository_update = AsyncMock(
        return_value=existing
    )
    monkeypatch.setattr(
        service,
        "repository_update_composition",
        repository_update,
    )
    monkeypatch.setattr(
        service,
        "get_composition",
        AsyncMock(return_value=reloaded),
    )

    data = ProductionCompositionCreate(
        material_id=100,
        material_usage_role_id=5,
        consumption_quantity=Decimal("2.250"),
        description="Reactivated",
    )

    result = await service.create_production_composition(
        session,
        20,
        data,
    )

    assert result is reloaded

    repository_update.assert_awaited_once_with(
        session,
        existing,
        {
            "consumption_quantity": Decimal("2.250"),
            "description": "Reactivated",
            "is_active": True,
        },
    )

    session.commit.assert_awaited_once()


async def test_create_composition_creates_new_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    patch_valid_create_dependencies(monkeypatch)

    monkeypatch.setattr(
        service,
        "get_composition_by_combination",
        AsyncMock(return_value=None),
    )

    created = SimpleNamespace(
        shoe_model_class_material_id=30
    )
    reloaded = SimpleNamespace(
        shoe_model_class_material_id=30,
        is_active=True,
    )

    repository_create = AsyncMock(
        return_value=created
    )
    monkeypatch.setattr(
        service,
        "repository_create_composition",
        repository_create,
    )
    monkeypatch.setattr(
        service,
        "get_composition",
        AsyncMock(return_value=reloaded),
    )

    data = make_create_data()

    result = await service.create_production_composition(
        session,
        20,
        data,
    )

    assert result is reloaded

    repository_create.assert_awaited_once_with(
        session,
        shoe_model_class_id=20,
        data=data.model_dump(),
    )

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


async def test_update_composition_rejects_ownership_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_id=20
            )
        ),
    )
    monkeypatch.setattr(
        service,
        "get_composition",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_material_id=30,
                shoe_model_class_id=999,
            )
        ),
    )

    with pytest.raises(EntityNotFoundError):
        await service.update_production_composition(
            session,
            20,
            30,
            ProductionCompositionUpdate(
                consumption_unit="meter"
            ),
        )

    session.commit.assert_not_awaited()


async def test_update_composition_passes_only_explicit_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    composition = SimpleNamespace(
        shoe_model_class_material_id=30,
        shoe_model_class_id=20,
    )
    reloaded = SimpleNamespace(
        shoe_model_class_material_id=30,
        shoe_model_class_id=20,
    )

    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_id=20
            )
        ),
    )
    monkeypatch.setattr(
        service,
        "get_composition",
        AsyncMock(
            side_effect=[
                composition,
                reloaded,
            ]
        ),
    )

    repository_update = AsyncMock(
        return_value=composition
    )
    monkeypatch.setattr(
        service,
        "repository_update_composition",
        repository_update,
    )

    result = await service.update_production_composition(
        session,
        20,
        30,
        ProductionCompositionUpdate(
            consumption_unit="meter"
        ),
    )

    assert result is reloaded

    repository_update.assert_awaited_once_with(
        session,
        composition,
        {"consumption_unit": "meter"},
    )

    session.commit.assert_awaited_once()


async def test_deactivate_composition_rejects_ownership_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_id=20
            )
        ),
    )
    monkeypatch.setattr(
        service,
        "get_composition",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_material_id=30,
                shoe_model_class_id=999,
            )
        ),
    )

    with pytest.raises(EntityNotFoundError):
        await service.deactivate_production_composition(
            session,
            20,
            30,
        )

    session.commit.assert_not_awaited()


async def test_deactivate_composition_uses_soft_deactivation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    composition = SimpleNamespace(
        shoe_model_class_material_id=30,
        shoe_model_class_id=20,
    )

    monkeypatch.setattr(
        service,
        "get_model_class",
        AsyncMock(
            return_value=SimpleNamespace(
                shoe_model_class_id=20
            )
        ),
    )
    monkeypatch.setattr(
        service,
        "get_composition",
        AsyncMock(return_value=composition),
    )

    repository_deactivate = AsyncMock()
    monkeypatch.setattr(
        service,
        "repository_deactivate_composition",
        repository_deactivate,
    )

    result = await service.deactivate_production_composition(
        session,
        20,
        30,
    )

    assert result is None

    repository_deactivate.assert_awaited_once_with(
        session,
        composition,
    )
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()
