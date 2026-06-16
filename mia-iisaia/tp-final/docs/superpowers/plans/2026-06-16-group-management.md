# Group Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack group management feature: backend CRUD endpoints for groups plus a user listing endpoint, and an Angular feature for creating/renaming/deleting groups and adding members, with a separate detail page for viewing members.

**Architecture:** Backend adds a `groups` router (7 endpoints), extends the `users` router with a list endpoint, and follows the existing FastAPI `router → service → schema` pattern. The frontend adds a `features/groups/` feature with a `GroupsService` (mutations only), two pages (`GroupsPage`, `GroupDetailPage`), and two components (`GroupCardComponent`, `AddMemberFormComponent`). All reads use Angular's `httpResource`; mutations go through `GroupsService` via `HttpClient`. The portal page is simplified to a single navigation card.

**Tech Stack:** FastAPI 0.136.3 + SQLAlchemy async (backend); Angular 22 with `httpResource`, `@Service`, Angular Material (frontend); pytest + httpx (backend tests); Angular TestBed + Vitest (frontend tests).

---

## File Map

### Backend — new
- `backend/app/schemas/group.py` — `GroupCreate`, `GroupRename`, `AddMemberBody`, `GroupRead`, `MemberRead`
- `backend/app/services/group.py` — all group business logic
- `backend/app/routers/groups.py` — all group endpoints
- `backend/tests/test_groups.py` — service + router tests

### Backend — modified
- `backend/app/schemas/user.py` — add `UserPublic` schema (id, display_name, email)
- `backend/app/routers/users.py` — add `GET /users` list endpoint
- `backend/app/main.py` — register groups router

### Frontend — new
- `frontend/src/app/features/groups/groups.service.ts`
- `frontend/src/app/features/groups/groups.routes.ts`
- `frontend/src/app/features/groups/pages/groups-page/groups-page.ts`
- `frontend/src/app/features/groups/pages/groups-page/groups-page.html`
- `frontend/src/app/features/groups/pages/groups-page/groups-page.scss`
- `frontend/src/app/features/groups/pages/groups-page/groups-page.spec.ts`
- `frontend/src/app/features/groups/pages/group-detail-page/group-detail-page.ts`
- `frontend/src/app/features/groups/pages/group-detail-page/group-detail-page.html`
- `frontend/src/app/features/groups/pages/group-detail-page/group-detail-page.scss`
- `frontend/src/app/features/groups/pages/group-detail-page/group-detail-page.spec.ts`
- `frontend/src/app/features/groups/components/group-card/group-card.ts`
- `frontend/src/app/features/groups/components/group-card/group-card.html`
- `frontend/src/app/features/groups/components/group-card/group-card.scss`
- `frontend/src/app/features/groups/components/group-card/group-card.spec.ts`
- `frontend/src/app/features/groups/components/add-member-form/add-member-form.ts`
- `frontend/src/app/features/groups/components/add-member-form/add-member-form.html`
- `frontend/src/app/features/groups/components/add-member-form/add-member-form.scss`
- `frontend/src/app/features/groups/components/add-member-form/add-member-form.spec.ts`

### Frontend — modified
- `frontend/src/app/app.routes.ts` — add groups lazy child route
- `frontend/src/app/shared/components/app-header/app-header.ts` — add Grupos to navItems
- `frontend/src/app/features/portal/pages/portal-page/portal-page.ts` — replace user card with nav card
- `frontend/src/app/features/portal/pages/portal-page/portal-page.html` — groups nav card template
- `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts` — update tests

### Docs
- `README.md` — add Group Management feature section

---

## Task 1: Backend — Group schemas + UserPublic

**Files:**
- Create: `backend/app/schemas/group.py`
- Modify: `backend/app/schemas/user.py`

- [ ] **Step 1: Create `backend/app/schemas/group.py`**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str


class GroupRename(BaseModel):
    name: str


class AddMemberBody(BaseModel):
    user_id: uuid.UUID


class GroupRead(BaseModel):
    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    created_at: datetime
    member_count: int

    model_config = {"from_attributes": True}


class MemberRead(BaseModel):
    user_id: uuid.UUID
    display_name: str
    email: str
    joined_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Add `UserPublic` to `backend/app/schemas/user.py`**

Append after the existing `UserRead` class:

```python
class UserPublic(BaseModel):
    id: uuid.UUID
    display_name: str
    email: str

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/group.py backend/app/schemas/user.py
git commit -m "feat: add group and user public schemas"
```

---

## Task 2: Backend — User list endpoint + tests

**Files:**
- Modify: `backend/app/routers/users.py`
- Modify: `backend/tests/test_users.py`

- [ ] **Step 1: Write the failing test**

Add to the bottom of `backend/tests/test_users.py`:

```python
@pytest.mark.asyncio
async def test_list_users_returns_all(db: AsyncSession):
    from app.services import user as user_service

    await user_service.get_or_create(db, "sub-lu-1", "u1@lu.com", "User One")
    await user_service.get_or_create(db, "sub-lu-2", "u2@lu.com", "User Two")

    claims = {"sub": "sub-lu-req", "email": "req@lu.com", "name": "Requester"}

    async def override_user():
        return claims

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    emails = [u["email"] for u in data]
    assert "u1@lu.com" in emails
    assert "u2@lu.com" in emails
    for u in data:
        assert "id" in u
        assert "display_name" in u
        assert "email" in u
        assert "keycloak_sub" not in u  # UserPublic hides internal fields
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/test_users.py::test_list_users_returns_all -v
```

Expected: FAIL — `404 Not Found` (route doesn't exist yet).

- [ ] **Step 3: Implement `GET /users` in `backend/app/routers/users.py`**

Replace the entire file:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserPublic, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserPublic])
async def list_users(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.display_name))
    return list(result.scalars().all())


