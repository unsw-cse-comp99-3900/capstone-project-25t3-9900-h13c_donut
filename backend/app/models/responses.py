"""
Response models for API standardization
"""

from pydantic import BaseModel, Field#修改
from typing import Any, Optional
from datetime import datetime
import uuid

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    requestId: str = Field(default_factory=lambda: str(uuid.uuid4()))#修改
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())#修改

class SuccessResponse(BaseResponse):
    """Success response model"""
    success: bool = True
    data: Any

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: str
    code: Optional[str] = None

class WebSocketMessage(BaseModel):
    """Base WebSocket message model"""
    type: str
    requestId: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())#修改

class InitMessage(WebSocketMessage):
    """Initialize session message"""
    type: str = "init"
    sessionId: Optional[str] = None
    accent: str = "us"  # Default to US English
    model: str = "free"  # free or paid

class AudioMessage(WebSocketMessage):
    """Audio data message"""
    type: str = "audio"
    data: str  # Base64 encoded audio data
    sequence: int = 0

class StopMessage(WebSocketMessage):
    """Stop recording message"""
    type: str = "stop"

class PartialTranscriptMessage(WebSocketMessage):
    """Partial transcript message"""
    type: str = "partial"
    text: str
    sequence: int
    startMs: Optional[int] = None
    endMs: Optional[int] = None

class FinalTranscriptMessage(WebSocketMessage):
    """Final transcript message"""
    type: str = "final"
    text: str
    segments: list = []
    confidence: Optional[float] = None

class TTSChunkMessage(WebSocketMessage):
    """TTS audio chunk message"""
    type: str = "tts_chunk"
    bytes_b64: str  # Base64 encoded audio data
    seq: int  # 序列号
    size: int  # 数据大小
    isLast: bool = False

class DoneMessage(WebSocketMessage):
    """Session complete message"""
    type: str = "done"
    sessionId: str
    totalDuration: Optional[int] = None
    audioUrl: Optional[str] = None

class ErrorMessage(WebSocketMessage):
    """Error message"""
    type: str = "error"
    error: str
    code: Optional[str] = None

class HeartbeatMessage(WebSocketMessage):
    """Heartbeat message"""
    type: str = "ping"

class HeartbeatResponse(WebSocketMessage):
    """Heartbeat response"""
    type: str = "pong"


