from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.model_class as model_class_service
from app.models.material import ShoeModelClassMaterial
from app.models.shoe_model import ShoeModelClass
from app.repositories.production_composition import (
    create_composition as real_create_composition,
)
from app.schemas.shoe_model import ShoeModelClassClone


async def get_active_combinations(
    client: AsyncClient,
    count: int = 3,
) -> list[tuple[dict, dict]]:
    materials_response = await client.get(
        "/api/v1/materials",
        params={
            "limit": 100,
            "is_active": True,
        },
    )
    assert materials_response.status_code == 200

    roles_response = await client.get(
        "/api/v1/material-usage-roles"
    )
    assert roles_response.status_code == 200

    materials = materials_response.json()
    roles = [
        role
        for role in roles_response.json()
        if role["is_active"]
    ]

    combinations = [
        (material, role)
        for material in materials
        for role in roles
    ]

    assert len(combinations) >= count

    return combinations[:count]


async def prepare_source_compositions(
    client: AsyncClient,
    source_class_id: int,
) -> tuple[list[dict], dict]:
    combinations = await get_active_combinations(
        client,
        count=3,
    )

    path = (
        f"/api/v1/model-classes/"
        f"{source_class_id}/materials"
    )

    payloads = [
        {
            "material_id": combinations[0][0]["material_id"],
            "material_usage_role_id": combinations[0][1][
                "material_usage_role_id"
            ],
            "consumption_quantity": "1.250",
            "consumption_unit": "pair",
            "is_required": True,
            "description": "Clone active source one",
        },
        {
            "material_id": combinations[1][0]["material_id"],
            "material_usage_role_id": combinations[1][1][
                "material_usage_role_id"
            ],
            "consumption_quantity": "0.750",
            "consumption_unit": "meter",
            "is_required": False,
            "description": "Clone active source two",
        },
        {
            "material_id": combinations[2][0]["material_id"],
            "material_usage_role_id": combinations[2][1][
                "material_usage_role_id"
            ],
            "consumption_quantity": "2.000",
            "consumption_unit": "sheet",
            "is_required": True,
            "description": "Clone inactive source",
        },
    ]

    created_rows = []

    for payload in payloads:
        response = await client.post(
            path,
            json=payload,
        )

        assert response.status_code == 201
        created_rows.append(response.json())

    inactive_row = created_rows[2]

    delete_response = await client.delete(
        (
            f"{path}/"
            f"{inactive_row['shoe_model_class_material_id']}"
        )
    )

    assert delete_response.status_code == 204

    return created_rows[:2], inactive_row


def composition_business_map(
    rows: list[dict],
) -> dict[tuple[int, int], dict]:
    return {
        (
            row["material_id"],
            row["material_usage_role_id"],
        ): {
            "consumption_quantity": Decimal(
                str(row["consumption_quantity"])
            ),
            "consumption_unit": row["consumption_unit"],
            "is_required": row["is_required"],
            "description": row["description"],
        }
        for row in rows
    }