@router.get("/me", response_model=UserRead)
async def read_me(user: User = Depends(get_current_user)):
    return user
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/test_users.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/users.py backend/tests/test_users.py
git commit -m "feat: add GET /users list endpoint"
```

---

## Task 3: Backend — Group service + service tests

**Files:**
- Create: `backend/app/services/group.py`
- Create: `backend/tests/test_groups.py` (service section)

- [ ] **Step 1: Write the failing service tests**

Create `backend/tests/test_groups.py`:

```python
import uuid

import pytest
from fastapi_keycloak_middleware import get_user
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.main import app
from app.services import group as group_service
from app.services import user as user_service


async def _make_user(db: AsyncSession, sub: str, email: str, name: str):
    return await user_service.get_or_create(db, sub, email, name)


# ── Service tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_group_adds_creator_as_member(db: AsyncSession):
    creator = await _make_user(db, "sub-cg-1", "alice@cg.com", "Alice")
    group = await group_service.create(db, "Viaje", creator.id)
    assert group.id is not None
    assert group.name == "Viaje"
    assert group.created_by == creator.id
    count = await group_service.get_member_count(db, group.id)
    assert count == 1


@pytest.mark.asyncio
async def test_list_for_user_returns_only_joined_groups(db: AsyncSession):
    alice = await _make_user(db, "sub-lf-a", "alice@lf.com", "Alice")
    bob = await _make_user(db, "sub-lf-b", "bob@lf.com", "Bob")
    await group_service.create(db, "Alice Group", alice.id)
    await group_service.create(db, "Bob Group", bob.id)
    rows = await group_service.list_for_user(db, alice.id)
    assert len(rows) == 1
    assert rows[0].Group.name == "Alice Group"
    assert rows[0].member_count == 1


@pytest.mark.asyncio
async def test_rename_group(db: AsyncSession):
    alice = await _make_user(db, "sub-rn-a", "alice@rn.com", "Alice")
    group = await group_service.create(db, "Old Name", alice.id)
    renamed = await group_service.rename(db, group.id, "New Name")
    assert renamed is not None
    assert renamed.name == "New Name"


@pytest.mark.asyncio
async def test_rename_nonexistent_returns_none(db: AsyncSession):
    result = await group_service.rename(db, uuid.uuid4(), "Name")
    assert result is None


@pytest.mark.asyncio
async def test_delete_group(db: AsyncSession):
    alice = await _make_user(db, "sub-del-a", "alice@del.com", "Alice")
    group = await group_service.create(db, "To Delete", alice.id)
    deleted = await group_service.delete(db, group.id)
    assert deleted is True
    rows = await group_service.list_for_user(db, alice.id)
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_false(db: AsyncSession):
    result = await group_service.delete(db, uuid.uuid4())
    assert result is False


@pytest.mark.asyncio
async def test_add_member(db: AsyncSession):
    alice = await _make_user(db, "sub-am-a", "alice@am.com", "Alice")
    bob = await _make_user(db, "sub-am-b", "bob@am.com", "Bob")
    group = await group_service.create(db, "Shared", alice.id)
    ok = await group_service.add_member(db, group.id, bob.id)
    assert ok is True
    assert await group_service.get_member_count(db, group.id) == 2


@pytest.mark.asyncio
async def test_add_member_is_idempotent(db: AsyncSession):
    alice = await _make_user(db, "sub-idem-a", "alice@idem.com", "Alice")
    group = await group_service.create(db, "Idem Group", alice.id)
    ok = await group_service.add_member(db, group.id, alice.id)
    assert ok is True
    assert await group_service.get_member_count(db, group.id) == 1


@pytest.mark.asyncio
async def test_add_member_group_not_found(db: AsyncSession):
    alice = await _make_user(db, "sub-404-a", "alice@404.com", "Alice")
    ok = await group_service.add_member(db, uuid.uuid4(), alice.id)
    assert ok is False


@pytest.mark.asyncio
async def test_add_member_user_not_found(db: AsyncSession):
    alice = await _make_user(db, "sub-404-b", "alice@404b.com", "Alice")
    group = await group_service.create(db, "Group", alice.id)
    ok = await group_service.add_member(db, group.id, uuid.uuid4())
    assert ok is False


@pytest.mark.asyncio
async def test_list_members(db: AsyncSession):
    alice = await _make_user(db, "sub-lm-a", "alice@lm.com", "Alice")
    bob = await _make_user(db, "sub-lm-b", "bob@lm.com", "Bob")
    group = await group_service.create(db, "Shared", alice.id)
    await group_service.add_member(db, group.id, bob.id)
    rows = await group_service.list_members(db, group.id)
    assert rows is not None
    assert len(rows) == 2
    emails = {row.User.email for row in rows}
    assert emails == {"alice@lm.com", "bob@lm.com"}


@pytest.mark.asyncio
async def test_list_members_group_not_found(db: AsyncSession):
    result = await group_service.list_members(db, uuid.uuid4())
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/test_groups.py -k "not router" -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.group'`.

- [ ] **Step 3: Create `backend/app/services/group.py`**

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User


async def get_member_count(db: AsyncSession, group_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).where(GroupMember.group_id == group_id)
    )
    return result.scalar_one()


