# Expense Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let authenticated users create expenses (description, amount, date, group) from a floating (+) button, and view a group's expenses as a list reached via a "Visualizar"-style action on each group card.

**Architecture:** New `expenses` resource nested under `/groups/{group_id}/expenses` on the backend (schema + service + router, mirroring the existing `groups` resource), plus a new `features/expenses` Angular feature (service, a reusable `MatDialog` create form, and a group-expenses list page) wired into the existing Portal page and `GroupCardComponent`.

**Tech Stack:** FastAPI 0.136.3, SQLAlchemy async, pytest/pytest-asyncio, httpx `AsyncClient` — Angular 22 standalone components, signals, `httpResource`, Angular Material (`MatDialog`, `MatList`, `MatFab`), Vitest.

## Global Constraints

- Spec source: `docs/superpowers/specs/2026-06-16-expense-management-design.md`
- An expense always belongs to a group; no group-less expense (spec §1)
- `category_id` and `paid_by` are never exposed in request/response schemas — assigned server-side (spec §2, §3.3)
- Default category = oldest active row in `categories`; created on the fly ("Gastos genéricos") if none exists yet, so the feature works without manually-applied seeds
- `paid_by` is always the current authenticated user — not user-selectable
- Routes nested under groups: `GET/POST /groups/{group_id}/expenses`, same 404 (group not found) / 403 (not a member) checks as `routers/groups.py` (spec §3.2)
- No editing/deleting expenses, no category UI, no "paid by" display, no pagination in this iteration (spec §1)
- Backend: snake_case, `uv` only, routes prefixed via `settings.api_prefix` in `main.py`, Pydantic schemas (never raw ORM) returned from routers
- Frontend: standalone components, `input()`/`output()`, signals for state, `httpResource` for GET data, no `ngClass`/`ngStyle`, Vitest specs colocated per component, manual signal-bound fields (no Reactive/Signal Forms) to match `add-member-form` / `groups-page`'s existing inline-form style
- Run backend tests from `backend/` (`uv run pytest`); frontend tests from `frontend/` (`ng test`)

---

## Task 1: Expense schemas

**Files:**
- Create: `backend/app/schemas/expense.py`
- Test: `backend/tests/test_expense_schemas.py`

**Interfaces:**
- Produces: `ExpenseCreate { description: str | None, amount: Decimal, date: date }`, `ExpenseRead { id: UUID, group_id: UUID, description: str | None, amount: str (serialized), date: date, created_at: datetime }` — both consumed by Task 2 (service) and Task 3 (router)

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_expense_schemas.py
import pytest
from pydantic import ValidationError

from app.schemas.expense import ExpenseCreate


def test_expense_create_accepts_valid_payload():
    body = ExpenseCreate(description="Supermercado", amount="125.50", date="2026-06-10")
    assert body.description == "Supermercado"
    assert str(body.amount) == "125.50"


def test_expense_create_rejects_non_positive_amount():
    with pytest.raises(ValidationError):
        ExpenseCreate(description="Bad", amount="0", date="2026-06-10")


def test_expense_create_allows_null_description():
    body = ExpenseCreate(description=None, amount="10.00", date="2026-06-10")
    assert body.description is None
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `backend/`): `uv run pytest tests/test_expense_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.schemas.expense'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/schemas/expense.py
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_serializer


class ExpenseCreate(BaseModel):
    description: str | None = None
    amount: Decimal = Field(gt=0)
    date: date


class ExpenseRead(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    description: str | None
    amount: Decimal
    date: date
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return str(value)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_expense_schemas.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/expense.py backend/tests/test_expense_schemas.py
git commit -m "feat: add expense request/response schemas"
```

---

## Task 2: Expense service

**Files:**
- Create: `backend/app/services/expense.py`
- Test: `backend/tests/test_expenses.py`

