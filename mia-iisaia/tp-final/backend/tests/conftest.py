from unittest import mock

# Disable the Keycloak middleware for all in-process tests. Must run before any
# `from app.main import app`. The real middleware is exercised by the separate
# E2E test (test_auth_e2e.py) against the running Docker stack.
mock.patch("fastapi_keycloak_middleware.setup_keycloak_middleware").start()

import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401, E402 — ensures all tables are registered
from app.core.config import settings  # noqa: E402
from app.db import Base  # noqa: E402


def _async_test_url() -> str:
    url = settings.effective_test_database_url
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine(_async_test_url())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
