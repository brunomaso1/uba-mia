# Category Feature — Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full backend for the `category` feature: SQLAlchemy models, Alembic setup, Pydantic schemas, service layer, and REST endpoints (GET / POST / soft-delete).

**Architecture:** Async SQLAlchemy 2.0 session per request (via FastAPI dependency), service layer holds all DB logic, router handles HTTP concerns only. Alembic is initialized for future schema migrations (initial schema lives in `db/init/01-init.sql`).

**Tech Stack:** FastAPI 0.136.3, SQLAlchemy 2.0.36 (async), asyncpg, Alembic 1.14.0, psycopg2-binary (Alembic sync), pytest + pytest-asyncio 0.24.0

---

## File map

| Action   | File                                    | Purpose                                  |
|----------|-----------------------------------------|------------------------------------------|
| Modify   | `backend/pyproject.toml`                | Add asyncpg dependency                   |
| Create   | `backend/app/db.py`                     | Async engine, session factory, Base      |
| Create   | `backend/app/models/__init__.py`        | Re-export all models (Alembic discovery) |
| Create   | `backend/app/models/app_user.py`        | AppUser ORM model                        |
| Create   | `backend/app/models/group.py`           | Group ORM model                          |
| Create   | `backend/app/models/group_member.py`    | GroupMember ORM model                    |
| Create   | `backend/app/models/category.py`        | Category ORM model                       |
| Create   | `backend/app/models/expense.py`         | Expense ORM model                        |
| Create   | `backend/alembic.ini`                   | Alembic config (via `alembic init`)      |
| Modify   | `backend/alembic/env.py`                | Wire models + async URL                  |
| Create   | `backend/app/deps.py`                   | `get_db` async session dependency        |
| Create   | `backend/app/schemas/__init__.py`       | Package marker                           |
| Create   | `backend/app/schemas/category.py`       | CategoryCreate / CategoryResponse        |
| Create   | `backend/app/services/__init__.py`      | Package marker                           |
| Create   | `backend/app/services/category.py`      | list_active, create, deactivate          |
| Create   | `backend/app/routers/__init__.py`       | Package marker                           |
| Create   | `backend/app/routers/categories.py`     | GET / POST / DELETE /api/v1/categories   |
| Modify   | `backend/app/main.py`                   | Register categories router               |
| Create   | `backend/tests/conftest.py`             | Async test engine + DB session fixture   |
| Create   | `backend/tests/test_categories.py`      | Integration tests for service + router   |

---

## Task 1: Add asyncpg and set up the DB module

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/app/db.py`

- [ ] **Step 1: Add asyncpg**

```bash
cd backend
uv add asyncpg
```

Expected: asyncpg appears in `pyproject.toml` under `dependencies`.

- [ ] **Step 2: Create `backend/app/db.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# psycopg2-binary uses postgresql://, asyncpg needs postgresql+asyncpg://
_async_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_async_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/app/db.py
git commit -m "feat: add asyncpg and async SQLAlchemy engine"
```

---

## Task 2: SQLAlchemy ORM models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/app_user.py`
- Create: `backend/app/models/group.py`
- Create: `backend/app/models/group_member.py`
- Create: `backend/app/models/category.py`
- Create: `backend/app/models/expense.py`

All models must be imported in `__init__.py` so Alembic can discover them.

- [ ] **Step 1: Create `backend/app/models/app_user.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base


class AppUser(Base):
    __tablename__ = "app_user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_sub: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

- [ ] **Step 2: Create `backend/app/models/group.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func, quoted_name

from app.db import Base


class Group(Base):
    __tablename__ = quoted_name("group", True)  # "group" is a reserved SQL keyword

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

- [ ] **Step 3: Create `backend/app/models/group_member.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base


class GroupMember(Base):
    __tablename__ = "group_member"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("group.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

- [ ] **Step 4: Create `backend/app/models/category.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base


