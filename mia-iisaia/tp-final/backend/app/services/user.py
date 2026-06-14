from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_or_create(
    db: AsyncSession, keycloak_sub: str, email: str, display_name: str
) -> User:
    result = await db.execute(select(User).where(User.keycloak_sub == keycloak_sub))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(keycloak_sub=keycloak_sub, email=email, display_name=display_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
