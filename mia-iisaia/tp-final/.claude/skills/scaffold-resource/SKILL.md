---
name: scaffold-resource
description: >-
  Scaffold a new backend REST resource in this FastAPI project following its
  exact layering — SQLAlchemy model, Pydantic schemas, async service functions,
  a thin router prefixed under /api/v1, registration in the model/app
  entrypoints, and a pytest suite covering both the service and the router.
  Invoke when the user wants to create / add a new backend resource, endpoint,
  table, or API for some entity (e.g. "add a tags resource", "scaffold a
  payments endpoint", "new API for budgets").
---

# Scaffold a backend resource

Generate a new resource under `backend/app/` that matches the layering already used
by `categories`, `expenses`, and `groups`. The goal is code indistinguishable from
what's there — same `Mapped` model style, same service-function shape, same thin
router, same test setup. Do not introduce new patterns (no class-based services, no
ORM objects returned from routers).

`categories` is the cleanest reference for a simple CRUD resource — read it if in
doubt.

## 1. Gather inputs

Confirm before writing (infer sensible defaults; ask only for gaps):

- **Resource name**: singular for the model/class (e.g. `Tag`), plural for the table
  and route (`tags`). Tables are plural (project convention).
- **Fields**: name + type + nullability for each column beyond the standard
  `id` (UUID PK) and `created_at`.
- **Operations**: which of list / get / create / update / delete are needed.
- **User-scoped?** If rows belong to a user (like `expenses`/`groups`), the router
  depends on `get_current_user` and the service filters by `user_id`. If global
  reference data (like `categories`), it does not. Decide this explicitly — it
  changes the router and service signatures.

## 2. Files to create / edit

```
backend/
├── app/
│   ├── models/<resource>.py        # new — SQLAlchemy model
│   ├── models/__init__.py          # EDIT — import + add to __all__
│   ├── schemas/<resource>.py       # new — Pydantic Create/Response
│   ├── services/<resource>.py      # new — async functions
│   ├── routers/<resource>.py       # new — APIRouter
│   └── main.py                     # EDIT — include_router
└── tests/test_<resources>.py       # new — service + router tests
```

All names are `snake_case`. The two edits (model registration and router
registration) are mandatory — skipping them means the table isn't created in tests
and the endpoints aren't mounted.

## 3. File templates

Replace `<Resource>` (PascalCase singular, e.g. `Tag`), `<resource>` (snake singular,
e.g. `tag`), `<resources>` (snake plural, e.g. `tags`).

### `app/models/<resource>.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base


class <Resource>(Base):
    __tablename__ = "<resources>"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # ...additional columns; use `str | None` + nullable=True for optionals
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

For a user-scoped resource, add a FK column:
```python
from sqlalchemy import ForeignKey
user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
)
```

### `app/models/__init__.py` (EDIT)

Add the import and extend `__all__` so the table is registered (tests rely on this
to create the schema, and it keeps Alembic autogenerate aware of the model):

```python
from app.models.<resource> import <Resource>
# ...
__all__ = [..., "<Resource>"]
```

### `app/schemas/<resource>.py`

```python
import uuid
from datetime import datetime

from pydantic import BaseModel


class <Resource>Create(BaseModel):
    name: str
    # ...input fields


class <Resource>Response(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

Routers return `*Response` schemas, never raw ORM objects — `from_attributes` lets
Pydantic read them off the model.

### `app/services/<resource>.py`

Module-level async functions taking `db: AsyncSession` as the first argument
(NOT a class). Use `select()`, and `commit` + `refresh` on writes:

```python
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.<resource> import <Resource>


async def list_all(db: AsyncSession) -> list[<Resource>]:
    result = await db.execute(select(<Resource>))
    return list(result.scalars().all())


async def create(db: AsyncSession, name: str) -> <Resource>:
    obj = <Resource>(name=name)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get(db: AsyncSession, <resource>_id: uuid.UUID) -> <Resource> | None:
    result = await db.execute(select(<Resource>).where(<Resource>.id == <resource>_id))
    return result.scalar_one_or_none()
```

For user-scoped resources, take `user_id: uuid.UUID` and add
`.where(<Resource>.user_id == user_id)` to every query. Return `None` for
not-found rather than raising — the router turns that into a 404.

### `app/routers/<resource>.py`

Thin handlers that delegate to the service. The router prefix is just
`/<resources>` — the `/api/v1` part is applied centrally in `main.py` via
`settings.api_prefix`, so do NOT repeat it here.

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas.<resource> import <Resource>Create, <Resource>Response
from app.services import <resource> as <resource>_service

router = APIRouter(prefix="/<resources>", tags=["<resources>"])


@router.get("", response_model=list[<Resource>Response])
async def list_<resources>(db: AsyncSession = Depends(get_db)):
    return await <resource>_service.list_all(db)


@router.post("", response_model=<Resource>Response, status_code=status.HTTP_201_CREATED)
async def create_<resource>(body: <Resource>Create, db: AsyncSession = Depends(get_db)):
    return await <resource>_service.create(db, body.name)


@router.get("/{<resource>_id}", response_model=<Resource>Response)
async def get_<resource>(<resource>_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    obj = await <resource>_service.get(db, <resource>_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="<Resource> not found"
        )
    return obj
```

For a user-scoped resource, add `from app.deps import get_current_user` and
`current_user: User = Depends(get_current_user)`, then pass `current_user.id`
into the service calls. Never return errors as 200 — always raise `HTTPException`.

### `app/main.py` (EDIT)

Mirror the existing router wiring exactly:

```python
from app.routers.<resources> import router as <resources>_router
# ...
app.include_router(<resources>_router, prefix=settings.api_prefix)
```

### `tests/test_<resources>.py`

Two sections — service tests use the `db` fixture directly; router tests override
`get_db` and drive the app with `AsyncClient` + `ASGITransport`. Match
`tests/test_categories.py` exactly:

```python
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.main import app
from app.services import <resource> as <resource>_service

# --- Service tests ---


@pytest.mark.asyncio
async def test_create_<resource>(db: AsyncSession):
    obj = await <resource>_service.create(db, "Ejemplo")
    assert obj.id is not None
    assert obj.name == "Ejemplo"


# --- Router tests ---


@pytest.mark.asyncio
async def test_list_<resources>_empty(db: AsyncSession):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/<resources>")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_<resource>_endpoint(db: AsyncSession):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/<resources>", json={"name": "Ocio"})
    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["name"] == "Ocio"
```

The `db` fixture (in `conftest.py`) creates all registered tables before each test
and drops them after — which is exactly why step 2's edit to `models/__init__.py`
matters. For user-scoped resources, also override `get_current_user` with a function
that yields a `User` row you created via the `db` fixture.

## 4. Database schema (migration)

The test suite builds tables from the models, but the running app does NOT — schema
changes go through **Alembic**, never by editing `db/init/01-init.sql`. After the
model exists, generate and apply a migration:

```bash
docker compose exec backend alembic revision --autogenerate -m "add <resources> table"
docker compose exec backend alembic upgrade head
```

Review the generated migration before applying — autogenerate can miss server
defaults or type nuances. Mention this step to the user; do not run it silently if
the stack isn't up.

## 5. Verify

```bash
cd backend && uv run pytest tests/test_<resources>.py -v
```

Integration tests need `app_db` running (`docker compose up app_db -d`) and read the
DB URL from `TEST_DATABASE_URL`, falling back to `DATABASE_URL`.

Then report to the user: files created and edited (call out the two registration
edits), test results, and the reminder that an Alembic migration is required before
the endpoints work against the real database.
