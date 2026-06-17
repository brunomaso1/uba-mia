import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import expense as expense_service
from app.services import group as group_service
from app.services import user as user_service


async def _make_user(db: AsyncSession, sub: str, email: str, name: str):
    return await user_service.get_or_create(db, sub, email, name)


# ── Service tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_assigns_default_category_when_none_exists(db: AsyncSession):
    alice = await _make_user(db, "sub-ex-1", "alice@ex1.com", "Alice")
    group = await group_service.create(db, "Viaje", alice.id)
    expense = await expense_service.create(
        db,
        group.id,
        alice.id,
        "Supermercado",
        Decimal("125.50"),
        date(2026, 6, 10),
    )
    assert expense.id is not None
    assert expense.group_id == group.id
    assert expense.paid_by == alice.id
    assert expense.category_id is not None
    assert expense.amount == Decimal("125.50")
    assert expense.description == "Supermercado"
    assert expense.date == date(2026, 6, 10)


@pytest.mark.asyncio
async def test_create_reuses_existing_default_category(db: AsyncSession):
    alice = await _make_user(db, "sub-ex-2", "alice@ex2.com", "Alice")
    group = await group_service.create(db, "Viaje", alice.id)
    first = await expense_service.create(
        db, group.id, alice.id, "A", Decimal("10.00"), date(2026, 6, 1)
    )
    second = await expense_service.create(
        db, group.id, alice.id, "B", Decimal("20.00"), date(2026, 6, 2)
    )
    assert first.category_id == second.category_id


@pytest.mark.asyncio
async def test_list_for_group_orders_by_date_desc(db: AsyncSession):
    alice = await _make_user(db, "sub-ex-3", "alice@ex3.com", "Alice")
    group = await group_service.create(db, "Viaje", alice.id)
    await expense_service.create(
        db, group.id, alice.id, "Older", Decimal("10.00"), date(2026, 6, 1)
    )
    await expense_service.create(
        db, group.id, alice.id, "Newer", Decimal("20.00"), date(2026, 6, 5)
    )
    expenses = await expense_service.list_for_group(db, group.id)
    assert [e.description for e in expenses] == ["Newer", "Older"]


@pytest.mark.asyncio
async def test_list_for_group_empty_for_unknown_group(db: AsyncSession):
    expenses = await expense_service.list_for_group(db, uuid.uuid4())
    assert expenses == []
