from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import ShoeModelClassMaterial


def make_composition_payload(
    material_id: int,
    usage_role_id: int,
) -> dict:
    return {
        "material_id": material_id,
        "material_usage_role_id": usage_role_id,
        "consumption_quantity": "1.500",
        "consumption_unit": "pair",
        "is_required": True,
        "description": "Integration composition",
    }


async def test_production_composition_full_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    test_shoe_model: dict,
    test_model_class: dict,
    active_construction_method: dict,
    active_material: dict,
    active_usage_role: dict,
) -> None:
    class_id = test_model_class["shoe_model_class_id"]
    material_id = active_material["material_id"]
    usage_role_id = active_usage_role[
        "material_usage_role_id"
    ]

    path = (
        f"/api/v1/model-classes/"
        f"{class_id}/materials"
    )

    initial_response = await client.get(path)

    assert initial_response.status_code == 200
    assert initial_response.json() == []

    material_before_response = await client.get(
        f"/api/v1/materials/{material_id}"
    )

    assert material_before_response.status_code == 200

    material_before = material_before_response.json()

    payload = make_composition_payload(
        material_id,
        usage_role_id,
    )

    create_response = await client.post(
        path,
        json=payload,
    )

    assert create_response.status_code == 201

    created = create_response.json()
    composition_id = created[
        "shoe_model_class_material_id"
    ]

    assert created["shoe_model_class_id"] == class_id
    assert created["material_id"] == material_id
    assert (
        created["material_usage_role_id"]
        == usage_role_id
    )
    assert created["is_active"] is True
    assert (
        Decimal(str(created["consumption_quantity"]))
        == Decimal("1.500")
    )

    duplicate_response = await client.post(
        path,
        json=payload,
    )

    assert duplicate_response.status_code == 409

    duplicate_body = duplicate_response.json()

    assert duplicate_body["error"]["code"] == "conflict"
    assert duplicate_body["error"]["message"]

    patch_response = await client.patch(
        (
            f"{path}/"
            f"{composition_id}"
        ),
        json={
            "consumption_quantity": "2.750",
            "description": "Patched composition",
        },
    )

    assert patch_response.status_code == 200

    patched = patch_response.json()

    assert (
        patched["shoe_model_class_material_id"]
        == composition_id
    )
    assert patched["shoe_model_class_id"] == class_id
    assert patched["material_id"] == material_id
    assert (
        patched["material_usage_role_id"]
        == usage_role_id
    )
    assert (
        Decimal(str(patched["consumption_quantity"]))
        == Decimal("2.750")
    )
    assert (
        patched["description"]
        == "Patched composition"
    )

    other_class_response = await client.post(
        (
            f"/api/v1/models/"
            f"{test_shoe_model['shoe_model_id']}/classes"
        ),
        json={
            "class_code": "TEST_OTHER_COMPOSITION_CLASS",
            "class_name": "Other Composition Class",
            "construction_method_id": (
                active_construction_method[
                    "construction_method_id"
                ]
            ),
            "quality_level": "test",
            "warranty_months": 12,
            "description": "Ownership test class",
            "is_active": True,
        },
    )

    assert other_class_response.status_code == 201

    other_class_id = other_class_response.json()[
        "shoe_model_class_id"
    ]

    ownership_response = await client.patch(
        (
            f"/api/v1/model-classes/"
            f"{other_class_id}/materials/"
            f"{composition_id}"
        ),
        json={
            "description": "Must not be applied",
        },
    )

    assert ownership_response.status_code == 404

    original_list_response = await client.get(path)

    assert original_list_response.status_code == 200

    original_rows = original_list_response.json()

    original_row = next(
        row
        for row in original_rows
        if row["shoe_model_class_material_id"]
        == composition_id
    )

    assert (
        original_row["description"]
        == "Patched composition"
    )

    delete_response = await client.delete(
        f"{path}/{composition_id}"
    )

    assert delete_response.status_code == 204

    hidden_response = await client.get(path)

    assert hidden_response.status_code == 200

    assert all(
        row["shoe_model_class_material_id"]
        != composition_id
        for row in hidden_response.json()
    )

    row_result = await db_session.execute(
        select(ShoeModelClassMaterial).where(
            ShoeModelClassMaterial
            .shoe_model_class_material_id
            == composition_id
        )
    )

    deactivated_row = row_result.scalar_one()

    assert deactivated_row.is_active is False

    material_after_response = await client.get(
        f"/api/v1/materials/{material_id}"
    )

    assert material_after_response.status_code == 200

    material_after = material_after_response.json()

    assert material_after == material_before

    reactivate_response = await client.post(
        path,
        json={
            "material_id": material_id,
            "material_usage_role_id": usage_role_id,
            "consumption_quantity": "3.250",
            "consumption_unit": "meter",
            "is_required": False,
            "description": "Reactivated composition",
        },
    )

    assert reactivate_response.status_code == 201

    reactivated = reactivate_response.json()

    assert (
        reactivated["shoe_model_class_material_id"]
        == composition_id
    )
    assert reactivated["is_active"] is True
    assert (
        Decimal(
            str(reactivated["consumption_quantity"])
        )
        == Decimal("3.250")
    )
    assert reactivated["consumption_unit"] == "meter"
    assert reactivated["is_required"] is False
    assert (
        reactivated["description"]
        == "Reactivated composition"
    )

    count_result = await db_session.execute(
        select(func.count())
        .select_from(ShoeModelClassMaterial)
        .where(
            ShoeModelClassMaterial
            .shoe_model_class_id
            == class_id,
            ShoeModelClassMaterial.material_id
            == material_id,
            ShoeModelClassMaterial
            .material_usage_role_id
            == usage_role_id,
        )
    )

    assert count_result.scalar_one() == 1

    final_response = await client.get(path)

    assert final_response.status_code == 200

    final_rows = final_response.json()

    assert sum(
        row["shoe_model_class_material_id"]
        == composition_id
        for row in final_rows
    ) == 1


