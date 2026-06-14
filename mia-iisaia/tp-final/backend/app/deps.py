from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends
from fastapi_keycloak_middleware import get_user
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models.user import User
from app.services import user as user_service


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def map_user(userinfo: dict[str, Any]) -> dict[str, Any]:
    # Runs on every authenticated request inside the middleware.
    # Keep it minimal: no DB access (no Depends/session available here).
    return userinfo


async def get_current_user(
    claims: dict[str, Any] = Depends(get_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    sub = claims["sub"]
    email = claims.get("email", "")
    display_name = (
        claims.get("name") or claims.get("preferred_username") or email or sub
    )
    return await user_service.get_or_create(db, sub, email, display_name)
