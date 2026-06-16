import pytest
from fastapi_keycloak_middleware import get_user
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.main import app
from app.models.user import User
from app.services import user as user_service

# --- Service tests ---


@pytest.mark.asyncio
async def test_get_or_create_creates_user(db: AsyncSession):
    user = await user_service.get_or_create(
        db, keycloak_sub="kc-sub-1", email="alice@example.com", display_name="Alice"
    )
    assert user.id is not None
    assert user.keycloak_sub == "kc-sub-1"
    assert user.email == "alice@example.com"
    assert user.display_name == "Alice"


@pytest.mark.asyncio
async def test_get_or_create_is_idempotent(db: AsyncSession):
    first = await user_service.get_or_create(
        db, keycloak_sub="kc-sub-2", email="bob@example.com", display_name="Bob"
    )
    second = await user_service.get_or_create(
        db, keycloak_sub="kc-sub-2", email="bob@example.com", display_name="Bob"
    )
    assert first.id == second.id


# --- Router tests (auth mocked via get_user override) ---


@pytest.mark.asyncio
async def test_users_me_creates_and_returns_user(db: AsyncSession):
    claims = {
        "sub": "kc-sub-me",
        "email": "alice@example.com",
        "name": "Alice Test",
    }

    async def override_user():
        return claims

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users/me")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["keycloak_sub"] == "kc-sub-me"
    assert data["email"] == "alice@example.com"
    assert data["display_name"] == "Alice Test"

    # The user was persisted.
    result = await db.execute(select(User).where(User.keycloak_sub == "kc-sub-me"))
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_list_users_returns_all(db: AsyncSession):
    from app.services import user as user_service

    await user_service.get_or_create(db, "sub-lu-1", "u1@lu.com", "User One")
    await user_service.get_or_create(db, "sub-lu-2", "u2@lu.com", "User Two")

    claims = {"sub": "sub-lu-req", "email": "req@lu.com", "name": "Requester"}

    async def override_user():
        return claims

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    emails = [u["email"] for u in data]
    assert "u1@lu.com" in emails
    assert "u2@lu.com" in emails
    for u in data:
        assert "id" in u
        assert "display_name" in u
        assert "email" in u
        assert "keycloak_sub" not in u  # UserPublic hides internal fields
