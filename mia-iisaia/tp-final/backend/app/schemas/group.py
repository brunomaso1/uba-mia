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
