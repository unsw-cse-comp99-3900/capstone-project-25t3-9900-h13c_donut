import httpx
import asyncio
from typing import AsyncGenerator
from app.core.pubsub import channel
from app.config import settings  # ✅ 统一使用 config.py 配置

def _pick_voice_id_by_accent(accent: str) -> str:
    """
    根据口音选择对应的 Voice ID
    
    配置优先级：
    1. .env 文件中的 VOICE_ID_AMERICAN 等
    2. config.py 中的硬编码默认值
    """
    a = (accent or "").lower()
    if "australia" in a: 
        return settings.voice_id_australia
    if "british" in a: 
        return settings.voice_id_british
    if "chinese" in a: 
        return settings.voice_id_chinese
    if "india" in a: 
        return settings.voice_id_india
    # 默认美式英语
    return settings.voice_id_american

async def _stream_elevenlabs(text: str, voice_id: str) -> AsyncGenerator[bytes, None]:
    """
    调用 ElevenLabs API 进行流式 TTS
    
    配置来源：app.config.settings
    - eleven_api_base: API 基础 URL
    - eleven_api_key: API 密钥
    """
    if not text or not text.strip():
        print("[tts] skip empty text")
        return
    if not settings.eleven_api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is missing")

    url = f"{settings.eleven_api_base}/text-to-speech/{voice_id}/stream?optimize_streaming_latency=2"
    headers = {
        "xi-api-key": settings.eleven_api_key,
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
