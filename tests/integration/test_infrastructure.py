from httpx import AsyncClient

TEST_MODEL_CODE = "TEST_TASK20_ISOLATION_MODEL"


async def test_shoe_lasts_smoke(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/shoe-lasts")

    assert response.status_code == 200

    shoe_lasts = response.json()

    assert isinstance(shoe_lasts, list)
    assert len(shoe_lasts) > 0
    assert shoe_lasts[0]["shoe_last_id"] > 0


async def test_01_committed_change_exists_inside_test(
    client: AsyncClient,
) -> None:
    shoe_lasts_response = await client.get("/api/v1/shoe-lasts")
    assert shoe_lasts_response.status_code == 200

    shoe_last = shoe_lasts_response.json()[0]

    response = await client.post(
        "/api/v1/models",
        json={
            "shoe_last_id": shoe_last["shoe_last_id"],
            "model_code": TEST_MODEL_CODE,
            "model_name": "Task 20 Isolation Model",
            "footwear_category": "test",
            "footwear_type": "test",
            "target_group": "test",
            "description": "Temporary integration-test entity",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    created_model = response.json()

    assert created_model["model_code"] == TEST_MODEL_CODE

    read_response = await client.get(f"/api/v1/models/{created_model['shoe_model_id']}")

    assert read_response.status_code == 200
    assert read_response.json()["model_code"] == TEST_MODEL_CODE


async def test_02_committed_change_was_rolled_back(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/models")

    assert response.status_code == 200

    models = response.json()

    assert all(model["model_code"] != TEST_MODEL_CODE for model in models)
