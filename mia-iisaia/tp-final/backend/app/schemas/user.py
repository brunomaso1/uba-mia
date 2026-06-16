import uuid
from datetime import datetime

from pydantic import BaseModel


class UserRead(BaseModel):
    id: uuid.UUID
    keycloak_sub: str
    display_name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    id: uuid.UUID
    display_name: str
    email: str

    model_config = {"from_attributes": True}
