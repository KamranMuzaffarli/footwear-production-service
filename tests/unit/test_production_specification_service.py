from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.production_specification as service
from app.core.exceptions import EntityNotFoundError


def make_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


def make_ready_graph() -> SimpleNamespace:
    shoe_last = SimpleNamespace(
        shoe_last_id=1,
        last_code="UNIT_LAST",
        last_name="Unit Last",
        last_type="standard",
        gender_category="unisex",
        size_system="EU",
        base_size=Decimal("42.0"),
        toe_shape="round",
        description="Unit test last",
        is_active=True,
    )

    shoe_model = SimpleNamespace(
        shoe_model_id=10,
        model_code="UNIT_MODEL",
        model_name="Unit Model",
        footwear_category="casual",
        footwear_type="shoe",
        target_group="adult",
        description="Unit test model",
        is_active=True,
        shoe_last=shoe_last,
    )

    construction_method = SimpleNamespace(
        construction_method_id=2,
        construction_method_code="cemented",
        construction_method_name="Cemented",
        difficulty_level="medium",
        description="Unit test construction method",
        is_active=True,
    )

    material_category = SimpleNamespace(
        material_category_id=3,
        material_category_code="leather",
        material_category_name="Leather",
        description="Unit test category",
        is_active=True,
    )

    material = SimpleNamespace(
        material_id=100,
        material_code="UNIT_MATERIAL",
        material_name="Unit Material",
        unit_of_measure="meter",
        description="Unit test material",
        is_active=True,
        category=material_category,
        attribute_values=[],
    )

    usage_role = SimpleNamespace(
        material_usage_role_id=5,
        material_role_code="upper",
        material_role_name="Upper",
        description="Unit test usage role",
        is_active=True,
    )

    composition = SimpleNamespace(
        shoe_model_class_material_id=30,
        consumption_quantity=Decimal("1.500"),
        consumption_unit="pair",
        is_required=True,
        description="Unit test composition",
        material=material,
        usage_role=usage_role,
    )

    return SimpleNamespace(
        shoe_model_class_id=20,
        class_code="UNIT_CLASS",
        class_name="Unit Class",
        quality_level="standard",
        warranty_months=12,
        description="Unit test class",
        is_active=True,
        shoe_model=shoe_model,
        construction_method=construction_method,
        compositions=[composition],
    )


async def get_result(
    monkeypatch: pytest.MonkeyPatch,
    graph: SimpleNamespace,
):
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_model_class_specification",
        AsyncMock(return_value=graph),
    )

    return await service.get_production_specification(
        session,
        graph.shoe_model_class_id,
    )


async def test_specification_rejects_missing_model_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = make_session()

    monkeypatch.setattr(
        service,
        "get_model_class_specification",
        AsyncMock(return_value=None),
    )

    with pytest.raises(EntityNotFoundError):
        await service.get_production_specification(
            session,
            999,
        )


async def test_specification_is_ready_when_all_rules_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = make_ready_graph()

    result = await get_result(
        monkeypatch,
        graph,
    )

    assert result.is_production_ready is True
    assert result.validation_issues == []
    assert len(result.composition) == 1


async def test_specification_reports_no_active_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = make_ready_graph()
    graph.compositions = []

    result = await get_result(
        monkeypatch,
        graph,
    )

    assert result.is_production_ready is False
    assert [issue.code for issue in result.validation_issues] == [
        "no_active_composition"
    ]


@pytest.mark.parametrize(
    ("target", "expected_code"),
    [
        (
            "shoe_model",
            "inactive_shoe_model",
        ),
        (
            "model_class",
            "inactive_model_class",
        ),
        (
            "shoe_last",
            "inactive_shoe_last",
        ),
        (
            "construction_method",
            "inactive_construction_method",
        ),
        (
            "material",
            "inactive_material",
        ),
        (
            "usage_role",
            "inactive_usage_role",
        ),
    ],
)
async def test_specification_reports_inactive_entities(
    monkeypatch: pytest.MonkeyPatch,
    target: str,
    expected_code: str,
) -> None:
    graph = make_ready_graph()

    if target == "shoe_model":
        graph.shoe_model.is_active = False
    elif target == "model_class":
        graph.is_active = False
    elif target == "shoe_last":
        graph.shoe_model.shoe_last.is_active = False
    elif target == "construction_method":
        graph.construction_method.is_active = False
    elif target == "material":
        graph.compositions[0].material.is_active = False
    elif target == "usage_role":
        graph.compositions[0].usage_role.is_active = False

    result = await get_result(
        monkeypatch,
        graph,
    )

    assert result.is_production_ready is False
    assert [issue.code for issue in result.validation_issues] == [expected_code]


async def test_specification_reports_missing_consumption_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = make_ready_graph()
    composition = graph.compositions[0]

    composition.consumption_quantity = None
    composition.consumption_unit = None

    result = await get_result(
        monkeypatch,
        graph,
    )

    assert result.is_production_ready is False

    assert [issue.code for issue in result.validation_issues] == [
        "missing_consumption_quantity",
        "missing_consumption_unit",
    ]


async def test_specification_reports_invalid_quantity_and_blank_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = make_ready_graph()
    composition = graph.compositions[0]

    composition.consumption_quantity = Decimal("0")
    composition.consumption_unit = "   "

    result = await get_result(
        monkeypatch,
        graph,
    )

    assert result.is_production_ready is False

    assert [issue.code for issue in result.validation_issues] == [
        "invalid_consumption_quantity",
        "missing_consumption_unit",
    ]


async def test_specification_collects_multiple_validation_issues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = make_ready_graph()
    composition = graph.compositions[0]

    graph.shoe_model.is_active = False
    graph.is_active = False
    graph.shoe_model.shoe_last.is_active = False
    composition.material.is_active = False
    composition.usage_role.is_active = False
    composition.consumption_quantity = None
    composition.consumption_unit = ""

    result = await get_result(
        monkeypatch,
        graph,
    )

    assert result.is_production_ready is False

    assert [issue.code for issue in result.validation_issues] == [
        "inactive_shoe_model",
        "inactive_model_class",
        "inactive_shoe_last",
        "inactive_material",
        "inactive_usage_role",
        "missing_consumption_quantity",
        "missing_consumption_unit",
    ]
