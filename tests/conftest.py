from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.api.dependencies import get_db_session
from app.core.config import settings
from app.main import app

if settings.test_database_url is None:
    raise RuntimeError("TEST_DATABASE_URL is required to run the test suite")

development_url = make_url(settings.database_url)
test_url = make_url(settings.test_database_url)

if development_url == test_url:
    raise RuntimeError("TEST_DATABASE_URL must not point to the development database")

if development_url.database == test_url.database:
    raise RuntimeError("Test and development database names must be different")


test_engine = create_async_engine(
    settings.test_database_url,
    poolclass=NullPool,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncIterator[AsyncClient]:
    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as http_client:
            yield http_client
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def active_shoe_last(
    client: AsyncClient,
) -> dict:
    response = await client.get("/api/v1/shoe-lasts")
    assert response.status_code == 200

    return next(shoe_last for shoe_last in response.json() if shoe_last["is_active"])


@pytest_asyncio.fixture
async def active_construction_method(
    client: AsyncClient,
) -> dict:
    response = await client.get("/api/v1/construction-methods")
    assert response.status_code == 200

    return next(method for method in response.json() if method["is_active"])


@pytest_asyncio.fixture
async def active_material(
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

    materials = response.json()
    assert materials

    return materials[0]


@pytest_asyncio.fixture
async def active_usage_role(
    client: AsyncClient,
) -> dict:
    response = await client.get("/api/v1/material-usage-roles")
    assert response.status_code == 200

    return next(role for role in response.json() if role["is_active"])


@pytest_asyncio.fixture
async def test_shoe_model(
    client: AsyncClient,
    active_shoe_last: dict,
) -> dict:
    response = await client.post(
        "/api/v1/models",
        json={
            "shoe_last_id": active_shoe_last["shoe_last_id"],
            "model_code": "TEST_INTEGRATION_MODEL",
            "model_name": "Integration Test Model",
            "footwear_category": "test",
            "footwear_type": "test",
            "target_group": "test",
            "description": "Integration test Shoe Model",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    return response.json()


@pytest_asyncio.fixture
async def test_model_class(
    client: AsyncClient,
    test_shoe_model: dict,
    active_construction_method: dict,
) -> dict:
    response = await client.post(
        (f"/api/v1/models/{test_shoe_model['shoe_model_id']}/classes"),
        json={
            "class_code": "TEST_INTEGRATION_CLASS",
            "class_name": "Integration Test Class",
            "construction_method_id": (
                active_construction_method["construction_method_id"]
            ),
            "quality_level": "test",
            "warranty_months": 12,
            "description": "Integration test Model Class",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    return response.json()
