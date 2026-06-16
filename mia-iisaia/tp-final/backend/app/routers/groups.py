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
    if not await group_service.get(db, group_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    if not await group_service.is_member(db, group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group"
        )
    group = await group_service.rename(db, group_id, body.name)
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
    if not await group_service.get(db, group_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    if not await group_service.is_member(db, group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group"
        )
    await group_service.delete(db, group_id)


@router.post("/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_member(
    group_id: uuid.UUID,
    body: AddMemberBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await group_service.get(db, group_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    if not await group_service.is_member(db, group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group"
        )
    ok = await group_service.add_member(db, group_id, body.user_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.get("/{group_id}/members", response_model=list[MemberRead])
async def list_members(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await group_service.get(db, group_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    if not await group_service.is_member(db, group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group"
        )
    rows = await group_service.list_members(db, group_id)
    return [
        MemberRead(
            user_id=row.User.id,
            display_name=row.User.display_name,
            email=row.User.email,
            joined_at=row.joined_at,
        )
        for row in rows
    ]
