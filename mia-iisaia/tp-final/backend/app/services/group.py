import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User


async def get(db: AsyncSession, group_id: uuid.UUID) -> Group | None:
    result = await db.execute(select(Group).where(Group.id == group_id))
    return result.scalar_one_or_none()


async def is_member(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None


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


async def add_member(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
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
