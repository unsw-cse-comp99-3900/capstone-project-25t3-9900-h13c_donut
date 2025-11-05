"""
TTS HTTP API Router

提供简单的 HTTP TTS 接口，用于流式传译
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.tts_elevenlabs import _stream_elevenlabs, _pick_voice_id_by_accent
import io

router = APIRouter()


class TtsRequest(BaseModel):
    text: str
    accent: str = "American English"
    model: str = "free"  # "free" or "paid"（暂时不区分，都使用相同的 TTS）


@router.post("/synthesize")
async def synthesize_tts(req: TtsRequest):
    """
    合成 TTS 音频（用于流式传译）
    
    参数：
    - text: 要合成的文本
    - accent: 口音（American English, British English, 等）
    - model: 模型（free 或 paid）
    
    返回：
    - audio/mpeg 音频流
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    print(f"[TTS API] Synthesizing: accent={req.accent}, model={req.model}, text_len={len(req.text)}")
    
    # 选择 voice_id
    voice_id = _pick_voice_id_by_accent(req.accent)
    
    # 收集音频到内存
    audio_chunks = []
    async for chunk in _stream_elevenlabs(req.text, voice_id):
        audio_chunks.append(chunk)
    
    # 合并音频数据
    audio_data = b''.join(audio_chunks)
    
    print(f"[TTS API] Generated {len(audio_data)} bytes")
    
    # 返回音频流
    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=tts.mp3",
            "Cache-Control": "no-cache",
        }
    )

