import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.expense import Expense


async def _get_or_create_default_category_id(db: AsyncSession) -> uuid.UUID:
    result = await db.execute(
        select(Category.id)
        .where(Category.is_active == True)  # noqa: E712
        .order_by(Category.created_at.asc())
        .limit(1)
    )
    category_id = result.scalar_one_or_none()
    if category_id is not None:
        return category_id

    category = Category(
        name="Gastos genéricos",
        description="Categoría por defecto para expenses sin clasificar",
    )
    db.add(category)
    await db.flush()
    return category.id


async def create(
    db: AsyncSession,
    group_id: uuid.UUID,
    paid_by: uuid.UUID,
    description: str | None,
    amount: Decimal,
    expense_date: date,
) -> Expense:
    category_id = await _get_or_create_default_category_id(db)
    expense = Expense(
        group_id=group_id,
        paid_by=paid_by,
        category_id=category_id,
        amount=amount,
        description=description,
        date=expense_date,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


async def list_for_group(db: AsyncSession, group_id: uuid.UUID) -> list[Expense]:
    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id)
        .order_by(Expense.date.desc())
    )
    return list(result.scalars().all())
