from httpx import AsyncClient


def make_model_payload(
    shoe_last_id: int,
    *,
    model_code: str = "TEST_SHOE_MODEL_API",
) -> dict:
    return {
        "shoe_last_id": shoe_last_id,
        "model_code": model_code,
        "model_name": "Test Shoe Model API",
        "footwear_category": "test",
        "footwear_type": "integration",
        "target_group": "test",
        "description": "Created by integration test",
        "is_active": True,
    }


async def test_shoe_model_create_get_and_partial_update(
    client: AsyncClient,
    active_shoe_last: dict,
) -> None:
    payload = make_model_payload(active_shoe_last["shoe_last_id"])

    create_response = await client.post(
        "/api/v1/models",
        json=payload,
    )

    assert create_response.status_code == 201

    created = create_response.json()
    model_id = created["shoe_model_id"]

    assert created["model_code"] == payload["model_code"]
    assert created["model_name"] == payload["model_name"]
    assert created["shoe_last_id"] == active_shoe_last["shoe_last_id"]

    get_response = await client.get(f"/api/v1/models/{model_id}")

    assert get_response.status_code == 200

    persisted = get_response.json()

    assert persisted["shoe_model_id"] == model_id
    assert persisted["model_code"] == payload["model_code"]

    patch_response = await client.patch(
        f"/api/v1/models/{model_id}",
        json={
            "model_name": "Updated Integration Model",
            "description": "Updated description",
        },
    )

    assert patch_response.status_code == 200

    updated = patch_response.json()

    assert updated["model_name"] == "Updated Integration Model"
    assert updated["description"] == "Updated description"

    assert updated["model_code"] == payload["model_code"]
    assert updated["shoe_last_id"] == payload["shoe_last_id"]
    assert updated["footwear_category"] == payload["footwear_category"]
    assert updated["target_group"] == payload["target_group"]

    final_response = await client.get(f"/api/v1/models/{model_id}")

    assert final_response.status_code == 200

    final_model = final_response.json()

    assert final_model["model_name"] == "Updated Integration Model"
    assert final_model["description"] == "Updated description"


async def test_shoe_model_duplicate_returns_centralized_409(
    client: AsyncClient,
    active_shoe_last: dict,
) -> None:
    payload = make_model_payload(
        active_shoe_last["shoe_last_id"],
        model_code="TEST_DUPLICATE_MODEL",
    )

    first_response = await client.post(
        "/api/v1/models",
        json=payload,
    )

    assert first_response.status_code == 201

    duplicate_response = await client.post(
        "/api/v1/models",
        json=payload,
    )

    assert duplicate_response.status_code == 409

    body = duplicate_response.json()

    assert body["error"]["code"] == "conflict"
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["message"]


async def test_shoe_model_missing_shoe_last_returns_centralized_404(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/models",
        json=make_model_payload(
            999999,
            model_code="TEST_MISSING_LAST",
        ),
    )

    assert response.status_code == 404

    body = response.json()

    assert body["error"]["code"] == "entity_not_found"
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["message"]


async def test_shoe_model_invalid_body_uses_fastapi_422(
    client: AsyncClient,
    active_shoe_last: dict,
) -> None:
    response = await client.post(
        "/api/v1/models",
        json={
            "shoe_last_id": active_shoe_last["shoe_last_id"],
            "model_code": "TEST_INVALID_MODEL",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert body["detail"]
    assert "error" not in body
