# app/api/v1/routers/session.py
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.api.v1.deps import get_current_user
from app.models.conversation import Conversation
from app.models.user import User

router = APIRouter(prefix="/session", tags=["session"])

class CreateSessionIn(BaseModel):
    accent: str = Field(pattern="^(us)$")  # S1 仅 us

@router.post("")
async def create_session(body: CreateSessionIn, user: User = Depends(get_current_user)):
    if body.accent != "us":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only 'us' supported in Sprint 1")
    conv = await Conversation.create(
        user=user,
        accent="us",
        model="free",
        started_at=dt.datetime.utcnow(),
        title=None,
    )
    return {"success": True,
            "data": {"sessionId": str(conv.id), "accent": "us", "model": "free",
                     "createdAt": conv.started_at.isoformat() + "Z"}}
