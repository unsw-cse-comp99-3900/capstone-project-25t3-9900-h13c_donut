import tempfile, os
import ffmpeg
import httpx
from ..config import settings

def webm_to_wav_16k_mono(webm_path: str) -> str:
    """把 webm/opus 转 16k 单声道 wav，返回 wav 路径（调用方负责删除）"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_file:
        (
            ffmpeg
            .input(webm_path)
            .output(wav_file.name, ac=1, ar="16000", format="wav")
            .overwrite_output()
            .run(quiet=True)
        )
        return wav_file.name

async def transcribe_wav_via_url(wav_path: str) -> str:
    """
    通过 HTTP 直连 WHISPER_API_URL 调 ASR：
      POST multipart/form-data:
        - model=settings.whisper_model
        - file=@wav (audio/wav)
        - response_format=verbose_json
      头：Authorization: Bearer OPENAI_API_KEY
    """
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    data = {
        "model": settings.whisper_model,
        "response_format": "verbose_json",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        with open(wav_path, "rb") as f:
            files = {"file": ("audio.wav", f, "audio/wav")}
            resp = await client.post(settings.whisper_api_url, headers=headers, data=data, files=files)
        resp.raise_for_status()
        js = resp.json()
        return (js.get("text") or "").strip()