class Category(Base):
    __tablename__ = "category"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

- [ ] **Step 5: Create `backend/app/models/expense.py`**

```python
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base


class Expense(Base):
    __tablename__ = "expense"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("group.id", ondelete="CASCADE"), nullable=False
    )
    paid_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

- [ ] **Step 6: Create `backend/app/models/__init__.py`**

```python
from app.models.app_user import AppUser
from app.models.category import Category
from app.models.expense import Expense
from app.models.group import Group
from app.models.group_member import GroupMember

__all__ = ["AppUser", "Category", "Expense", "Group", "GroupMember"]
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add SQLAlchemy ORM models for all tables"
```

---

## Task 3: Alembic initialization

Alembic is used for **future** schema changes only. The initial schema lives in `db/init/01-init.sql`. Here we initialize Alembic and stamp the DB so it knows it's at the baseline.

**Files:**
- Create: `backend/alembic.ini` (via `alembic init`)
- Modify: `backend/alembic/env.py`

- [ ] **Step 1: Initialize Alembic inside the backend directory**

```bash
cd backend
alembic init alembic
```

Expected: creates `alembic.ini` and `alembic/` directory with `env.py`, `script.py.mako`, `versions/`.

- [ ] **Step 2: Set the sqlalchemy.url in `backend/alembic.ini`**

Find this line:
```
sqlalchemy.url = driver://user:pass@localhost/dbname
```

Replace with (sync URL for migrations — psycopg2-binary):
```
sqlalchemy.url = postgresql://expense_user:changeme@localhost:5432/expense_db
```

- [ ] **Step 3: Replace `backend/alembic/env.py` content**

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db import Base
import app.models  # noqa: F401 — registers all models with Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Stamp the DB at head (marks baseline without running migrations)**

The app_db container must be running:
```bash
docker compose up app_db -d
alembic stamp head
```

Expected output: `INFO  [alembic.runtime.migration] Running stamp_revision -> <revision_id>`

- [ ] **Step 5: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "chore: initialize Alembic for future schema migrations"
```

---

## Task 4: FastAPI DB session dependency

**Files:**
- Create: `backend/app/deps.py`

- [ ] **Step 1: Create `backend/app/deps.py`**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/deps.py
git commit -m "feat: add async DB session dependency"
```

---

## Task 5: Category Pydantic schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/category.py`

- [ ] **Step 1: Create `backend/app/schemas/__init__.py`**

```python
```

(Empty — package marker only.)

- [ ] **Step 2: Create `backend/app/schemas/category.py`**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas for category"
```

---

## Task 6: Category service

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/category.py`

- [ ] **Step 1: Write the failing tests first** (see Task 9 — write tests before service)

Skip ahead to Task 9 Step 1, then come back here.

- [ ] **Step 2: Create `backend/app/services/__init__.py`**

```python
```

(Empty — package marker only.)

- [ ] **Step 3: Create `backend/app/services/category.py`**

```python
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
```

- [ ] **Step 4: Run service tests to verify they pass**

```bash
cd backend
uv run pytest tests/test_categories.py::test_create_category tests/test_categories.py::test_list_active_categories tests/test_categories.py::test_deactivate_category tests/test_categories.py::test_deactivate_nonexistent -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ backend/tests/conftest.py backend/tests/test_categories.py
git commit -m "feat: add category service with list, create, deactivate"
```

---

## Task 7: Category router

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/categories.py`

- [ ] **Step 1: Create `backend/app/routers/__init__.py`**

```python
```

(Empty — package marker only.)

- [ ] **Step 2: Create `backend/app/routers/categories.py`**

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services import category as category_service

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    return await category_service.list_active(db)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(body: CategoryCreate, db: AsyncSession = Depends(get_db)):
    return await category_service.create(db, body.name, body.description)


@router.delete("/{category_id}", response_model=CategoryResponse)
async def deactivate_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    category = await category_service.deactivate(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category
```

