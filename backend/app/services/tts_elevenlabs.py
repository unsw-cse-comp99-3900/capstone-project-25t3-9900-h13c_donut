import os
import httpx
import asyncio
from typing import AsyncGenerator
from app.core.pubsub import channel

ELEVEN_API = os.getenv("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1")
ELEVEN_KEY = os.getenv("ELEVENLABS_API_KEY", "")

VOICE_ID_AMERICAN  = os.getenv("VOICE_ID_AMERICAN",  "EXAVITQu4vr4xnSDxMaL")
VOICE_ID_AUSTRALIA = os.getenv("VOICE_ID_AUSTRALIA", "IKne3meq5aSn9XLyUdCD")
VOICE_ID_BRITISH   = os.getenv("VOICE_ID_BRITISH",   "JBFqnCBsd6RMkjVDRZzb")
VOICE_ID_CHINESE   = os.getenv("VOICE_ID_CHINESE",   "hkfHEbBvdQFNX4uWHqRF")
VOICE_ID_INDIA     = os.getenv("VOICE_ID_INDIA",     "kL06KYMvPY56NluIQ72m")

def _pick_voice_id_by_accent(accent: str) -> str:
    a = (accent or "").lower()
    if "australia" in a: return VOICE_ID_AUSTRALIA
    if "british"   in a: return VOICE_ID_BRITISH
    if "chinese"   in a: return VOICE_ID_CHINESE
    if "india"     in a: return VOICE_ID_INDIA
    return VOICE_ID_AMERICAN
    # return "21m00Tcm4TlvDq8ikWAM"

async def _stream_elevenlabs(text: str, voice_id: str) -> AsyncGenerator[bytes, None]:
    if not text or not text.strip():
        print("[tts] skip empty text")
        return
    if not ELEVEN_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is missing")

    url = f"{ELEVEN_API}/text-to-speech/{voice_id}/stream?optimize_streaming_latency=2"
    headers = {
        "xi-api-key": ELEVEN_KEY,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.7},
    }

    print(f"[tts] HTTP POST {url} voice={voice_id}")
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes():
                if chunk:
                    yield chunk
                await asyncio.sleep(0)

async def _synth_and_stream_common(conv_id: str, text: str, accent: str):
    voice_id = _pick_voice_id_by_accent(accent)
    # 1) 通知前端开始
    await channel.pub_tts_json(conv_id, {"type": "start", "mime": "audio/mpeg"})
    print(f"[tts→ws] start -> {conv_id}")

    try:
        # 2) 流式分片
        got_any = False
        async for chunk in _stream_elevenlabs(text, voice_id):
            got_any = True
            await channel.pub_tts_bytes(conv_id, chunk)
        print(f"[tts] stream done, got_any={got_any}")
    finally:
        # 3) 通知前端结束
        await channel.pub_tts_json(conv_id, {"type": "stop"})
        print(f"[tts→ws] stop  -> {conv_id}")

async def synth_and_stream_free(conv_id: str, text: str, accent: str):
    await _synth_and_stream_common(conv_id, text, accent)

async def synth_and_stream_paid(conv_id: str, text: str, accent: str):
    await _synth_and_stream_common(conv_id, text, accent)
