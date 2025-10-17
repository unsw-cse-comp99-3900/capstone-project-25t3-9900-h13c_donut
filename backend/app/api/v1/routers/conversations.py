import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.transcript import Transcript

router = APIRouter(prefix="/conversations", tags=["conversations"])

# ===== Schemas =====
class ConversationTitleIn(BaseModel):
    title: str

class CreateConversationIn(BaseModel):
    title: str | None = None

class AppendSegmentIn(BaseModel):
    startMs: int | None = None
    endMs: int | None = None
    text: str
    audioUrl: str | None = None

# ===== Routes =====
@router.get("", response_model=dict)
async def list_conversations(
    user: User = Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    total = await Conversation.filter(user=user).count()
    rows = await Conversation.filter(user=user).order_by("-started_at").offset(offset).limit(limit)
    items = []
    for c in rows:
        items.append({
            "id": str(c.id),
            "title": c.title,
            "accent": c.accent,
            "model": c.model,
            "startedAt": c.started_at.isoformat() + "Z",
            "endedAt": c.ended_at.isoformat() + "Z" if c.ended_at else None,
            "durationSec": c.duration_sec,
        })
    return {"success": True, "data": {"items": items, "offset": offset, "limit": limit, "total": total}}

@router.post("", response_model=dict)
async def create_conversation(body: CreateConversationIn, user: User = Depends(get_current_user)):
    now = dt.datetime.utcnow()
    c = await Conversation.create(
        user=user,
        accent="us",
        model="free",
        started_at=now,
        title=(body.title.strip() if body.title else None),
    )
    return {"success": True, "data": {"id": str(c.id), "title": c.title or "", "createdAtMs": int(now.timestamp()*1000)}}

@router.get("/{cid}", response_model=dict)
async def get_conversation_detail(cid: str, user: User = Depends(get_current_user)):
    c = await Conversation.get_or_none(id=cid, user=user)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    trs = await Transcript.filter(conversation_id=c.id).order_by("seq")
    transcripts = [{
        "seq": t.seq,
        "isFinal": t.is_final,
        "startMs": t.start_ms,
        "endMs": t.end_ms,
        "text": t.text,
        "audioUrl": t.audio_url,
    } for t in trs]
    return {
        "success": True,
        "data": {
            "conversation": {
                "id": str(c.id),
                "title": c.title,
                "accent": c.accent,
                "model": c.model,
                "startedAt": c.started_at.isoformat() + "Z",
                "endedAt": c.ended_at.isoformat() + "Z" if c.ended_at else None,
                "durationSec": c.duration_sec,
            },
            "transcripts": transcripts,
            "audioUrl": None,
        }
    }

@router.patch("/{cid}", response_model=dict)
async def rename_conversation(cid: str, body: ConversationTitleIn, user: User = Depends(get_current_user)):
    c = await Conversation.get_or_none(id=cid, user=user)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    c.title = (body.title or "").strip()[:80]
    await c.save()
    return {"success": True, "data": {"id": str(c.id), "title": c.title}}

@router.delete("/{cid}", response_model=dict)
async def delete_conversation(cid: str, user: User = Depends(get_current_user)):
    c = await Conversation.get_or_none(id=cid, user=user)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    # 先删 transcript，再删 conversation（外键已级联，但手动更明确）
    await Transcript.filter(conversation_id=c.id).delete()
    await c.delete()
    return {"success": True, "data": {"id": cid, "deleted": True}}

@router.post("/{cid}/segments", response_model=dict)
async def append_segment(cid: str, body: AppendSegmentIn, user: User = Depends(get_current_user)):
    c = await Conversation.get_or_none(id=cid, user=user)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    seq = await Transcript.filter(conversation_id=c.id).count() + 1
    t = await Transcript.create(
        conversation_id=c.id,
        seq=seq,
        is_final=True,
        start_ms=body.startMs,
        end_ms=body.endMs,
        text=body.text,
        audio_url=body.audioUrl,
    )
    return {"success": True, "data": {"id": f"s_{seq}", "seq": seq, "startMs": t.start_ms, "endMs": t.end_ms, "text": t.text, "audioUrl": t.audio_url}}