async def list_for_user(db: AsyncSession, user_id: uuid.UUID):
    member_count_sq = (
        select(func.count())
        .where(GroupMember.group_id == Group.id)
        .correlate(Group)
        .scalar_subquery()
    )
    stmt = (
        select(Group, member_count_sq.label("member_count"))
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == user_id)
        .order_by(Group.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.all()


async def create(db: AsyncSession, name: str, creator_id: uuid.UUID) -> Group:
    group = Group(name=name, created_by=creator_id)
    db.add(group)
    await db.flush()
    db.add(GroupMember(user_id=creator_id, group_id=group.id))
    await db.commit()
    await db.refresh(group)
    return group


async def rename(db: AsyncSession, group_id: uuid.UUID, name: str) -> Group | None:
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        return None
    group.name = name
    await db.commit()
    await db.refresh(group)
    return group


async def delete(db: AsyncSession, group_id: uuid.UUID) -> bool:
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        return False
    await db.delete(group)
    await db.commit()
    return True


async def add_member(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    if not (
        await db.execute(select(Group).where(Group.id == group_id))
    ).scalar_one_or_none():
        return False
    if not (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none():
        return False
    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return True  # already a member — idempotent
    db.add(GroupMember(user_id=user_id, group_id=group_id))
    await db.commit()
    return True


async def list_members(db: AsyncSession, group_id: uuid.UUID):
    if not (
        await db.execute(select(Group).where(Group.id == group_id))
    ).scalar_one_or_none():
        return None
    stmt = (
        select(User, GroupMember.joined_at)
        .join(GroupMember, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.joined_at)
    )
    result = await db.execute(stmt)
    return result.all()
```

- [ ] **Step 4: Run service tests to verify they pass**

```bash
cd backend && uv run pytest tests/test_groups.py -k "not router" -v
```

Expected: all service tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/group.py backend/tests/test_groups.py
git commit -m "feat: add group service with tests"
```

---

## Task 4: Backend — Group router + tests + register

**Files:**
- Create: `backend/app/routers/groups.py`
- Modify: `backend/tests/test_groups.py` (router section)
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing router tests**

Append to the bottom of `backend/tests/test_groups.py`:

```python
# ── Router tests ───────────────────────────────────────────────────────────────


def _claims(sub: str, email: str, name: str) -> dict:
    return {"sub": sub, "email": email, "name": name}


@pytest.mark.asyncio
async def test_get_groups_empty(db: AsyncSession):
    async def override_user():
        return _claims("sub-rt-1", "rt1@test.com", "RT One")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/groups")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_post_group_creates_and_returns(db: AsyncSession):
    async def override_user():
        return _claims("sub-rt-2", "rt2@test.com", "RT Two")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/groups", json={"name": "Vacaciones"})
    app.dependency_overrides.clear()
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Vacaciones"
    assert data["member_count"] == 1


@pytest.mark.asyncio
async def test_patch_group_renames(db: AsyncSession):
    async def override_user():
        return _claims("sub-rt-3", "rt3@test.com", "RT Three")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        create_resp = await client.post("/api/v1/groups", json={"name": "Old"})
        group_id = create_resp.json()["id"]
        rename_resp = await client.patch(
            f"/api/v1/groups/{group_id}", json={"name": "New"}
        )
    app.dependency_overrides.clear()
    assert rename_resp.status_code == 200
    assert rename_resp.json()["name"] == "New"
    assert rename_resp.json()["member_count"] == 1


@pytest.mark.asyncio
async def test_patch_nonexistent_group_returns_404(db: AsyncSession):
    async def override_user():
        return _claims("sub-rt-4", "rt4@test.com", "RT Four")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/api/v1/groups/{uuid.uuid4()}", json={"name": "X"}
        )
    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_group_returns_204(db: AsyncSession):
    async def override_user():
        return _claims("sub-rt-5", "rt5@test.com", "RT Five")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        create_resp = await client.post("/api/v1/groups", json={"name": "Temp"})
        group_id = create_resp.json()["id"]
        delete_resp = await client.delete(f"/api/v1/groups/{group_id}")
    app.dependency_overrides.clear()
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_group_returns_404(db: AsyncSession):
    async def override_user():
        return _claims("sub-rt-6", "rt6@test.com", "RT Six")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(f"/api/v1/groups/{uuid.uuid4()}")
    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_member_adds_user(db: AsyncSession):
    alice = await _make_user(db, "sub-pm-a", "alice@pm.com", "Alice")
    bob = await _make_user(db, "sub-pm-b", "bob@pm.com", "Bob")

    async def override_user():
        return _claims("sub-pm-a", "alice@pm.com", "Alice")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        create_resp = await client.post("/api/v1/groups", json={"name": "Team"})
        group_id = create_resp.json()["id"]
        add_resp = await client.post(
            f"/api/v1/groups/{group_id}/members",
            json={"user_id": str(bob.id)},
        )
    app.dependency_overrides.clear()
    assert add_resp.status_code == 204


@pytest.mark.asyncio
async def test_get_members_returns_list(db: AsyncSession):
    alice = await _make_user(db, "sub-gm-a", "alice@gm.com", "Alice")
    bob = await _make_user(db, "sub-gm-b", "bob@gm.com", "Bob")

    async def override_user():
        return _claims("sub-gm-a", "alice@gm.com", "Alice")

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        create_resp = await client.post("/api/v1/groups", json={"name": "Team"})
        group_id = create_resp.json()["id"]
        await client.post(
            f"/api/v1/groups/{group_id}/members",
            json={"user_id": str(bob.id)},
        )
        members_resp = await client.get(f"/api/v1/groups/{group_id}/members")
    app.dependency_overrides.clear()
    assert members_resp.status_code == 200
    members = members_resp.json()
    assert len(members) == 2
    emails = {m["email"] for m in members}
    assert emails == {"alice@gm.com", "bob@gm.com"}
```

- [ ] **Step 2: Run router tests to verify they fail**

```bash
cd backend && uv run pytest tests/test_groups.py -k "router or test_get_groups or test_post_group or test_patch or test_delete or test_post_member or test_get_members" -v
```

Expected: FAIL — `404 Not Found` (routes not registered).

- [ ] **Step 3: Create `backend/app/routers/groups.py`**

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.group import (
    AddMemberBody,
    GroupCreate,
    GroupRead,
    GroupRename,
    MemberRead,
)
from app.services import group as group_service

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[GroupRead])
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await group_service.list_for_user(db, current_user.id)
    return [
        GroupRead(
            id=row.Group.id,
            name=row.Group.name,
            created_by=row.Group.created_by,
            created_at=row.Group.created_at,
            member_count=row.member_count,
        )
        for row in rows
    ]


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(
    body: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await group_service.create(db, body.name, current_user.id)
    return GroupRead(
        id=group.id,
        name=group.name,
        created_by=group.created_by,
        created_at=group.created_at,
        member_count=1,
    )


@router.patch("/{group_id}", response_model=GroupRead)
async def rename_group(
    group_id: uuid.UUID,
    body: GroupRename,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = await group_service.rename(db, group_id, body.name)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    member_count = await group_service.get_member_count(db, group_id)
    return GroupRead(
        id=group.id,
        name=group.name,
        created_by=group.created_by,
        created_at=group.created_at,
        member_count=member_count,
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await group_service.delete(db, group_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )


@router.post(
    "/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT
)
async def add_member(
    group_id: uuid.UUID,
    body: AddMemberBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await group_service.add_member(db, group_id, body.user_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group or user not found",
        )


@router.get("/{group_id}/members", response_model=list[MemberRead])
async def list_members(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await group_service.list_members(db, group_id)
    if rows is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    return [
        MemberRead(
            user_id=row.User.id,
            display_name=row.User.display_name,
            email=row.User.email,
            joined_at=row.joined_at,
        )
        for row in rows
    ]
```

- [ ] **Step 4: Register the router in `backend/app/main.py`**

Replace the entire file:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware

from app.core.config import settings
from app.deps import map_user
from app.routers.categories import router as categories_router
from app.routers.groups import router as groups_router
from app.routers.users import router as users_router

app = FastAPI(title="Expense API", version="0.1.0")

app.include_router(categories_router, prefix=settings.api_prefix)
app.include_router(groups_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)

keycloak_config = KeycloakConfiguration(
    url=f"{settings.keycloak_url}/",
    realm=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
)

setup_keycloak_middleware(
    app,
    keycloak_configuration=keycloak_config,
    user_mapper=map_user,
    exclude_patterns=["/health", "/docs", "/redoc", "/openapi.json"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/test")
def test_info():
    return {
        "service": app.title,
        "version": app.version,
        "api_prefix": settings.api_prefix,
        "status": "ok",
    }
```

- [ ] **Step 5: Run all backend tests to verify everything passes**

```bash
cd backend && uv run pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/groups.py backend/app/main.py backend/tests/test_groups.py
git commit -m "feat: add group router endpoints with tests"
```

---

## Task 5: Frontend — GroupsService

**Files:**
- Create: `frontend/src/app/features/groups/groups.service.ts`

The service exports the TypeScript interfaces used by all group components, and provides mutation methods (POST/PATCH/DELETE) via `HttpClient`. Reads are done with `httpResource` directly in components.

- [ ] **Step 1: Create `frontend/src/app/features/groups/groups.service.ts`**

```typescript
import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ConfigService } from '../../core/config.service';

export interface Group {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
  member_count: number;
}

export interface Member {
  user_id: string;
  display_name: string;
  email: string;
  joined_at: string;
}

export interface UserPublic {
  id: string;
  display_name: string;
  email: string;
}

@Service()
export class GroupsService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(ConfigService);

  private get base(): string {
    return `${this.config.apiUrl()}/groups`;
  }

  createGroup(name: string): Observable<Group> {
    return this.http.post<Group>(this.base, { name });
  }

  renameGroup(id: string, name: string): Observable<Group> {
    return this.http.patch<Group>(`${this.base}/${id}`, { name });
  }

  deleteGroup(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/${id}`);
  }

  addMember(groupId: string, userId: string): Observable<void> {
    return this.http.post<void>(`${this.base}/${groupId}/members`, {
      user_id: userId,
    });
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/features/groups/groups.service.ts
git commit -m "feat: add GroupsService with mutation methods and shared interfaces"
```

---

## Task 6: Frontend — GroupCard component

**Files:**
- Create: `frontend/src/app/features/groups/components/group-card/group-card.ts`
- Create: `frontend/src/app/features/groups/components/group-card/group-card.html`
- Create: `frontend/src/app/features/groups/components/group-card/group-card.scss`
- Create: `frontend/src/app/features/groups/components/group-card/group-card.spec.ts`

The card receives a `Group` and the list of all app users. It handles rename (inline edit), delete, and "open add-member form" locally, emitting events to its parent after each successful mutation.

- [ ] **Step 1: Create `group-card.ts`**

```typescript
import {
  Component,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { Group, GroupsService, UserPublic } from '../../groups.service';
import { AddMemberFormComponent } from '../add-member-form/add-member-form';

@Component({
  selector: 'app-group-card',
  imports: [
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    AddMemberFormComponent,
  ],
  templateUrl: './group-card.html',
  styleUrl: './group-card.scss',
})
export class GroupCardComponent {
  private readonly groupsService = inject(GroupsService);
  private readonly router = inject(Router);

  readonly group = input.required<Group>();
  readonly allUsers = input<UserPublic[]>([]);

  readonly renamed = output<Group>();
  readonly deleted = output<void>();
  readonly memberAdded = output<void>();

  protected readonly isEditing = signal(false);
  protected readonly editName = signal('');
  protected readonly showAddMember = signal(false);
  protected readonly isSaving = signal(false);

  protected startEdit(): void {
    this.editName.set(this.group().name);
    this.isEditing.set(true);
  }

  protected cancelEdit(): void {
    this.isEditing.set(false);
  }

  protected confirmRename(): void {
    const name = this.editName().trim();
    if (!name || name === this.group().name) {
      this.isEditing.set(false);
      return;
    }
    this.isSaving.set(true);
    this.groupsService.renameGroup(this.group().id, name).subscribe({
      next: (updated) => {
        this.renamed.emit(updated);
        this.isEditing.set(false);
        this.isSaving.set(false);
      },
      error: () => this.isSaving.set(false),
    });
  }

  protected onDelete(): void {
    this.isSaving.set(true);
    this.groupsService.deleteGroup(this.group().id).subscribe({
      next: () => this.deleted.emit(),
      error: () => this.isSaving.set(false),
    });
  }

  protected goToDetail(): void {
    this.router.navigate(['/groups', this.group().id]);
  }

  protected onMemberAdded(): void {
    this.showAddMember.set(false);
    this.memberAdded.emit();
  }
}
```

- [ ] **Step 2: Create `group-card.html`**

```html
<mat-card>
  <mat-card-header>
    @if (isEditing()) {
      <input
        class="edit-input"
        [value]="editName()"
        (input)="editName.set($any($event.target).value)"
        (keydown.enter)="confirmRename()"
        (keydown.escape)="cancelEdit()"
        aria-label="Nombre del grupo"
        autofocus
      />
      <button
        mat-icon-button
        (click)="confirmRename()"
        [disabled]="isSaving()"
        aria-label="Confirmar nombre"
      >
        <mat-icon>check</mat-icon>
      </button>
      <button mat-icon-button (click)="cancelEdit()" aria-label="Cancelar edición">
        <mat-icon>close</mat-icon>
      </button>
    } @else {
      <mat-card-title>{{ group().name }}</mat-card-title>
    }
  </mat-card-header>

  <mat-card-content>
    <p class="member-count">
      {{ group().member_count }}
      {{ group().member_count === 1 ? 'miembro' : 'miembros' }}
    </p>

    @if (showAddMember()) {
      <app-add-member-form
        [groupId]="group().id"
        [allUsers]="allUsers()"
        (memberAdded)="onMemberAdded()"
      />
    }
  </mat-card-content>

  <mat-card-actions>
    <button
      mat-icon-button
      (click)="startEdit()"
      [disabled]="isEditing() || isSaving()"
      aria-label="Renombrar grupo"
    >
      <mat-icon>edit</mat-icon>
    </button>
    <button mat-icon-button (click)="goToDetail()" aria-label="Ver miembros">
      <mat-icon>people</mat-icon>
    </button>
    <button
      mat-icon-button
      (click)="showAddMember.set(!showAddMember())"
      aria-label="Agregar miembro"
    >
      <mat-icon>person_add</mat-icon>
    </button>
    <button
      mat-icon-button
      (click)="onDelete()"
      [disabled]="isSaving()"
      aria-label="Eliminar grupo"
      color="warn"
    >
      <mat-icon>delete</mat-icon>
    </button>
  </mat-card-actions>
</mat-card>
```

- [ ] **Step 3: Create `group-card.scss`**

```scss
:host {
  display: block;
}

.edit-input {
  flex: 1;
  border: none;
  border-bottom: 1px solid var(--mat-sys-primary);
  background: transparent;
  font-size: 1.25rem;
  font-weight: 500;
  outline: none;
  padding: 0;
  color: inherit;
}

.member-count {
  margin: 0;
  color: var(--mat-sys-on-surface-variant);
  font-size: 0.875rem;
}

mat-card-actions {
  display: flex;
  gap: 4px;
}
```

- [ ] **Step 4: Create `group-card.spec.ts`**

```typescript
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';

import { GroupCardComponent } from './group-card';
import { GroupsService, Group } from '../../groups.service';
import { ConfigService } from '../../../../core/config.service';

const mockGroup: Group = {
  id: 'g-1',
  name: 'Test Group',
  created_by: 'u-1',
  created_at: '2026-01-01T00:00:00Z',
  member_count: 2,
};

describe('GroupCardComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupCardComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        {
          provide: GroupsService,
          useValue: {
            renameGroup: () => of(mockGroup),
            deleteGroup: () => of(undefined),
            addMember: () => of(undefined),
          },
        },
        {
          provide: ConfigService,
          useValue: { apiUrl: () => 'http://localhost:8000/api/v1' },
        },
        {
          provide: OidcSecurityService,
          useValue: {
            authenticated: signal({ isAuthenticated: true }),
          },
        },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(GroupCardComponent);
    fixture.componentRef.setInput('group', mockGroup);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows group name', () => {
    const fixture = TestBed.createComponent(GroupCardComponent);
    fixture.componentRef.setInput('group', mockGroup);
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).textContent,
    ).toContain('Test Group');
  });

  it('shows member count', () => {
    const fixture = TestBed.createComponent(GroupCardComponent);
    fixture.componentRef.setInput('group', mockGroup);
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).textContent,
    ).toContain('2 miembros');
  });
});
```

- [ ] **Step 5: Run frontend tests**

```bash
cd frontend && ng test --run-in-band 2>&1 | head -60
```

Expected: `GroupCardComponent` tests PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/features/groups/components/group-card/
git commit -m "feat: add GroupCard component"
```

