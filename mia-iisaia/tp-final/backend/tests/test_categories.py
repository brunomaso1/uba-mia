import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.main import app
from app.services import category as category_service

# --- Service tests ---


@pytest.mark.asyncio
async def test_create_category(db: AsyncSession):
    cat = await category_service.create(db, "Transporte", "Gastos de transporte")
    assert cat.id is not None
    assert cat.name == "Transporte"
    assert cat.description == "Gastos de transporte"
    assert cat.is_active is True


@pytest.mark.asyncio
async def test_list_active_categories(db: AsyncSession):
    await category_service.create(db, "Comida", None)
    await category_service.create(db, "Deporte", None)
    cats = await category_service.list_active(db)
    assert len(cats) == 2
    assert all(c.is_active for c in cats)


@pytest.mark.asyncio
async def test_deactivate_category(db: AsyncSession):
    cat = await category_service.create(db, "Hogar", None)
    deactivated = await category_service.deactivate(db, cat.id)
    assert deactivated is not None
    assert deactivated.is_active is False
    active = await category_service.list_active(db)
    assert all(c.id != cat.id for c in active)


@pytest.mark.asyncio
async def test_deactivate_nonexistent(db: AsyncSession):
    result = await category_service.deactivate(db, uuid.uuid4())
    assert result is None


# --- Router tests ---


@pytest.mark.asyncio
async def test_get_categories_empty(db: AsyncSession):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/categories")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_post_category(db: AsyncSession):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/categories", json={"name": "Ocio", "description": None}
        )
    app.dependency_overrides.clear()
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ocio"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_delete_category_soft_deletes(db: AsyncSession):
    cat = await category_service.create(db, "Temporal", None)

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(f"/api/v1/categories/{cat.id}")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_category_not_found(db: AsyncSession):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(f"/api/v1/categories/{uuid.uuid4()}")
    app.dependency_overrides.clear()
    assert response.status_code == 404
