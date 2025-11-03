# app/schemas/key.py
from pydantic import BaseModel
from typing import Optional

class VerifyKeyIn(BaseModel):
    key: str  # 用户输入的明文密钥

class VerifyKeyOut(BaseModel):
    ok: bool
    message: Optional[str] = None