---

## Task 7: Frontend — AddMemberForm component

**Files:**
- Create: `frontend/src/app/features/groups/components/add-member-form/add-member-form.ts`
- Create: `frontend/src/app/features/groups/components/add-member-form/add-member-form.html`
- Create: `frontend/src/app/features/groups/components/add-member-form/add-member-form.scss`
- Create: `frontend/src/app/features/groups/components/add-member-form/add-member-form.spec.ts`

Fetches the group's current members via `httpResource` and filters them out of the `allUsers` input. On selection + submit, calls `GroupsService.addMember` and emits `memberAdded`.

- [ ] **Step 1: Create `add-member-form.ts`**

```typescript
import {
  Component,
  computed,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { httpResource } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from '../../../../core/config.service';
import { GroupsService, Member, UserPublic } from '../../groups.service';

@Component({
  selector: 'app-add-member-form',
  imports: [
    MatButtonModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
    MatSelectModule,
  ],
  templateUrl: './add-member-form.html',
  styleUrl: './add-member-form.scss',
})
export class AddMemberFormComponent {
  private readonly groupsService = inject(GroupsService);
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  readonly groupId = input.required<string>();
  readonly allUsers = input<UserPublic[]>([]);
  readonly memberAdded = output<void>();

  private readonly isAuthenticated = computed(
    () => this.oidc.authenticated().isAuthenticated,
  );

  protected readonly members = httpResource<Member[]>(() =>
    this.isAuthenticated()
      ? `${this.config.apiUrl()}/groups/${this.groupId()}/members`
      : undefined,
  );

  protected readonly availableUsers = computed(() => {
    const memberIds = new Set(
      (this.members.value() ?? []).map((m) => m.user_id),
    );
    return this.allUsers().filter((u) => !memberIds.has(u.id));
  });

  protected readonly selectedUserId = signal<string | null>(null);
  protected readonly isSubmitting = signal(false);

  protected onSubmit(): void {
    const userId = this.selectedUserId();
    if (!userId) return;
    this.isSubmitting.set(true);
    this.groupsService.addMember(this.groupId(), userId).subscribe({
      next: () => {
        this.selectedUserId.set(null);
        this.isSubmitting.set(false);
        this.memberAdded.emit();
      },
      error: () => this.isSubmitting.set(false),
    });
  }
}
```

