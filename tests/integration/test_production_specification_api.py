from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import ShoeModelClassMaterial
from app.models.shoe_model import ShoeModelClass


async def get_active_material_with_attributes(
    client: AsyncClient,
) -> dict:
    response = await client.get(
        "/api/v1/materials",
        params={
            "limit": 100,
            "is_active": True,
        },
    )

    assert response.status_code == 200

    for material in response.json():
        detail_response = await client.get(
            f"/api/v1/materials/{material['material_id']}"
        )

        assert detail_response.status_code == 200

        detail = detail_response.json()

        if detail["attribute_values"]:
            return detail

    raise AssertionError(
        "Test seed must contain an active Material with attributes"
    )


async def create_composition(
    client: AsyncClient,
    *,
    class_id: int,
    material_id: int,
    usage_role_id: int,
    quantity: str = "1.500",
    unit: str | None = "pair",
    description: str = "Specification test composition",
) -> dict:
    response = await client.post(
        (
            f"/api/v1/model-classes/"
            f"{class_id}/materials"
        ),
        json={
            "material_id": material_id,
            "material_usage_role_id": usage_role_id,
            "consumption_quantity": quantity,
            "consumption_unit": unit,
            "is_required": True,
            "description": description,
        },
    )

    assert response.status_code == 201

    return response.json()


async def get_second_active_material(
    client: AsyncClient,
    excluded_material_id: int,
) -> dict:
    response = await client.get(
        "/api/v1/materials",
        params={
            "limit": 100,
            "is_active": True,
        },
    )

    assert response.status_code == 200

    return next(
        material
        for material in response.json()
        if material["material_id"] != excluded_material_id
    )


async def test_production_specification_missing_class_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/model-classes/999999/specification"
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["code"] == "entity_not_found"
    assert body["error"]["message"]


async def test_production_specification_ready_graph_is_aggregated_and_read_only(
    client: AsyncClient,
    db_session: AsyncSession,
    test_model_class: dict,
    active_usage_role: dict,
) -> None:
    class_id = test_model_class[
        "shoe_model_class_id"
    ]

    material = await get_active_material_with_attributes(
        client
    )

    active_row = await create_composition(
        client,
        class_id=class_id,
        material_id=material["material_id"],
        usage_role_id=active_usage_role[
            "material_usage_role_id"
        ],
        quantity="1.750",
        unit="pair",
        description="Ready specification composition",
    )

    second_material = await get_second_active_material(
        client,
        material["material_id"],
    )

    inactive_row = await create_composition(
        client,
        class_id=class_id,
        material_id=second_material["material_id"],
        usage_role_id=active_usage_role[
            "material_usage_role_id"
        ],
        quantity="0.500",
        unit="meter",
        description="Inactive specification composition",
    )

    delete_response = await client.delete(
        (
            f"/api/v1/model-classes/{class_id}/materials/"
            f"{inactive_row['shoe_model_class_material_id']}"
        )
    )

    assert delete_response.status_code == 204

    class_result = await db_session.execute(
        select(ShoeModelClass).where(
            ShoeModelClass.shoe_model_class_id
            == class_id
        )
    )
    model_class = class_result.scalar_one()

    composition_result = await db_session.execute(
        select(ShoeModelClassMaterial).where(
            ShoeModelClassMaterial
            .shoe_model_class_material_id
            == active_row["shoe_model_class_material_id"]
        )
    )
    composition = composition_result.scalar_one()

    class_snapshot = (
        model_class.construction_method_id,
        model_class.quality_level,
        model_class.warranty_months,
        model_class.description,
        model_class.is_active,
    )

    composition_snapshot = (
        composition.material_id,
        composition.material_usage_role_id,
        composition.consumption_quantity,
        composition.consumption_unit,
        composition.is_required,
        composition.description,
        composition.is_active,
    )

    response = await client.get(
        (
            f"/api/v1/model-classes/"
            f"{class_id}/specification"
        )
    )

    assert response.status_code == 200

    specification = response.json()

    assert specification["is_production_ready"] is True
    assert specification["validation_issues"] == []

    assert specification["shoe_model"]
    assert specification["shoe_model"]["shoe_last"]
    assert specification["model_class"]
    assert specification["construction_method"]

    assert (
        specification["model_class"][
            "shoe_model_class_id"
        ]
        == class_id
    )

    rows = specification["composition"]

    assert len(rows) == 1
    assert (
        rows[0]["shoe_model_class_material_id"]
        == active_row["shoe_model_class_material_id"]
    )

    assert rows[0]["material"]
    assert rows[0]["material"]["category"]
    assert rows[0]["usage_role"]

    assert (
        Decimal(str(rows[0]["consumption_quantity"]))
        == Decimal("1.750")
    )
    assert rows[0]["consumption_unit"] == "pair"

    assert (
        inactive_row["shoe_model_class_material_id"]
        not in {
            row["shoe_model_class_material_id"]
            for row in rows
        }
    )

    assert "production_standard" not in specification

    attribute_values = rows[0]["material"][
        "attribute_values"
    ]

    assert attribute_values

    first_attribute_value = attribute_values[0]

    assert "value_text" in first_attribute_value
    assert "value_numeric" in first_attribute_value
    assert "value_boolean" in first_attribute_value
    assert first_attribute_value["attribute"]
    assert (
        first_attribute_value["attribute"][
            "material_attribute_id"
        ]
        > 0
    )
    assert first_attribute_value["attribute"][
        "material_attribute_code"
    ]

    await db_session.refresh(model_class)
    await db_session.refresh(composition)

    assert (
        (
            model_class.construction_method_id,
            model_class.quality_level,
            model_class.warranty_months,
            model_class.description,
            model_class.is_active,
        )
        == class_snapshot
    )

    assert (
        (
            composition.material_id,
            composition.material_usage_role_id,
            composition.consumption_quantity,
            composition.consumption_unit,
            composition.is_required,
            composition.description,
            composition.is_active,
        )
        == composition_snapshot
    )

    inactive_result = await db_session.execute(
        select(ShoeModelClassMaterial).where(
            ShoeModelClassMaterial
            .shoe_model_class_material_id
            == inactive_row[
                "shoe_model_class_material_id"
            ]
        )
    )

    inactive_composition = inactive_result.scalar_one()

    assert inactive_composition.is_active is False


