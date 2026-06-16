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
    await _make_user(db, "sub-pm-a", "alice@pm.com", "Alice")
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
    await _make_user(db, "sub-gm-a", "alice@gm.com", "Alice")
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