- [ ] **Step 2: Create `add-member-form.html`**

```html
<div class="add-member-form">
  @if (members.isLoading()) {
    <mat-spinner diameter="24" aria-label="Cargando miembros actuales…" />
  } @else {
    <mat-form-field appearance="outline" class="user-select">
      <mat-label>Seleccionar usuario</mat-label>
      <mat-select
        [value]="selectedUserId()"
        (selectionChange)="selectedUserId.set($event.value)"
        aria-label="Usuario a agregar"
      >
        @for (user of availableUsers(); track user.id) {
          <mat-option [value]="user.id">
            {{ user.display_name }} ({{ user.email }})
          </mat-option>
        } @empty {
          <mat-option disabled>Todos los usuarios ya son miembros</mat-option>
        }
      </mat-select>
    </mat-form-field>

    <button
      mat-flat-button
      color="primary"
      (click)="onSubmit()"
      [disabled]="!selectedUserId() || isSubmitting()"
    >
      Agregar
    </button>
  }
</div>
```

- [ ] **Step 3: Create `add-member-form.scss`**

```scss
.add-member-form {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 8px;
}

.user-select {
  flex: 1;
  min-width: 200px;
}
```

- [ ] **Step 4: Create `add-member-form.spec.ts`**

```typescript
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';

import { AddMemberFormComponent } from './add-member-form';
import { GroupsService } from '../../groups.service';
import { ConfigService } from '../../../../core/config.service';

describe('AddMemberFormComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddMemberFormComponent],
      providers: [
        provideHttpClient(),
        {
          provide: GroupsService,
          useValue: { addMember: () => of(undefined) },
        },
        {
          provide: ConfigService,
          useValue: { apiUrl: () => 'http://localhost:8000/api/v1' },
        },
        {
          provide: OidcSecurityService,
          useValue: {
            authenticated: signal({ isAuthenticated: true }),
          },
        },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(AddMemberFormComponent);
    fixture.componentRef.setInput('groupId', 'g-1');
    expect(fixture.componentInstance).toBeTruthy();
  });
});
```

