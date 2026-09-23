from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)

from app.api.dependencies import get_db_session
from app.core.config import settings
from app.main import app
from sqlalchemy.pool import NullPool


if settings.test_database_url is None:
    raise RuntimeError(
        "TEST_DATABASE_URL is required to run the test suite"
    )

development_url = make_url(settings.database_url)
test_url = make_url(settings.test_database_url)

if development_url == test_url:
    raise RuntimeError(
        "TEST_DATABASE_URL must not point to the development database"
    )

if development_url.database == test_url.database:
    raise RuntimeError(
        "Test and development database names must be different"
    )


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

    app.dependency_overrides[get_db_session] = (
        override_get_db_session
    )

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as http_client:
            yield http_client
    finally:
        app.dependency_overrides.clear()