**Interfaces:**
- Consumes: `app.models.expense.Expense`, `app.models.category.Category`, `app.services.user.get_or_create` (test helper only)
- Produces: `create(db, group_id: UUID, paid_by: UUID, description: str | None, amount: Decimal, expense_date: date) -> Expense`, `list_for_group(db, group_id: UUID) -> list[Expense]` — both consumed by Task 3 (router)

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_expenses.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `backend/`): `uv run pytest tests/test_expenses.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.expense'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/expense.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_expenses.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/expense.py backend/tests/test_expenses.py
git commit -m "feat: add expense service with default-category assignment"
```

---

## Task 3: Expense router + app registration

**Files:**
- Create: `backend/app/routers/expenses.py`
- Modify: `backend/app/main.py` (register router)
- Modify: `backend/tests/test_expenses.py` (append router tests)

**Interfaces:**
- Consumes: `expense_service.create`, `expense_service.list_for_group` (Task 2); `group_service.get`, `group_service.is_member` (existing, `app/services/group.py`); `ExpenseCreate`, `ExpenseRead` (Task 1); `get_current_user`, `get_db` (existing, `app/deps.py`)
- Produces: `GET/POST /api/v1/groups/{group_id}/expenses` — consumed by Task 4 (frontend `ExpensesService`)

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_expenses.py`:

```python
# ── Router tests ───────────────────────────────────────────────────────────────

from fastapi_keycloak_middleware import get_user
from httpx import ASGITransport, AsyncClient

from app.deps import get_db
from app.main import app


def _claims(sub: str, email: str, name: str) -> dict:
    return {"sub": sub, "email": email, "name": name}


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
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `backend/`): `uv run pytest tests/test_expenses.py -v`
Expected: FAIL — `404` for all client calls (no route registered at `/api/v1/groups/{id}/expenses`)

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/routers/expenses.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseRead
from app.services import expense as expense_service
from app.services import group as group_service

router = APIRouter(prefix="/groups/{group_id}/expenses", tags=["expenses"])