- [ ] **Step 5: Run frontend tests**

```bash
cd frontend && ng test --run-in-band 2>&1 | head -60
```

Expected: `AddMemberFormComponent` tests PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/features/groups/components/add-member-form/
git commit -m "feat: add AddMemberForm component"
```

---

## Task 8: Frontend — GroupsPage

**Files:**
- Create: `frontend/src/app/features/groups/pages/groups-page/groups-page.ts`
- Create: `frontend/src/app/features/groups/pages/groups-page/groups-page.html`
- Create: `frontend/src/app/features/groups/pages/groups-page/groups-page.scss`
- Create: `frontend/src/app/features/groups/pages/groups-page/groups-page.spec.ts`

Lists the current user's groups, creates new ones inline, and delegates card-level mutations to `GroupCardComponent`. Reloads groups via `httpResource.reload()` after any mutation.

- [ ] **Step 1: Create `groups-page.ts`**

```typescript
import { Component, inject, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from '../../../../core/config.service';
import { Group, GroupsService, UserPublic } from '../../groups.service';
import { GroupCardComponent } from '../../components/group-card/group-card';

@Component({
  selector: 'app-groups-page',
  imports: [
    GroupCardComponent,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './groups-page.html',
  styleUrl: './groups-page.scss',
})
export class GroupsPage {
  private readonly groupsService = inject(GroupsService);
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  protected readonly authenticated = this.oidc.authenticated;

  protected readonly groups = httpResource<Group[]>(() =>
    this.authenticated().isAuthenticated
      ? `${this.config.apiUrl()}/groups`
      : undefined,
  );

  protected readonly allUsers = httpResource<UserPublic[]>(() =>
    this.authenticated().isAuthenticated
      ? `${this.config.apiUrl()}/users`
      : undefined,
  );

  protected readonly showCreateForm = signal(false);
  protected readonly newGroupName = signal('');
  protected readonly isCreating = signal(false);

  protected createGroup(): void {
    const name = this.newGroupName().trim();
    if (!name) return;
    this.isCreating.set(true);
    this.groupsService.createGroup(name).subscribe({
      next: () => {
        this.newGroupName.set('');
        this.showCreateForm.set(false);
        this.isCreating.set(false);
        this.groups.reload();
      },
      error: () => this.isCreating.set(false),
    });
  }

  protected onGroupMutated(): void {
    this.groups.reload();
  }
}
```

- [ ] **Step 2: Create `groups-page.html`**

```html
<div class="groups-container">
  <div class="groups-header">
    <h1>Mis Grupos</h1>
    <button
      mat-flat-button
      color="primary"
      (click)="showCreateForm.set(!showCreateForm())"
    >
      <mat-icon>add</mat-icon>
      Nuevo grupo
    </button>
  </div>

  @if (showCreateForm()) {
    <div class="create-form">
      <mat-form-field appearance="outline">
        <mat-label>Nombre del grupo</mat-label>
        <input
          matInput
          [value]="newGroupName()"
          (input)="newGroupName.set($any($event.target).value)"
          (keydown.enter)="createGroup()"
          placeholder="Ej: Vacaciones 2026"
        />
      </mat-form-field>
      <button
        mat-flat-button
        color="primary"
        (click)="createGroup()"
        [disabled]="isCreating() || !newGroupName().trim()"
      >
        Crear
      </button>
      <button mat-button (click)="showCreateForm.set(false)">Cancelar</button>
    </div>
  }

  @if (groups.isLoading()) {
    <div class="loading">
      <mat-spinner diameter="48" aria-label="Cargando grupos…" />
    </div>
  } @else if (groups.error()) {
    <p role="alert">No se pudieron cargar los grupos.</p>
  } @else {
    <div class="groups-grid">
      @for (group of groups.value() ?? []; track group.id) {
        <app-group-card
          [group]="group"
          [allUsers]="allUsers.value() ?? []"
          (deleted)="onGroupMutated()"
          (renamed)="onGroupMutated()"
          (memberAdded)="onGroupMutated()"
        />
      } @empty {
        <p class="empty-state">
          No perteneces a ningún grupo todavía. ¡Crea el primero!
        </p>
      }
    </div>
  }
</div>
```

- [ ] **Step 3: Create `groups-page.scss`**

```scss
.groups-container {
  padding: 24px;
  max-width: 960px;
  margin: 0 auto;
}

.groups-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;

  h1 {
    margin: 0;
  }
}

.create-form {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;

  mat-form-field {
    flex: 1;
    min-width: 200px;
  }
}

.loading {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}

.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.empty-state {
  color: var(--mat-sys-on-surface-variant);
  text-align: center;
  padding: 48px 0;
}
```

- [ ] **Step 4: Create `groups-page.spec.ts`**

```typescript
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';

import { GroupsPage } from './groups-page';
import { GroupsService } from '../../groups.service';
import { ConfigService } from '../../../../core/config.service';

describe('GroupsPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupsPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        {
          provide: GroupsService,
          useValue: {
            createGroup: () => of({ id: 'g-1', name: 'New', member_count: 1 }),
            renameGroup: () => of({}),
            deleteGroup: () => of(undefined),
            addMember: () => of(undefined),
          },
        },
        {
          provide: ConfigService,
          useValue: { apiUrl: () => 'http://localhost:8000/api/v1' },
        },
        {
          provide: OidcSecurityService,
          useValue: {
            authenticated: signal({ isAuthenticated: true }),
          },
        },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(GroupsPage);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows page heading', () => {
    const fixture = TestBed.createComponent(GroupsPage);
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('h1')?.textContent,
    ).toContain('Mis Grupos');
  });
});
```

- [ ] **Step 5: Run frontend tests**

```bash
cd frontend && ng test --run-in-band 2>&1 | head -80
```

Expected: `GroupsPage` tests PASS alongside prior tests.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/features/groups/pages/groups-page/
git commit -m "feat: add GroupsPage"
```