async def test_model_class_clone_copies_only_active_compositions(
    client: AsyncClient,
    db_session: AsyncSession,
    test_model_class: dict,
) -> None:
    source_id = test_model_class[
        "shoe_model_class_id"
    ]

    active_rows, inactive_row = (
        await prepare_source_compositions(
            client,
            source_id,
        )
    )

    source_class_before_response = await client.get(
        f"/api/v1/model-classes/{source_id}"
    )
    assert source_class_before_response.status_code == 200
    source_class_before = (
        source_class_before_response.json()
    )

    source_active_before_response = await client.get(
        (
            f"/api/v1/model-classes/"
            f"{source_id}/materials"
        )
    )
    assert source_active_before_response.status_code == 200
    source_active_before = (
        source_active_before_response.json()
    )

    assert len(source_active_before) == 2

    inactive_id = inactive_row[
        "shoe_model_class_material_id"
    ]

    inactive_result = await db_session.execute(
        select(ShoeModelClassMaterial).where(
            ShoeModelClassMaterial
            .shoe_model_class_material_id
            == inactive_id
        )
    )
    inactive_before = inactive_result.scalar_one()

    assert inactive_before.is_active is False

    inactive_snapshot = (
        inactive_before.material_id,
        inactive_before.material_usage_role_id,
        inactive_before.consumption_quantity,
        inactive_before.consumption_unit,
        inactive_before.is_required,
        inactive_before.description,
        inactive_before.is_active,
    )

    material_ids = {
        row["material_id"]
        for row in active_rows + [inactive_row]
    }

    materials_before = {}

    for material_id in material_ids:
        response = await client.get(
            f"/api/v1/materials/{material_id}"
        )
        assert response.status_code == 200
        materials_before[material_id] = response.json()

    clone_response = await client.post(
        f"/api/v1/model-classes/{source_id}/clone",
        json={
            "class_code": "TEST_CLONE_SUCCESS",
            "class_name": "Successful Test Clone",
        },
    )

    assert clone_response.status_code == 201

    clone = clone_response.json()
    clone_id = clone["shoe_model_class_id"]

    assert clone_id != source_id
    assert (
        clone["shoe_model_id"]
        == source_class_before["shoe_model_id"]
    )
    assert clone["class_code"] == "TEST_CLONE_SUCCESS"
    assert (
        clone["class_name"]
        == "Successful Test Clone"
    )
    assert (
        clone["construction_method_id"]
        == source_class_before["construction_method_id"]
    )
    assert (
        clone["quality_level"]
        == source_class_before["quality_level"]
    )
    assert (
        clone["warranty_months"]
        == source_class_before["warranty_months"]
    )
    assert (
        clone["description"]
        == source_class_before["description"]
    )
    assert (
        clone["is_active"]
        == source_class_before["is_active"]
    )

    clone_compositions_response = await client.get(
        (
            f"/api/v1/model-classes/"
            f"{clone_id}/materials"
        )
    )

    assert clone_compositions_response.status_code == 200

    clone_rows = clone_compositions_response.json()

    assert len(clone_rows) == len(source_active_before)
    assert len(clone_rows) == 2

    assert (
        composition_business_map(clone_rows)
        == composition_business_map(source_active_before)
    )

    assert all(
        row["is_active"] is True
        for row in clone_rows
    )

    inactive_combination = (
        inactive_row["material_id"],
        inactive_row["material_usage_role_id"],
    )

    clone_combinations = {
        (
            row["material_id"],
            row["material_usage_role_id"],
        )
        for row in clone_rows
    }

    assert inactive_combination not in clone_combinations

    source_class_after_response = await client.get(
        f"/api/v1/model-classes/{source_id}"
    )
    assert source_class_after_response.status_code == 200

    assert (
        source_class_after_response.json()
        == source_class_before
    )

    source_active_after_response = await client.get(
        (
            f"/api/v1/model-classes/"
            f"{source_id}/materials"
        )
    )
    assert source_active_after_response.status_code == 200

    assert (
        source_active_after_response.json()
        == source_active_before
    )

    await db_session.refresh(inactive_before)

    inactive_after_snapshot = (
        inactive_before.material_id,
        inactive_before.material_usage_role_id,
        inactive_before.consumption_quantity,
        inactive_before.consumption_unit,
        inactive_before.is_required,
        inactive_before.description,
        inactive_before.is_active,
    )

    assert inactive_after_snapshot == inactive_snapshot

    for material_id, material_before in (
        materials_before.items()
    ):
        response = await client.get(
            f"/api/v1/materials/{material_id}"
        )
        assert response.status_code == 200
        assert response.json() == material_before


