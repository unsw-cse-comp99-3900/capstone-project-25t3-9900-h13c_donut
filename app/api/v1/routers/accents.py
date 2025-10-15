# app/api/v1/routers/accents.py
from fastapi import APIRouter

router = APIRouter(prefix="/accents", tags=["accents"])

@router.get("")
async def get_accents():
    return {"success": True, "data": {"accents": [
        {"code": "us", "label": "American English (US)", "available": True}
    ]}}
