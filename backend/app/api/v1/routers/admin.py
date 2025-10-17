from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

class VerifyKeyIn(BaseModel):
    key: str

@router.post("/verify-key")
async def verify_key(body: VerifyKeyIn):
    ok = (body.key == "SECRET123")
    return {"success": True, "data": {"ok": ok}}
