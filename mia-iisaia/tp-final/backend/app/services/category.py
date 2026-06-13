import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


async def list_active(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).where(Category.is_active == True))  # noqa: E712
    return list(result.scalars().all())


async def create(db: AsyncSession, name: str, description: str | None) -> Category:
    category = Category(name=name, description=description)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def deactivate(db: AsyncSession, category_id: uuid.UUID) -> Category | None:
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        return None
    category.is_active = False
    await db.commit()
    await db.refresh(category)
    return category
