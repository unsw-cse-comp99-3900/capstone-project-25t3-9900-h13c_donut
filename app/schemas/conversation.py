from pydantic import BaseModel
from typing import Optional, List

class ConversationItem(BaseModel):
    id: str
    title: Optional[str] = None
    accent: str
    model: str
    startedAt: str
    endedAt: Optional[str] = None
    durationSec: Optional[int] = None

class ConversationListOut(BaseModel):
    items: List[ConversationItem]
    offset: int
    limit: int
    total: int

class ConversationDetail(BaseModel):
    id: str
    title: Optional[str] = None
    accent: str
    model: str
    startedAt: str
    endedAt: Optional[str] = None
    durationSec: Optional[int] = None

class TranscriptOut(BaseModel):
    seq: int
    isFinal: bool
    startMs: int | None = None
    endMs: int | None = None
    text: str

class ConversationDetailOut(BaseModel):
    conversation: ConversationDetail
    transcripts: list[TranscriptOut]
    audioUrl: str | None = None

class ConversationTitleIn(BaseModel):
    title: str