async def test_composition_patch_forbidden_field_returns_422(
    client: AsyncClient,
    test_model_class: dict,
    active_material: dict,
    active_usage_role: dict,
) -> None:
    class_id = test_model_class["shoe_model_class_id"]

    path = (
        f"/api/v1/model-classes/"
        f"{class_id}/materials"
    )

    create_response = await client.post(
        path,
        json=make_composition_payload(
            active_material["material_id"],
            active_usage_role[
                "material_usage_role_id"
            ],
        ),
    )

    assert create_response.status_code == 201

    composition_id = create_response.json()[
        "shoe_model_class_material_id"
    ]

    response = await client.patch(
        f"{path}/{composition_id}",
        json={
            "material_id": 999999,
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert "error" not in body


async def test_composition_missing_material_returns_404(
    client: AsyncClient,
    test_model_class: dict,
    active_usage_role: dict,
) -> None:
    class_id = test_model_class["shoe_model_class_id"]

    response = await client.post(
        (
            f"/api/v1/model-classes/"
            f"{class_id}/materials"
        ),
        json=make_composition_payload(
            999999,
            active_usage_role[
                "material_usage_role_id"
            ],
        ),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["code"] == "entity_not_found"
    assert body["error"]["message"]


async def test_composition_missing_usage_role_returns_404(
    client: AsyncClient,
    test_model_class: dict,
    active_material: dict,
) -> None:
    class_id = test_model_class["shoe_model_class_id"]

    response = await client.post(
        (
            f"/api/v1/model-classes/"
            f"{class_id}/materials"
        ),
        json=make_composition_payload(
            active_material["material_id"],
            999999,
        ),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["code"] == "entity_not_found"
    assert body["error"]["message"]


async def test_composition_non_positive_quantity_returns_422(
    client: AsyncClient,
    test_model_class: dict,
    active_material: dict,
    active_usage_role: dict,
) -> None:
    class_id = test_model_class["shoe_model_class_id"]

    payload = make_composition_payload(
        active_material["material_id"],
        active_usage_role[
            "material_usage_role_id"
        ],
    )
    payload["consumption_quantity"] = 0

    response = await client.post(
        (
            f"/api/v1/model-classes/"
            f"{class_id}/materials"
        ),
        json=payload,
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert "error" not in body