async def _ensure_member(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    if not await group_service.get(db, group_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    if not await group_service.is_member(db, group_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group"
        )


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    group_id: uuid.UUID,
    body: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_member(db, group_id, current_user.id)
    return await expense_service.create(
        db, group_id, current_user.id, body.description, body.amount, body.date
    )


@router.get("", response_model=list[ExpenseRead])
async def list_expenses(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_member(db, group_id, current_user.id)
    return await expense_service.list_for_group(db, group_id)
```

```python
# backend/app/main.py — add the import and include_router call
from app.routers.expenses import router as expenses_router
# ...
app.include_router(expenses_router, prefix=settings.api_prefix)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_expenses.py -v`
Expected: 9 passed (4 service tests from Task 2 + 5 router tests)

Then run the full suite to confirm no regressions: `uv run pytest -v`

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/expenses.py backend/app/main.py backend/tests/test_expenses.py
git commit -m "feat: add expenses router nested under groups"
```

---

## Task 4: Frontend ExpensesService

**Files:**
- Create: `frontend/src/app/features/expenses/expenses.service.ts`
- Test: `frontend/src/app/features/expenses/expenses.service.spec.ts`

**Interfaces:**
- Produces: `interface Expense { id: string; group_id: string; description: string | null; amount: string; date: string; created_at: string }`, `interface ExpenseCreateBody { description: string | null; amount: string; date: string }`, `class ExpensesService { listExpenses(groupId: string): Observable<Expense[]>; createExpense(groupId: string, body: ExpenseCreateBody): Observable<Expense> }` — consumed by Task 5 (dialog) and Task 6 (list page)

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/app/features/expenses/expenses.service.spec.ts
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';

import { ExpensesService } from './expenses.service';
import { ConfigService } from '../../core/config.service';

describe('ExpensesService', () => {
  let service: ExpensesService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ConfigService,
          useValue: { apiUrl: () => 'http://localhost:8000/api/v1' },
        },
      ],
    });
    service = TestBed.inject(ExpensesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lists expenses for a group', () => {
    service.listExpenses('g-1').subscribe();
    const req = httpMock.expectOne('http://localhost:8000/api/v1/groups/g-1/expenses');
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('creates an expense for a group', () => {
    const body = { description: 'Cena', amount: '45.00', date: '2026-06-10' };
    service.createExpense('g-1', body).subscribe();
    const req = httpMock.expectOne('http://localhost:8000/api/v1/groups/g-1/expenses');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(body);
    req.flush({ id: 'e-1', group_id: 'g-1', created_at: '2026-06-10T00:00:00Z', ...body });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `ng test --watch=false expenses.service.spec.ts`
Expected: FAIL — cannot find module `./expenses.service`

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/src/app/features/expenses/expenses.service.ts
import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ConfigService } from '../../core/config.service';

export interface Expense {
  id: string;
  group_id: string;
  description: string | null;
  amount: string;
  date: string;
  created_at: string;
}

export interface ExpenseCreateBody {
  description: string | null;
  amount: string;
  date: string;
}

@Service()
export class ExpensesService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(ConfigService);

  private base(groupId: string): string {
    return `${this.config.apiUrl()}/groups/${groupId}/expenses`;
  }

  listExpenses(groupId: string): Observable<Expense[]> {
    return this.http.get<Expense[]>(this.base(groupId));
  }

  createExpense(groupId: string, body: ExpenseCreateBody): Observable<Expense> {
    return this.http.post<Expense>(this.base(groupId), body);
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `ng test --watch=false expenses.service.spec.ts`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/features/expenses/expenses.service.ts frontend/src/app/features/expenses/expenses.service.spec.ts
git commit -m "feat: add ExpensesService for group-scoped expense API calls"
```

---

## Task 5: ExpenseFormDialogComponent

**Files:**
- Create: `frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.ts`
- Create: `frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.html`
- Create: `frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.scss`
- Test: `frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.spec.ts`

**Interfaces:**
- Consumes: `ExpensesService.createExpense` (Task 4); `Group`, `GroupsService` from `frontend/src/app/features/groups/groups.service.ts` (existing — only used to type/fetch the group dropdown, not to mutate groups); `MAT_DIALOG_DATA: { preselectedGroupId?: string } | null`
- Produces: `class ExpenseFormDialogComponent` — opened via `MatDialog.open(ExpenseFormDialogComponent, { data })`, closes with `Expense | undefined` — consumed by Task 6 (group expenses page) and Task 8 (portal page)

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.spec.ts
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { ExpenseFormDialogComponent } from './expense-form-dialog';
import { ExpensesService } from '../../expenses.service';
import { ConfigService } from '../../../../core/config.service';

const mockGroups = [
  { id: 'g-1', name: 'Familia', created_by: 'u-1', created_at: '2026-01-01T00:00:00Z', member_count: 2 },
  { id: 'g-2', name: 'Viaje', created_by: 'u-1', created_at: '2026-01-02T00:00:00Z', member_count: 3 },
];

function setup(dialogData: { preselectedGroupId?: string } | null, createResult = of({})) {
  const expensesService = { createExpense: vi.fn(() => createResult) };
  TestBed.configureTestingModule({
    imports: [ExpenseFormDialogComponent],
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      { provide: ExpensesService, useValue: expensesService },
      { provide: ConfigService, useValue: { apiUrl: () => 'http://localhost:8000/api/v1' } },
      { provide: MAT_DIALOG_DATA, useValue: dialogData },
      { provide: MatDialogRef, useValue: { close: vi.fn() } },
    ],
  });
  const fixture = TestBed.createComponent(ExpenseFormDialogComponent);
  return {
    fixture,
    expensesService,
    dialogRef: TestBed.inject(MatDialogRef),
    httpMock: TestBed.inject(HttpTestingController),
  };
}

describe('ExpenseFormDialogComponent', () => {
  it('defaults the date field to today', () => {
    const { fixture, httpMock } = setup(null);
    const today = new Date().toISOString().slice(0, 10);
    expect((fixture.componentInstance as any).date()).toBe(today);
    httpMock.expectOne('http://localhost:8000/api/v1/groups').flush(mockGroups);
  });

  it('preselects the group passed via dialog data once groups load', async () => {
    const { fixture, httpMock } = setup({ preselectedGroupId: 'g-2' });
    fixture.detectChanges();
    httpMock.expectOne('http://localhost:8000/api/v1/groups').flush(mockGroups);
    await fixture.whenStable();
    fixture.detectChanges();
    expect((fixture.componentInstance as any).selectedGroupId()).toBe('g-2');
  });

  it('defaults to the first group when no group is preselected', async () => {
    const { fixture, httpMock } = setup(null);
    fixture.detectChanges();
    httpMock.expectOne('http://localhost:8000/api/v1/groups').flush(mockGroups);
    await fixture.whenStable();
    fixture.detectChanges();
    expect((fixture.componentInstance as any).selectedGroupId()).toBe('g-1');
  });

  it('does not submit when no group is selected', () => {
    const { fixture, expensesService } = setup(null);
    const instance = fixture.componentInstance as any;
    instance.amount.set(10);
    instance.onSubmit();
    expect(expensesService.createExpense).not.toHaveBeenCalled();
  });

  it('submits with the selected group and formatted amount, then closes with the result', () => {
    const created = { id: 'e-1' };
    const { fixture, expensesService, dialogRef } = setup(null, of(created));
    const instance = fixture.componentInstance as any;
    instance.selectedGroupId.set('g-1');
    instance.description.set('Cena');
    instance.amount.set(45);
    instance.date.set('2026-06-10');
    instance.onSubmit();
    expect(expensesService.createExpense).toHaveBeenCalledWith('g-1', {
      description: 'Cena',
      amount: '45.00',
      date: '2026-06-10',
    });
    expect(dialogRef.close).toHaveBeenCalledWith(created);
  });

  it('shows an error message and keeps the dialog open when submission fails', () => {
    const { fixture, dialogRef } = setup(null, throwError(() => new Error('boom')));
    const instance = fixture.componentInstance as any;
    instance.selectedGroupId.set('g-1');
    instance.amount.set(10);
    instance.onSubmit();
    expect(instance.errorMessage()).toContain('No se pudo registrar el gasto');
    expect(dialogRef.close).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `ng test --watch=false expense-form-dialog.spec.ts`
Expected: FAIL — cannot find module `./expense-form-dialog`

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.ts
import { Component, effect, inject, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { ConfigService } from '../../../../core/config.service';
import { Expense, ExpensesService } from '../../expenses.service';
import { Group } from '../../../groups/groups.service';

export interface ExpenseFormDialogData {
  preselectedGroupId?: string;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

@Component({
  selector: 'app-expense-form-dialog',
  imports: [
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
  ],
  templateUrl: './expense-form-dialog.html',
  styleUrl: './expense-form-dialog.scss',
})
export class ExpenseFormDialogComponent {
  private readonly config = inject(ConfigService);
  private readonly expensesService = inject(ExpensesService);
  private readonly dialogRef = inject(MatDialogRef<ExpenseFormDialogComponent, Expense | undefined>);
  private readonly data = inject<ExpenseFormDialogData | null>(MAT_DIALOG_DATA, { optional: true });

  protected readonly groups = httpResource<Group[]>(() => `${this.config.apiUrl()}/groups`);

  protected readonly description = signal('');
  protected readonly amount = signal<number | null>(null);
  protected readonly date = signal(todayIsoDate());
  protected readonly selectedGroupId = signal<string | null>(null);
  protected readonly isSubmitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  constructor() {
    effect(() => {
      const groups = this.groups.value();
      if (!groups || groups.length === 0 || this.selectedGroupId()) return;
      const preselected = this.data?.preselectedGroupId;
      const match = preselected && groups.some((g) => g.id === preselected);
      this.selectedGroupId.set(match ? (preselected as string) : groups[0].id);
    });
  }

  protected onSubmit(): void {
    const groupId = this.selectedGroupId();
    const amountValue = this.amount();
    const dateValue = this.date();
    if (!groupId || amountValue === null || amountValue <= 0 || !dateValue) return;

    this.isSubmitting.set(true);
    this.errorMessage.set(null);
    this.expensesService
      .createExpense(groupId, {
        description: this.description().trim() || null,
        amount: amountValue.toFixed(2),
        date: dateValue,
      })
      .subscribe({
        next: (expense) => {
          this.isSubmitting.set(false);
          this.dialogRef.close(expense);
        },
        error: () => {
          this.isSubmitting.set(false);
          this.errorMessage.set('No se pudo registrar el gasto. Intentá nuevamente.');
        },
      });
  }

  protected onCancel(): void {
    this.dialogRef.close(undefined);
  }
}
```

```html
<!-- frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.html -->
<h2 mat-dialog-title>Nuevo gasto</h2>

<mat-dialog-content class="form-content">
  <mat-form-field appearance="outline">
    <mat-label>Descripción</mat-label>
    <input
      matInput
      [value]="description()"
      (input)="description.set($any($event.target).value)"
    />
  </mat-form-field>

  <mat-form-field appearance="outline">
    <mat-label>Monto</mat-label>
    <input
      matInput
      type="number"
      step="0.01"
      min="0.01"
      [value]="amount()"
      (input)="amount.set($any($event.target).valueAsNumber)"
    />
  </mat-form-field>

  <mat-form-field appearance="outline">
    <mat-label>Fecha</mat-label>
    <input matInput type="date" [value]="date()" (input)="date.set($any($event.target).value)" />
  </mat-form-field>

  <mat-form-field appearance="outline">
    <mat-label>Grupo</mat-label>
    <mat-select
      [value]="selectedGroupId()"
      (selectionChange)="selectedGroupId.set($event.value)"
      aria-label="Grupo del gasto"
    >
      @for (group of groups.value() ?? []; track group.id) {
        <mat-option [value]="group.id">{{ group.name }}</mat-option>
      }
    </mat-select>
  </mat-form-field>

  @if (errorMessage()) {
    <p role="alert">{{ errorMessage() }}</p>
  }
</mat-dialog-content>

<mat-dialog-actions align="end">
  <button mat-button (click)="onCancel()">Cancelar</button>
  <button
    mat-flat-button
    color="primary"
    (click)="onSubmit()"
    [disabled]="isSubmitting() || !selectedGroupId() || !amount()"
  >
    Guardar
  </button>
</mat-dialog-actions>
```

```scss
// frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.scss
.form-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 320px;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `ng test --watch=false expense-form-dialog.spec.ts`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/features/expenses/components/expense-form-dialog/
git commit -m "feat: add ExpenseFormDialogComponent for creating expenses"
```

---

## Task 6: GroupExpensesPage + route

**Files:**
- Create: `frontend/src/app/features/expenses/pages/group-expenses-page/group-expenses-page.ts`
- Create: `frontend/src/app/features/expenses/pages/group-expenses-page/group-expenses-page.html`
- Create: `frontend/src/app/features/expenses/pages/group-expenses-page/group-expenses-page.scss`
- Test: `frontend/src/app/features/expenses/pages/group-expenses-page/group-expenses-page.spec.ts`
- Modify: `frontend/src/app/features/groups/groups.routes.ts`

**Interfaces:**
- Consumes: `ExpensesService.listExpenses` (Task 4), `ExpenseFormDialogComponent` (Task 5)
- Produces: route `/groups/:id/expenses` — consumed by Task 7 (group card link)

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/app/features/expenses/pages/group-expenses-page/group-expenses-page.spec.ts
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';
import { convertToParamMap } from '@angular/router';
import { vi } from 'vitest';

import { GroupExpensesPage } from './group-expenses-page';
import { ConfigService } from '../../../../core/config.service';

describe('GroupExpensesPage', () => {
  function setup(dialogResult: unknown = undefined) {
    const dialog = { open: vi.fn(() => ({ afterClosed: () => of(dialogResult) })) };
    TestBed.configureTestingModule({
      imports: [GroupExpensesPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        { provide: MatDialog, useValue: dialog },
        {
          provide: ActivatedRoute,
          useValue: { paramMap: of(convertToParamMap({ id: 'g-1' })) },
        },
        { provide: ConfigService, useValue: { apiUrl: () => 'http://localhost:8000/api/v1' } },
        { provide: OidcSecurityService, useValue: { authenticated: signal({ isAuthenticated: true }) } },
      ],
    });
    const fixture = TestBed.createComponent(GroupExpensesPage);
    return { fixture, dialog };
  }

  it('should create', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows page heading', () => {
    const { fixture } = setup();
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('h1')?.textContent).toContain(
      'Gastos del grupo',
    );
  });

  it('opens the expense dialog with the current group preselected', () => {
    const { fixture, dialog } = setup();
    fixture.detectChanges();
    (fixture.componentInstance as any).openAddExpenseDialog();
    expect(dialog.open).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ data: { preselectedGroupId: 'g-1' } }),
    );
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `ng test --watch=false group-expenses-page.spec.ts`
Expected: FAIL — cannot find module `./group-expenses-page`

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/src/app/features/expenses/pages/group-expenses-page/group-expenses-page.ts
import { Component, computed, inject } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from '../../../../core/config.service';
import { Expense } from '../../expenses.service';
import { ExpenseFormDialogComponent } from '../../components/expense-form-dialog/expense-form-dialog';

@Component({
  selector: 'app-group-expenses-page',
  imports: [MatButtonModule, MatIconModule, MatListModule, MatProgressSpinnerModule],
  templateUrl: './group-expenses-page.html',
  styleUrl: './group-expenses-page.scss',
})
export class GroupExpensesPage {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);
  private readonly dialog = inject(MatDialog);

  protected readonly groupId = toSignal(this.route.paramMap.pipe(map((p) => p.get('id') ?? '')), {
    initialValue: '',
  });

  private readonly isAuthenticated = computed(() => this.oidc.authenticated().isAuthenticated);

  protected readonly expenses = httpResource<Expense[]>(() =>
    this.isAuthenticated() && this.groupId()
      ? `${this.config.apiUrl()}/groups/${this.groupId()}/expenses`
      : undefined,
  );

  protected goBack(): void {
    this.router.navigate(['/groups']);
  }

  protected openAddExpenseDialog(): void {
    const ref = this.dialog.open(ExpenseFormDialogComponent, {
      data: { preselectedGroupId: this.groupId() },
    });
    ref.afterClosed().subscribe((result: unknown) => {
      if (result) this.expenses.reload();
    });
  }
}
```

```html
<!-- frontend/src/app/features/expenses/pages/group-expenses-page/group-expenses-page.html -->
<div class="expenses-container">
  <div class="expenses-header">
    <button mat-icon-button (click)="goBack()" aria-label="Volver a grupos">
      <mat-icon>arrow_back</mat-icon>
    </button>
    <h1>Gastos del grupo</h1>
  </div>

  @if (expenses.isLoading()) {
    <div class="loading">
      <mat-spinner diameter="48" aria-label="Cargando gastos…" />
    </div>
  } @else if (expenses.error()) {
    <p role="alert">No se pudieron cargar los gastos.</p>
  } @else {
    <mat-list>
      @for (expense of expenses.value() ?? []; track expense.id) {
        <mat-list-item>
          <span matListItemTitle>{{ expense.description || 'Sin descripción' }}</span>
          <span matListItemLine>{{ expense.date }} — ${{ expense.amount }}</span>
        </mat-list-item>
      } @empty {
        <p>Este grupo no tiene gastos todavía.</p>
      }
    </mat-list>
  }

  <button mat-fab color="primary" class="add-expense-fab" (click)="openAddExpenseDialog()" aria-label="Agregar gasto">
    <mat-icon>add</mat-icon>
  </button>
</div>
```

```scss
// frontend/src/app/features/expenses/pages/group-expenses-page/group-expenses-page.scss
.expenses-container {
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
}

.expenses-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;

  h1 {
    margin: 0;
  }
}

.loading {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}

.add-expense-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
}
```

```typescript
// frontend/src/app/features/groups/groups.routes.ts — add a third route entry
{
  path: ':id/expenses',
  title: 'Gastos del Grupo',
  loadComponent: () =>
    import('../expenses/pages/group-expenses-page/group-expenses-page').then(
      (m) => m.GroupExpensesPage,
    ),
},
```

- [ ] **Step 4: Run test to verify it passes**

Run: `ng test --watch=false group-expenses-page.spec.ts`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/features/expenses/pages/group-expenses-page/ frontend/src/app/features/groups/groups.routes.ts
git commit -m "feat: add GroupExpensesPage and /groups/:id/expenses route"
```

