import pytest
from httpx import AsyncClient


async def test_shoe_last_read_api(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/shoe-lasts")

    assert response.status_code == 200

    shoe_lasts = response.json()

    assert isinstance(shoe_lasts, list)
    assert shoe_lasts

    existing = shoe_lasts[0]
    shoe_last_id = existing["shoe_last_id"]

    detail_response = await client.get(
        f"/api/v1/shoe-lasts/{shoe_last_id}"
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["shoe_last_id"] == shoe_last_id
    assert isinstance(detail["sizes"], list)
    assert detail["sizes"]

    missing_response = await client.get(
        "/api/v1/shoe-lasts/999999"
    )

    assert missing_response.status_code == 404


async def test_shoe_last_filter(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/shoe-lasts")

    assert response.status_code == 200

    shoe_lasts = response.json()
    assert shoe_lasts

    size_system = shoe_lasts[0]["size_system"]

    filtered_response = await client.get(
        "/api/v1/shoe-lasts",
        params={"size_system": size_system},
    )

    assert filtered_response.status_code == 200

    filtered = filtered_response.json()

    assert filtered
    assert all(
        shoe_last["size_system"] == size_system
        for shoe_last in filtered
    )


async def test_shoe_model_read_api_and_pagination(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/models",
        params={
            "limit": 1,
            "offset": 0,
        },
    )

    assert response.status_code == 200

    first_page = response.json()

    assert len(first_page) == 1

    second_response = await client.get(
        "/api/v1/models",
        params={
            "limit": 1,
            "offset": 1,
        },
    )

    assert second_response.status_code == 200

    second_page = second_response.json()

    assert len(second_page) == 1

    assert (
        first_page[0]["shoe_model_id"]
        != second_page[0]["shoe_model_id"]
    )

    shoe_model_id = first_page[0]["shoe_model_id"]

    detail_response = await client.get(
        f"/api/v1/models/{shoe_model_id}"
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["shoe_model_id"] == shoe_model_id
    assert "shoe_last" in detail

    classes_response = await client.get(
        f"/api/v1/models/{shoe_model_id}/classes"
    )

    assert classes_response.status_code == 200
    assert isinstance(classes_response.json(), list)

    missing_response = await client.get(
        "/api/v1/models/999999"
    )

    assert missing_response.status_code == 404


async def test_shoe_model_filter(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/models",
        params={"limit": 100},
    )

    assert response.status_code == 200

    models = response.json()
    assert models

    footwear_category = models[0]["footwear_category"]

    filtered_response = await client.get(
        "/api/v1/models",
        params={
            "footwear_category": footwear_category,
            "limit": 100,
        },
    )

    assert filtered_response.status_code == 200

    filtered = filtered_response.json()

    assert filtered
    assert all(
        model["footwear_category"] == footwear_category
        for model in filtered
    )


async def test_material_read_api_and_pagination(
    client: AsyncClient,
) -> None:
    first_response = await client.get(
        "/api/v1/materials",
        params={
            "limit": 1,
            "offset": 0,
        },
    )

    assert first_response.status_code == 200

    first_page = first_response.json()
    assert len(first_page) == 1

    second_response = await client.get(
        "/api/v1/materials",
        params={
            "limit": 1,
            "offset": 1,
        },
    )

    assert second_response.status_code == 200

    second_page = second_response.json()
    assert len(second_page) == 1

    assert (
        first_page[0]["material_id"]
        != second_page[0]["material_id"]
    )


async def test_material_search_and_detail_graph(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/materials",
        params={"limit": 100},
    )

    assert response.status_code == 200

    materials = response.json()
    assert materials

    selected_material = None
    selected_detail = None

    for material in materials:
        detail_response = await client.get(
            f"/api/v1/materials/{material['material_id']}"
        )

        assert detail_response.status_code == 200

        detail = detail_response.json()

        if detail["attribute_values"]:
            selected_material = material
            selected_detail = detail
            break

    assert selected_material is not None
    assert selected_detail is not None

    assert "category" in selected_detail
    assert selected_detail["category"]["material_category_id"] > 0

    attribute_values = selected_detail["attribute_values"]

    assert attribute_values
    assert "attribute" in attribute_values[0]

    attribute = attribute_values[0]["attribute"]

    assert attribute["material_attribute_id"] > 0
    assert attribute["material_attribute_code"]

    search_response = await client.get(
        "/api/v1/materials",
        params={
            "search": selected_material["material_code"],
            "limit": 100,
        },
    )

    assert search_response.status_code == 200

    search_results = search_response.json()

    assert any(
        material["material_id"]
        == selected_material["material_id"]
        for material in search_results
    )


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/construction-methods",
        "/api/v1/material-categories",
        "/api/v1/material-usage-roles",
    ],
)
async def test_reference_data_endpoints(
    client: AsyncClient,
    path: str,
) -> None:
    response = await client.get(path)

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert data
