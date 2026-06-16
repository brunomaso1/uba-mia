---
name: expense-management-design
description: Full-stack design for expense creation and per-group expense listing — backend API, frontend feature, FAB entry points
metadata:
  type: project
---

# Design: Expense Management Feature

**Date:** 2026-06-16
**Stack:** Angular 22 · FastAPI 0.136.3 · PostgreSQL 18.4

---

## 1. Scope

Allow authenticated users to:

- Create an expense (description, amount, date, group) from a floating (+) button on the Portal page
- Create an expense from a group's expense list, with that group pre-selected
- View the list of expenses belonging to a group ("Visualizar" action from a group card in "Mis Grupos")

An expense always belongs to a group; there is no group-less expense.

**Explicitly excluded (this iteration):** editing/deleting expenses, category selection in the UI, displaying who paid, splits/settlements, pagination.

---

## 2. Database

No schema changes required. The `expenses` table already exists (`db/init/01-init.sql`) with `group_id`, `paid_by`, `category_id` (all NOT NULL FKs), `amount`, `description`, `date`, `created_at`.

`category_id` is NOT NULL but is not part of the requested alta fields. Resolution: the backend assigns a default category automatically — the oldest active row in `categories` (seeded as "Gastos genéricos") — without exposing category in the API request/response. `paid_by` is always the current authenticated user; not user-selectable.

---

## 3. Backend

### 3.1 New files

| File | Purpose |
|------|---------|
| `backend/app/schemas/expense.py` | Pydantic request/response schemas for expenses |
| `backend/app/services/expense.py` | Business logic and DB queries for expenses |
| `backend/app/routers/expenses.py` | Route handlers for the expenses resource |

### 3.2 API endpoints

Nested under groups, same pattern as `/groups/{id}/members`. All require a valid JWT and group membership.

| Method | Path | Description |
|--------|------|--------------|
| GET | `/groups/{group_id}/expenses` | List expenses for the group, ordered by date descending |
| POST | `/groups/{group_id}/expenses` | Create an expense in the group; `paid_by` = current user |

Both return 404 if the group doesn't exist, 403 if the current user is not a member — identical to the existing members endpoints.

### 3.3 Schemas (`schemas/expense.py`)

```python
# Request
ExpenseCreate  { description: str | None, amount: Decimal, date: date }

# Response
ExpenseRead    { id, group_id, description, amount, date, created_at }
```

`paid_by` and `category_id` are not exposed in either schema.

### 3.4 Service logic (`services/expense.py`)

- `get_default_category_id(db)` — SELECT id FROM categories WHERE is_active ORDER BY created_at ASC LIMIT 1
- `create(db, group_id, paid_by, description, amount, expense_date)` — resolves default category, inserts the expense
- `list_for_group(db, group_id)` — SELECT expenses WHERE group_id ORDER BY date DESC

Membership/existence checks happen in the router, matching `routers/groups.py`'s existing pattern (calls into `group_service.get` / `group_service.is_member`).

---

## 4. Frontend

### 4.1 Folder structure

```
frontend/src/app/features/expenses/
├── expenses.service.ts          # HttpClient wrapper for expenses endpoints
├── components/
│   └── expense-form-dialog/     # ts + html + scss + spec — MatDialog for create
└── pages/
    └── group-expenses-page/     # ts + html + scss + spec
```

### 4.2 Routes

```
/groups/:id/expenses  → GroupExpensesPage  (title: 'Gastos del Grupo')
```

Registered as a new child route in `groups.routes.ts` (lazy-loaded from the `expenses` feature folder), alongside the existing `/groups/:id` member route.

### 4.3 ExpensesService

- `listExpenses(groupId): Observable<Expense[]>` → `GET /groups/:id/expenses`
- `createExpense(groupId, { description, amount, date }): Observable<Expense>` → `POST /groups/:id/expenses`

### 4.4 ExpenseFormDialogComponent

A `MatDialog` opened from both the Portal FAB and the group expenses page FAB.

**Inputs (via `MAT_DIALOG_DATA`):** `preselectedGroupId?: string`

**Fields:**
- Descripción (text input)
- Monto (numeric input)
- Fecha (date picker, default: today)
- Grupo (`mat-select`, populated from `GET /groups`; default = `preselectedGroupId` if provided, else the first group in the list)

Implemented with plain signals bound to inputs (no Reactive/Signal Forms), matching the existing style of `add-member-form` and `groups-page`'s inline create form.

On submit → `ExpensesService.createExpense(selectedGroupId, ...)` → close dialog with the created expense (or `undefined` on cancel) → caller refreshes its list/resource.

On error (400/403/500) → inline error message inside the dialog; dialog stays open so the user can retry.

### 4.5 Portal page update

- Add a `mat-fab` button, `position: fixed; bottom: 24px; right: 24px` (or host `style` per Angular rules — no `ngStyle`), icon `add`, `aria-label="Agregar gasto"`
- Click → opens `ExpenseFormDialogComponent` with no `preselectedGroupId`

### 4.6 GroupExpensesPage (`/groups/:id/expenses`)

- Fetches `GET /groups/:id/expenses` via `httpResource`
- Renders a Material list of expenses: description, amount (currency-formatted), date — sorted by date descending (server-sorted)
- Same fixed FAB as the Portal page, opening the dialog with `preselectedGroupId` = the current group id
- On dialog close with a result → `expenses.reload()`
- Back button → `router.navigate(['/groups'])`

### 4.7 GroupCardComponent update

Add a new `mat-icon-button` ("Ver gastos", icon `receipt_long`) next to the existing edit/members/add-member/delete icons → `router.navigate(['/groups', id, 'expenses'])`.

---

## 5. Error handling

- `httpResource` loading/error states in `GroupExpensesPage` follow the same spinner/error-message pattern as `GroupDetailPage`
- Dialog submission errors are shown inline in the dialog (see 4.4); no optimistic updates — wait for server confirmation before closing/refreshing

---

## 6. Testing

- Backend: `pytest` tests for `POST`/`GET /groups/:id/expenses` covering success, 404 (group doesn't exist), and 403 (not a member)
- Frontend: specs for `ExpenseFormDialogComponent` (default values, submit, error display) and `GroupExpensesPage` (loading/empty/error/list states), following the existing groups feature spec style

---

## 7. README update

Add an "Expense Management" section under Features documenting:
- What the feature does
- The components and pages involved
- The API endpoints it uses
