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
async def deactivate_category(
    category_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    category = await category_service.deactivate(db, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return category
