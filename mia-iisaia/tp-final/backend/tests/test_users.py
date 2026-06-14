import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