- [ ] **Step 3: Register the router in `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.categories import router as categories_router

app = FastAPI(title="Expense API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 4: Run router tests to verify they pass**

```bash
cd backend
uv run pytest tests/test_categories.py -v
```

Expected: all tests PASS (including router tests added in Task 9).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/ backend/app/main.py
git commit -m "feat: add category router GET/POST/DELETE /api/v1/categories"
```

---

## Task 8: Run full test suite

- [ ] **Step 1: Run all tests**

```bash
cd backend
uv run pytest -v
```

Expected: all tests PASS including `test_health.py` and `test_categories.py`.

- [ ] **Step 2: If test_health fails**

`test_health.py` uses a sync `TestClient`. It doesn't touch the DB so it should still pass. If it fails, the error will be import-related — fix the import causing the issue before continuing.

---

## Task 9: Integration tests

Write these **before** the service and router (TDD). This task is referenced by Task 6 and Task 7.

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_categories.py`

- [ ] **Step 1: Create `backend/tests/conftest.py`**

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
import app.models  # noqa: F401 — ensures all tables are registered

TEST_DATABASE_URL = "postgresql+asyncpg://expense_user:changeme@localhost:5432/expense_db"


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

- [ ] **Step 2: Create `backend/tests/test_categories.py`**

```python
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.main import app
from app.services import category as category_service


# --- Service tests ---

@pytest.mark.asyncio
async def test_create_category(db: AsyncSession):
    cat = await category_service.create(db, "Transporte", "Gastos de transporte")
    assert cat.id is not None
    assert cat.name == "Transporte"
    assert cat.description == "Gastos de transporte"
    assert cat.is_active is True


@pytest.mark.asyncio
async def test_list_active_categories(db: AsyncSession):
    await category_service.create(db, "Comida", None)
    await category_service.create(db, "Deporte", None)
    cats = await category_service.list_active(db)
    assert len(cats) == 2
    assert all(c.is_active for c in cats)


@pytest.mark.asyncio
async def test_deactivate_category(db: AsyncSession):
    cat = await category_service.create(db, "Hogar", None)
    deactivated = await category_service.deactivate(db, cat.id)
    assert deactivated is not None
    assert deactivated.is_active is False
    active = await category_service.list_active(db)
    assert all(c.id != cat.id for c in active)


@pytest.mark.asyncio
async def test_deactivate_nonexistent(db: AsyncSession):
    result = await category_service.deactivate(db, uuid.uuid4())
    assert result is None


# --- Router tests ---

@pytest.mark.asyncio
async def test_get_categories_empty(db: AsyncSession):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/categories")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_post_category(db: AsyncSession):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/categories", json={"name": "Ocio", "description": None})
    app.dependency_overrides.clear()
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ocio"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_delete_category_soft_deletes(db: AsyncSession):
    cat = await category_service.create(db, "Temporal", None)

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/api/v1/categories/{cat.id}")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_category_not_found(db: AsyncSession):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/api/v1/categories/{uuid.uuid4()}")
    app.dependency_overrides.clear()
    assert response.status_code == 404
```

- [ ] **Step 3: Run only the service tests (router not implemented yet — they'll fail)**

```bash
cd backend
uv run pytest tests/test_categories.py::test_create_category tests/test_categories.py::test_list_active_categories tests/test_categories.py::test_deactivate_category tests/test_categories.py::test_deactivate_nonexistent -v
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError` (service doesn't exist yet). That's correct — now go implement Task 6.

---

## Execution order

Tasks must be done in this order (dependencies):

```
Task 1 (DB module)
  → Task 2 (models)
    → Task 3 (Alembic)
    → Task 9 Step 1-2 (write tests — before service)
      → Task 4 (deps.py)
      → Task 5 (schemas)
        → Task 6 (service)
          → Task 7 (router)
            → Task 8 (full test suite)
```