---

## Task 7: "Ver gastos" action on GroupCardComponent

**Files:**
- Modify: `frontend/src/app/features/groups/components/group-card/group-card.ts`
- Modify: `frontend/src/app/features/groups/components/group-card/group-card.html`
- Modify: `frontend/src/app/features/groups/components/group-card/group-card.spec.ts`

**Interfaces:**
- Consumes: `Router` (existing, already injected in this component)
- Produces: clicking the "Ver gastos" button navigates to `/groups/:id/expenses` — no new exported interface (other tasks don't depend on this)

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/app/features/groups/components/group-card/group-card.spec.ts` (inside the existing `describe` block):

```typescript
  it('navigates to the group expenses page when "Ver gastos" is clicked', () => {
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    const fixture = TestBed.createComponent(GroupCardComponent);
    fixture.componentRef.setInput('group', mockGroup);
    fixture.detectChanges();

    const expensesBtn = (fixture.nativeElement as HTMLElement).querySelector(
      'button[aria-label="Ver gastos"]',
    ) as HTMLButtonElement;
    expensesBtn.click();

    expect(navigateSpy).toHaveBeenCalledWith(['/groups', 'g-1', 'expenses']);
  });
```

Add the `Router` import at the top of the spec file:

```typescript
import { Router } from '@angular/router';
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `ng test --watch=false group-card.spec.ts`
Expected: FAIL — no element matches `button[aria-label="Ver gastos"]`

- [ ] **Step 3: Write minimal implementation**

In `group-card.html`, add a new button next to "Ver miembros" (inside `mat-card-actions`):

```html
<button mat-icon-button (click)="goToExpenses()" aria-label="Ver gastos">
  <mat-icon>receipt_long</mat-icon>
</button>
```

In `group-card.ts`, add the method next to `goToDetail()`:

```typescript
  protected goToExpenses(): void {
    this.router.navigate(['/groups', this.group().id, 'expenses']);
  }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `ng test --watch=false group-card.spec.ts`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/features/groups/components/group-card/
git commit -m "feat: add 'Ver gastos' action to group card"
```

---

## Task 8: Floating add-expense button on the Portal page

**Files:**
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.html`
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.scss`
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts`

**Interfaces:**
- Consumes: `ExpenseFormDialogComponent` (Task 5)

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts`:

```typescript
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';
import { vi } from 'vitest';
```

Add inside the `describe('PortalPage', ...)` block, alongside a `dialog` mock wired into the `TestBed` providers:

```typescript
  it('opens the expense dialog when the floating add button is clicked', () => {
    const dialog = { open: vi.fn(() => ({ afterClosed: () => of(undefined) })) };
    TestBed.overrideProvider(MatDialog, { useValue: dialog });

    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();

    const fab = (fixture.nativeElement as HTMLElement).querySelector(
      'button[aria-label="Agregar gasto"]',
    ) as HTMLButtonElement;
    fab.click();

    expect(dialog.open).toHaveBeenCalled();
  });
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `ng test --watch=false portal-page.spec.ts`
Expected: FAIL — no element matches `button[aria-label="Agregar gasto"]`

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/src/app/features/portal/pages/portal-page/portal-page.ts
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

import { ExpenseFormDialogComponent } from '../../../expenses/components/expense-form-dialog/expense-form-dialog';

@Component({
  selector: 'app-portal-page',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatIconModule],
  templateUrl: './portal-page.html',
  styleUrl: './portal-page.scss',
})
export class PortalPage {
  private readonly dialog = inject(MatDialog);

  protected openAddExpenseDialog(): void {
    this.dialog.open(ExpenseFormDialogComponent);
  }
}
```

```html
<!-- frontend/src/app/features/portal/pages/portal-page/portal-page.html -->
<main class="portal-container">
  <mat-card class="feature-card">
    <mat-card-header>
      <mat-icon mat-card-avatar>group</mat-icon>
      <mat-card-title>Mis Grupos</mat-card-title>
      <mat-card-subtitle> Gestiona tus grupos de gastos compartidos </mat-card-subtitle>
    </mat-card-header>
    <mat-card-actions>
      <a mat-flat-button color="primary" routerLink="/groups"> Ir a grupos </a>
    </mat-card-actions>
  </mat-card>

  <button
    mat-fab
    color="primary"
    class="add-expense-fab"
    (click)="openAddExpenseDialog()"
    aria-label="Agregar gasto"
  >
    <mat-icon>add</mat-icon>
  </button>
</main>
```

```scss
// frontend/src/app/features/portal/pages/portal-page/portal-page.scss
.portal-container {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 24px;
  max-width: 960px;
  margin: 0 auto;
}

.feature-card {
  min-width: 260px;
  flex: 1;
}

.add-expense-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `ng test --watch=false portal-page.spec.ts`
Expected: 3 passed

Then run the full frontend suite to confirm no regressions: `ng test --watch=false`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/features/portal/pages/portal-page/
git commit -m "feat: add floating add-expense button to the portal page"
```

---

## Task 9: README documentation

**Files:**
- Modify: `README.md`

**Interfaces:** None (documentation only)

- [ ] **Step 1: Update the Group Management endpoints table**

In `README.md`, under `### Group Management (`/groups`, `/groups/:id`)`, the existing endpoints table is unchanged — expenses get their own section below it (next step), since they're a distinct resource reached via the group card's new "Ver gastos" action.

- [ ] **Step 2: Add the Expense Management section**

Insert a new section immediately after the `### Group Management` section (after its endpoints table, before the next `---`) in `README.md`:

```markdown
### Expense Management (`/groups/:id/expenses`)

Allows authenticated users to record and view shared expenses within a group. An expense always belongs to a group.

**Entry points:**
- Floating (+) button on the Portal page — opens the create-expense dialog with the first group preselected
- "Ver gastos" action on each `GroupCardComponent` — navigates to that group's expense list
- Floating (+) button on the expense list itself — opens the same dialog with the current group preselected

**Pages:**
- `GroupExpensesPage` — lists a group's expenses (description, amount, date), ordered by date descending

**Components:**
- `ExpenseFormDialogComponent` — `MatDialog` form: descripción, monto, fecha (default: today), grupo (`mat-select`, defaults to the preselected group or the first group)

**Service:** `ExpensesService` — list and create methods, scoped per group

**API endpoints used:**

| Method | Path | Description |
|--------|------|--------------|
| GET | `/api/v1/groups/:id/expenses` | List expenses for a group, ordered by date descending |
| POST | `/api/v1/groups/:id/expenses` | Create an expense in a group (`paid_by` = current user; category assigned automatically) |
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document the expense management feature"
```
