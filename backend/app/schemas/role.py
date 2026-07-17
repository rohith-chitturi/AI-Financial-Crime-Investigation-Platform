from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class RoleBase(BaseModel):
    name: str
    permissions: list[str] = []

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: UUID

    class Config:
        from_attributes = True