---

## Task 9: Frontend — GroupDetailPage

**Files:**
- Create: `frontend/src/app/features/groups/pages/group-detail-page/group-detail-page.ts`
- Create: `frontend/src/app/features/groups/pages/group-detail-page/group-detail-page.html`
- Create: `frontend/src/app/features/groups/pages/group-detail-page/group-detail-page.scss`
- Create: `frontend/src/app/features/groups/pages/group-detail-page/group-detail-page.spec.ts`

Reads `:id` from the URL, fetches that group's members via `httpResource`, and renders them in a Material list.

- [ ] **Step 1: Create `group-detail-page.ts`**

```typescript
import { Component, computed, inject } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from '../../../../core/config.service';
import { Member } from '../../groups.service';

@Component({
  selector: 'app-group-detail-page',
  imports: [
    MatButtonModule,
    MatIconModule,
    MatListModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './group-detail-page.html',
  styleUrl: './group-detail-page.scss',
})
export class GroupDetailPage {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  private readonly groupId = toSignal(
    this.route.paramMap.pipe(map((p) => p.get('id') ?? '')),
    { initialValue: '' },
  );

  private readonly isAuthenticated = computed(
    () => this.oidc.authenticated().isAuthenticated,
  );

  protected readonly members = httpResource<Member[]>(() =>
    this.isAuthenticated() && this.groupId()
      ? `${this.config.apiUrl()}/groups/${this.groupId()}/members`
      : undefined,
  );

  protected goBack(): void {
    this.router.navigate(['/groups']);
  }
}
```

- [ ] **Step 2: Create `group-detail-page.html`**

```html
<div class="detail-container">
  <div class="detail-header">
    <button mat-icon-button (click)="goBack()" aria-label="Volver a grupos">
      <mat-icon>arrow_back</mat-icon>
    </button>
    <h1>Miembros del grupo</h1>
  </div>

  @if (members.isLoading()) {
    <div class="loading">
      <mat-spinner diameter="48" aria-label="Cargando miembros…" />
    </div>
  } @else if (members.error()) {
    <p role="alert">No se pudieron cargar los miembros.</p>
  } @else {
    <mat-list>
      @for (member of members.value() ?? []; track member.user_id) {
        <mat-list-item>
          <span matListItemTitle>{{ member.display_name }}</span>
          <span matListItemLine>{{ member.email }}</span>
        </mat-list-item>
      } @empty {
        <p>Este grupo no tiene miembros.</p>
      }
    </mat-list>
  }
</div>
```

- [ ] **Step 3: Create `group-detail-page.scss`**

```scss
.detail-container {
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
}

.detail-header {
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
```

- [ ] **Step 4: Create `group-detail-page.spec.ts`**