async def test_production_specification_not_ready_returns_200(
    client: AsyncClient,
    test_model_class: dict,
    active_material: dict,
    active_usage_role: dict,
) -> None:
    class_id = test_model_class[
        "shoe_model_class_id"
    ]

    composition = await create_composition(
        client,
        class_id=class_id,
        material_id=active_material["material_id"],
        usage_role_id=active_usage_role[
            "material_usage_role_id"
        ],
    )

    patch_response = await client.patch(
        (
            f"/api/v1/model-classes/{class_id}/materials/"
            f"{composition['shoe_model_class_material_id']}"
        ),
        json={
            "consumption_unit": None,
        },
    )

    assert patch_response.status_code == 200

    response = await client.get(
        (
            f"/api/v1/model-classes/"
            f"{class_id}/specification"
        )
    )

    assert response.status_code == 200

    specification = response.json()

    assert specification["is_production_ready"] is False

    issue_codes = {
        issue["code"]
        for issue in specification["validation_issues"]
    }

    assert "missing_consumption_unit" in issue_codes


async def test_production_specification_without_active_composition(
    client: AsyncClient,
    test_model_class: dict,
) -> None:
    class_id = test_model_class[
        "shoe_model_class_id"
    ]

    response = await client.get(
        (
            f"/api/v1/model-classes/"
            f"{class_id}/specification"
        )
    )

    assert response.status_code == 200

    specification = response.json()

    assert specification["is_production_ready"] is False
    assert specification["composition"] == []

    issue_codes = {
        issue["code"]
        for issue in specification["validation_issues"]
    }

    assert "no_active_composition" in issue_codes


async def test_production_specification_collects_multiple_issues(
    client: AsyncClient,
    test_model_class: dict,
    active_material: dict,
    active_usage_role: dict,
) -> None:
    class_id = test_model_class[
        "shoe_model_class_id"
    ]

    composition = await create_composition(
        client,
        class_id=class_id,
        material_id=active_material["material_id"],
        usage_role_id=active_usage_role[
            "material_usage_role_id"
        ],
    )

    composition_patch_response = await client.patch(
        (
            f"/api/v1/model-classes/{class_id}/materials/"
            f"{composition['shoe_model_class_material_id']}"
        ),
        json={
            "consumption_unit": None,
        },
    )

    assert composition_patch_response.status_code == 200

    class_patch_response = await client.patch(
        f"/api/v1/model-classes/{class_id}",
        json={
            "is_active": False,
        },
    )

    assert class_patch_response.status_code == 200

    response = await client.get(
        (
            f"/api/v1/model-classes/"
            f"{class_id}/specification"
        )
    )

    assert response.status_code == 200

    specification = response.json()

    assert specification["is_production_ready"] is False

    issue_codes = {
        issue["code"]
        for issue in specification["validation_issues"]
    }

    assert {
        "inactive_model_class",
        "missing_consumption_unit",
    }.issubset(issue_codes)
