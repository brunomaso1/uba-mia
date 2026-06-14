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