async def test_model_class_clone_missing_source_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/model-classes/999999/clone",
        json={
            "class_code": "TEST_MISSING_CLONE",
            "class_name": "Missing Clone",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["code"] == "entity_not_found"
    assert body["error"]["message"]


async def test_model_class_clone_duplicate_code_returns_409(
    client: AsyncClient,
    test_model_class: dict,
) -> None:
    source_id = test_model_class[
        "shoe_model_class_id"
    ]

    response = await client.post(
        f"/api/v1/model-classes/{source_id}/clone",
        json={
            "class_code": test_model_class["class_code"],
            "class_name": "Duplicate Clone",
        },
    )

    assert response.status_code == 409

    body = response.json()

    assert body["error"]["code"] == "conflict"
    assert body["error"]["message"]


async def test_model_class_clone_validation_returns_422(
    client: AsyncClient,
    test_model_class: dict,
) -> None:
    source_id = test_model_class[
        "shoe_model_class_id"
    ]

    missing_field_response = await client.post(
        f"/api/v1/model-classes/{source_id}/clone",
        json={
            "class_code": "TEST_MISSING_FIELD",
        },
    )

    assert missing_field_response.status_code == 422
    assert "detail" in missing_field_response.json()

    extra_field_response = await client.post(
        f"/api/v1/model-classes/{source_id}/clone",
        json={
            "class_code": "TEST_EXTRA_FIELD",
            "class_name": "Extra Field Clone",
            "shoe_model_id": 999999,
        },
    )

    assert extra_field_response.status_code == 422
    assert "detail" in extra_field_response.json()


async def test_model_class_clone_rolls_back_partial_database_work(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    test_model_class: dict,
) -> None:
    source_id = test_model_class[
        "shoe_model_class_id"
    ]

    await prepare_source_compositions(
        client,
        source_id,
    )

    source_before_response = await client.get(
        f"/api/v1/model-classes/{source_id}"
    )
    assert source_before_response.status_code == 200
    source_before = source_before_response.json()

    compositions_before_response = await client.get(
        (
            f"/api/v1/model-classes/"
            f"{source_id}/materials"
        )
    )
    assert compositions_before_response.status_code == 200
    compositions_before = (
        compositions_before_response.json()
    )

    assert len(compositions_before) == 2

    clone_class_id: int | None = None
    composition_calls = 0

    async def controlled_create_composition(
        session: AsyncSession,
        *,
        shoe_model_class_id: int,
        data: dict,
    ):
        nonlocal clone_class_id
        nonlocal composition_calls

        clone_class_id = shoe_model_class_id
        composition_calls += 1

        if composition_calls == 2:
            raise RuntimeError(
                "forced clone composition failure"
            )

        return await real_create_composition(
            session,
            shoe_model_class_id=shoe_model_class_id,
            data=data,
        )

    monkeypatch.setattr(
        model_class_service,
        "repository_create_composition",
        controlled_create_composition,
    )

    with pytest.raises(
        RuntimeError,
        match="forced clone composition failure",
    ):
        await model_class_service.clone_model_class(
            db_session,
            source_id,
            ShoeModelClassClone(
                class_code="TEST_CLONE_ROLLBACK",
                class_name="Rollback Test Clone",
            ),
        )

    assert composition_calls == 2
    assert clone_class_id is not None

    clone_by_id_result = await db_session.execute(
        select(ShoeModelClass).where(
            ShoeModelClass.shoe_model_class_id
            == clone_class_id
        )
    )

    assert clone_by_id_result.scalar_one_or_none() is None

    clone_by_code_result = await db_session.execute(
        select(ShoeModelClass).where(
            ShoeModelClass.class_code
            == "TEST_CLONE_ROLLBACK"
        )
    )

    assert clone_by_code_result.scalar_one_or_none() is None

    partial_count_result = await db_session.execute(
        select(func.count())
        .select_from(ShoeModelClassMaterial)
        .where(
            ShoeModelClassMaterial.shoe_model_class_id
            == clone_class_id
        )
    )

    assert partial_count_result.scalar_one() == 0

    source_after_response = await client.get(
        f"/api/v1/model-classes/{source_id}"
    )
    assert source_after_response.status_code == 200

    assert source_after_response.json() == source_before

    compositions_after_response = await client.get(
        (
            f"/api/v1/model-classes/"
            f"{source_id}/materials"
        )
    )
    assert compositions_after_response.status_code == 200

    assert (
        compositions_after_response.json()
        == compositions_before
    )
