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
