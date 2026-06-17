import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi_keycloak_middleware import get_user
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.main import app
from app.services import expense as expense_service
from app.services import group as group_service
from app.services import user as user_service


async def _make_user(db: AsyncSession, sub: str, email: str, name: str):
    return await user_service.get_or_create(db, sub, email, name)


def _claims(sub: str, email: str, name: str) -> dict:
    return {"sub": sub, "email": email, "name": name}


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


# ── Router tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_expense_creates_and_returns(db: AsyncSession):
    alice = await _make_user(db, "sub-rt-ex-1", "rtex1@test.com", "RT Ex One")
    group = await group_service.create(db, "Viaje", alice.id)

    async def override_user():
        return _claims("sub-rt-ex-1", "rtex1@test.com", "RT Ex One")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/v1/groups/{group.id}/expenses",
            json={"description": "Cena", "amount": "45.00", "date": "2026-06-10"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Cena"
    assert data["amount"] == "45.00"
    assert data["date"] == "2026-06-10"
    assert data["group_id"] == str(group.id)


@pytest.mark.asyncio
async def test_post_expense_group_not_found_returns_404(db: AsyncSession):
    await _make_user(db, "sub-rt-ex-2", "rtex2@test.com", "RT Ex Two")

    async def override_user():
        return _claims("sub-rt-ex-2", "rtex2@test.com", "RT Ex Two")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/v1/groups/{uuid.uuid4()}/expenses",
            json={"description": "Cena", "amount": "45.00", "date": "2026-06-10"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_expense_by_non_member_returns_403(db: AsyncSession):
    alice = await _make_user(db, "sub-rt-ex-3", "rtex3@test.com", "Alice")
    group = await group_service.create(db, "Viaje", alice.id)

    async def override_user():
        return _claims("sub-rt-ex-4", "rtex4@test.com", "Bob Non-Member")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/v1/groups/{group.id}/expenses",
            json={"description": "Cena", "amount": "45.00", "date": "2026-06-10"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_expenses_returns_list_ordered_desc(db: AsyncSession):
    alice = await _make_user(db, "sub-rt-ex-5", "rtex5@test.com", "Alice")
    group = await group_service.create(db, "Viaje", alice.id)

    async def override_user():
        return _claims("sub-rt-ex-5", "rtex5@test.com", "Alice")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            f"/api/v1/groups/{group.id}/expenses",
            json={"description": "Older", "amount": "10.00", "date": "2026-06-01"},
        )
        await client.post(
            f"/api/v1/groups/{group.id}/expenses",
            json={"description": "Newer", "amount": "20.00", "date": "2026-06-05"},
        )
        response = await client.get(f"/api/v1/groups/{group.id}/expenses")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    descriptions = [e["description"] for e in response.json()]
    assert descriptions == ["Newer", "Older"]


@pytest.mark.asyncio
async def test_get_expenses_by_non_member_returns_403(db: AsyncSession):
    alice = await _make_user(db, "sub-rt-ex-6", "rtex6@test.com", "Alice")
    group = await group_service.create(db, "Viaje", alice.id)

    async def override_user():
        return _claims("sub-rt-ex-7", "rtex7@test.com", "Bob Non-Member")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/v1/groups/{group.id}/expenses")
    app.dependency_overrides.clear()
    assert response.status_code == 403