```typescript
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { GroupDetailPage } from './group-detail-page';
import { ConfigService } from '../../../../core/config.service';

describe('GroupDetailPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupDetailPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        {
          provide: ConfigService,
          useValue: { apiUrl: () => 'http://localhost:8000/api/v1' },
        },
        {
          provide: OidcSecurityService,
          useValue: {
            authenticated: signal({ isAuthenticated: true }),
          },
        },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(GroupDetailPage);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows page heading', () => {
    const fixture = TestBed.createComponent(GroupDetailPage);
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('h1')?.textContent,
    ).toContain('Miembros del grupo');
  });
});
```

- [ ] **Step 5: Run frontend tests**

```bash
cd frontend && ng test --run-in-band 2>&1 | head -80
```

Expected: `GroupDetailPage` tests PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/features/groups/pages/group-detail-page/
git commit -m "feat: add GroupDetailPage"
```

---

## Task 10: Wire routes, update header, update portal page

**Files:**
- Create: `frontend/src/app/features/groups/groups.routes.ts`
- Modify: `frontend/src/app/app.routes.ts`
- Modify: `frontend/src/app/shared/components/app-header/app-header.ts`
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.html`
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts`

- [ ] **Step 1: Create `frontend/src/app/features/groups/groups.routes.ts`**

```typescript
import { Routes } from '@angular/router';

export const groupsRoutes: Routes = [
  {
    path: '',
    title: 'Mis Grupos',
    loadComponent: () =>
      import('./pages/groups-page/groups-page').then((m) => m.GroupsPage),
  },
  {
    path: ':id',
    title: 'Detalle del Grupo',
    loadComponent: () =>
      import('./pages/group-detail-page/group-detail-page').then(
        (m) => m.GroupDetailPage,
      ),
  },
];
```

- [ ] **Step 2: Update `frontend/src/app/app.routes.ts`**

Replace the entire file:

```typescript
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./shared/components/app-shell/app-shell').then(
        (m) => m.AppShell,
      ),
    children: [
      {
        path: '',
        loadChildren: () =>
          import('./features/portal/portal.routes').then(
            (m) => m.portalRoutes,
          ),
      },
      {
        path: 'groups',
        loadChildren: () =>
          import('./features/groups/groups.routes').then(
            (m) => m.groupsRoutes,
          ),
      },
    ],
  },
];
```

- [ ] **Step 3: Update `navItems` in `frontend/src/app/shared/components/app-header/app-header.ts`**

Find the line:

```typescript
  protected readonly navItems = [{ label: 'Portal', path: '/' }];
```

Replace it with:

```typescript
  protected readonly navItems = [
    { label: 'Portal', path: '/' },
    { label: 'Grupos', path: '/groups' },
  ];
```

- [ ] **Step 4: Replace `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`**

```typescript
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-portal-page',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatIconModule],
  templateUrl: './portal-page.html',
  styleUrl: './portal-page.scss',
})
export class PortalPage {}
```

- [ ] **Step 5: Replace `frontend/src/app/features/portal/pages/portal-page/portal-page.html`**

```html
<main class="portal-container">
  <mat-card class="feature-card">
    <mat-card-header>
      <mat-icon mat-card-avatar>group</mat-icon>
      <mat-card-title>Mis Grupos</mat-card-title>
      <mat-card-subtitle>
        Gestiona tus grupos de gastos compartidos
      </mat-card-subtitle>
    </mat-card-header>
    <mat-card-actions>
      <a mat-flat-button color="primary" routerLink="/groups">
        Ir a grupos
      </a>
    </mat-card-actions>
  </mat-card>
</main>
```

- [ ] **Step 6: Replace `frontend/src/app/features/portal/pages/portal-page/portal-page.scss`**

```scss
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
```

- [ ] **Step 7: Replace `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts`**

```typescript
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { PortalPage } from './portal-page';

describe('PortalPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PortalPage],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(PortalPage);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows groups navigation card', () => {
    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).textContent,
    ).toContain('Mis Grupos');
  });
});
```

- [ ] **Step 8: Run all frontend tests**

```bash
cd frontend && ng test --run-in-band 2>&1 | head -100
```

Expected: all tests PASS.

- [ ] **Step 9: Commit**

```bash
git add \
  frontend/src/app/features/groups/groups.routes.ts \
  frontend/src/app/app.routes.ts \
  frontend/src/app/shared/components/app-header/app-header.ts \
  frontend/src/app/features/portal/pages/portal-page/
git commit -m "feat: wire groups routes, update nav and portal page"
```

---

## Task 11: README update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Group Management feature section**

In `README.md`, find the existing `### Portal (\`/\`)` section under `## Features`. Add the new section immediately after it:

```markdown
### Group Management (`/groups`, `/groups/:id`)

Allows authenticated users to manage expense groups and their members.

**Pages:**
- `GroupsPage` — lists all groups the user belongs to; create new groups inline; each `GroupCardComponent` supports rename (edit-in-place), delete, and inline add-member
- `GroupDetailPage` — lists all members of a group with their display name and email

**Components:**
- `GroupCardComponent` — card with name, member count, edit/delete/add-member/detail actions
- `AddMemberFormComponent` — select from all app users, filtered to exclude existing members; lazy-fetches the group's current members when opened

**Service:** `GroupsService` — mutation methods (create, rename, delete, add member)

**API endpoints used:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/users` | All registered users (for add-member selector) |
| GET | `/api/v1/groups` | Groups the current user belongs to |
| POST | `/api/v1/groups` | Create group (creator auto-added as member) |
| PATCH | `/api/v1/groups/:id` | Rename group |
| DELETE | `/api/v1/groups/:id` | Delete group (cascades expenses) |
| POST | `/api/v1/groups/:id/members` | Add a user to the group |
| GET | `/api/v1/groups/:id/members` | List all members of the group |
```

- [ ] **Step 2: Run all backend tests one final time to confirm nothing regressed**

```bash
cd backend && uv run pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add Group Management feature to README"
```
