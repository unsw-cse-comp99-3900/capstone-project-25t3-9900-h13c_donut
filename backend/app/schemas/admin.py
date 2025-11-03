# app/schemas/admin.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# ========== 通用返回模型 ==========
class AdminUserBase(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: Literal["user", "admin"]
    createdAt: str = Field(alias="created_at")

    class Config:
        populate_by_name = True


class AdminUserListOut(BaseModel):
    items: List[AdminUserBase]
    offset: int
    limit: int
    total: int


class AdminUserDetailOut(BaseModel):
    user: AdminUserBase


# ========== 入参模型 ==========
class AdminUserUpdateIn(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Literal["user", "admin"]] = None


class AdminResetPasswordIn(BaseModel):
    newPassword: str = Field(min_length=6)
