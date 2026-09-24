from httpx import AsyncClient


def make_class_payload(
    construction_method_id: int,
    *,
    class_code: str = "TEST_MODEL_CLASS_API",
) -> dict:
    return {
        "class_code": class_code,
        "class_name": "Test Model Class API",
        "construction_method_id": construction_method_id,
        "quality_level": "standard",
        "warranty_months": 12,
        "description": "Created by integration test",
        "is_active": True,
    }


async def test_model_class_create_get_and_partial_update(
    client: AsyncClient,
    test_shoe_model: dict,
    active_construction_method: dict,
) -> None:
    payload = make_class_payload(
        active_construction_method[
            "construction_method_id"
        ]
    )

    create_response = await client.post(
        (
            f"/api/v1/models/"
            f"{test_shoe_model['shoe_model_id']}/classes"
        ),
        json=payload,
    )

    assert create_response.status_code == 201

    created = create_response.json()
    class_id = created["shoe_model_class_id"]

    assert created["class_code"] == payload["class_code"]
    assert created["class_name"] == payload["class_name"]
    assert (
        created["shoe_model_id"]
        == test_shoe_model["shoe_model_id"]
    )
    assert (
        created["construction_method_id"]
        == payload["construction_method_id"]
    )

    get_response = await client.get(
        f"/api/v1/model-classes/{class_id}"
    )

    assert get_response.status_code == 200

    persisted = get_response.json()

    assert (
        persisted["shoe_model_class_id"]
        == class_id
    )
    assert (
        persisted["class_code"]
        == payload["class_code"]
    )

    patch_response = await client.patch(
        f"/api/v1/model-classes/{class_id}",
        json={
            "quality_level": "premium",
            "warranty_months": 24,
        },
    )

    assert patch_response.status_code == 200

    updated = patch_response.json()

    assert updated["quality_level"] == "premium"
    assert updated["warranty_months"] == 24

    assert updated["class_code"] == payload["class_code"]
    assert updated["class_name"] == payload["class_name"]
    assert (
        updated["construction_method_id"]
        == payload["construction_method_id"]
    )
    assert (
        updated["shoe_model_id"]
        == test_shoe_model["shoe_model_id"]
    )

    final_response = await client.get(
        f"/api/v1/model-classes/{class_id}"
    )

    assert final_response.status_code == 200

    final_class = final_response.json()

    assert final_class["quality_level"] == "premium"
    assert final_class["warranty_months"] == 24


async def test_model_class_duplicate_code_returns_409(
    client: AsyncClient,
    test_shoe_model: dict,
    active_construction_method: dict,
) -> None:
    payload = make_class_payload(
        active_construction_method[
            "construction_method_id"
        ],
        class_code="TEST_DUPLICATE_CLASS",
    )

    path = (
        f"/api/v1/models/"
        f"{test_shoe_model['shoe_model_id']}/classes"
    )

    first_response = await client.post(
        path,
        json=payload,
    )

    assert first_response.status_code == 201

    duplicate_response = await client.post(
        path,
        json=payload,
    )

    assert duplicate_response.status_code == 409

    body = duplicate_response.json()

    assert body["error"]["code"] == "conflict"
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["message"]


async def test_model_class_missing_parent_model_returns_404(
    client: AsyncClient,
    active_construction_method: dict,
) -> None:
    response = await client.post(
        "/api/v1/models/999999/classes",
        json=make_class_payload(
            active_construction_method[
                "construction_method_id"
            ],
            class_code="TEST_MISSING_PARENT",
        ),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["code"] == "entity_not_found"
    assert body["error"]["message"]


async def test_model_class_missing_construction_method_returns_404(
    client: AsyncClient,
    test_shoe_model: dict,
) -> None:
    response = await client.post(
        (
            f"/api/v1/models/"
            f"{test_shoe_model['shoe_model_id']}/classes"
        ),
        json=make_class_payload(
            999999,
            class_code="TEST_MISSING_METHOD",
        ),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["code"] == "entity_not_found"
    assert body["error"]["message"]


async def test_model_class_patch_forbidden_field_returns_422(
    client: AsyncClient,
    test_model_class: dict,
) -> None:
    response = await client.patch(
        (
            f"/api/v1/model-classes/"
            f"{test_model_class['shoe_model_class_id']}"
        ),
        json={
            "class_name": "Forbidden Change",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert "error" not in body
