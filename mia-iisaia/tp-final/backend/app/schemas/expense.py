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
