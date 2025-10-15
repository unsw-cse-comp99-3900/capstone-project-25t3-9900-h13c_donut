import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.transcript import Transcript
from app.schemas.conversation import (
    ConversationListOut, ConversationItem,
    ConversationDetailOut, ConversationDetail,
    TranscriptOut, ConversationTitleIn,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("", response_model=dict)
async def list_conversations(
    user: User = Depends(get_current_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
):
    # 统计总数
    total = await Conversation.filter(user=user).count()
    # 拉分页
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

@router.get("/{cid}", response_model=dict)
async def get_conversation_detail(
    cid: str,
    user: User = Depends(get_current_user),
):
    c = await Conversation.get_or_none(id=cid, user=user)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    # 拉取转写（目前可能为空；后续由 WS 写入）
    trs = await Transcript.filter(conversation_id=c.id).order_by("seq")
    transcripts = [{
        "seq": t.seq, "isFinal": t.is_final,
        "startMs": t.start_ms, "endMs": t.end_ms, "text": t.text
    } for t in trs]
    # 音频 URL（S1 可为 None；S2 再接对象存储）
    audio_url = None
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
            "audioUrl": audio_url,
        }
    }

@router.patch("/{cid}", response_model=dict)
async def rename_conversation(
    cid: str,
    body: ConversationTitleIn,
    user: User = Depends(get_current_user),
):
    c = await Conversation.get_or_none(id=cid, user=user)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    c.title = body.title.strip()[:80]
    await c.save()
    return {"success": True, "data": {"id": str(c.id), "title": c.title}}
