# app/schemas/license_key.py
from __future__ import annotations
from pydantic import BaseModel, Field, constr
from typing import List, Optional

class BatchGenerateIn(BaseModel):
    count: int = Field(ge=1, le=200, description="要生成的密钥数量，最大200")
    keyType: constr(strip_whitespace=True, min_length=1, max_length=16) = "paid"
    expireDays: Optional[int] = Field(default=None, ge=1, le=3650, description="多少天后过期；None表示不过期")
    prefix: Optional[constr(strip_whitespace=True, min_length=1, max_length=8)] = Field(
        default="FAT", description="密钥前缀，便于识别渠道/环境"
    )

class GeneratedKeyItem(BaseModel):
    id: str
    key: str
    keyType: str
    expiresAt: Optional[str] = None

class BatchGenerateOut(BaseModel):
    keys: List[GeneratedKeyItem]

class VerifyKeyIn(BaseModel):
    key: str
    consume: bool = False
