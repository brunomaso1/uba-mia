import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — ensures all tables are registered
from app.core.config import settings
from app.db import Base


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
