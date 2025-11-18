import tempfile, os
import ffmpeg
import httpx
from ..config import settings

def webm_to_wav_16k_mono(webm_path: str) -> str:
    """把 webm/opus 转 16k 单声道 wav，返回 wav 路径（调用方负责删除）"""
    # 验证输入文件
    if not os.path.exists(webm_path):
        raise FileNotFoundError(f"Input file not found: {webm_path}")
    
    file_size = os.path.getsize(webm_path)
    if file_size == 0:
        raise ValueError(f"Input file is empty: {webm_path}")
    
    print(f"[ffmpeg] Converting {webm_path} ({file_size} bytes) to WAV...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_file:
        try:
            (
                ffmpeg
                .input(webm_path)
                # ❌ 移除音频滤波（可能引入失真，影响 Whisper 识别）
                .output(
                    wav_file.name, 
                    ac=1,           # 单声道
                    ar="16000",     # 16kHz 采样率（Whisper 推荐）
                    format="wav",
                    acodec="pcm_s16le",  # 16位 PCM（无损）
                    loglevel="error"     # 只显示错误
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # ✅ 验证转换后的 WAV 文件
            wav_size = os.path.getsize(wav_file.name)
            if wav_size == 0:
                raise ValueError(f"Converted WAV file is empty: {wav_file.name}")
            
            # 检查 WAV 文件头（应该是 "RIFF"）
            with open(wav_file.name, "rb") as f:
                wav_header = f.read(4)
                if wav_header != b'RIFF':
                    raise ValueError(f"Invalid WAV file header: {wav_header.hex()}")
            
            print(f"[ffmpeg] Conversion successful: {wav_file.name} ({wav_size} bytes)")
            return wav_file.name
        except ffmpeg.Error as e:
            # 打印详细错误信息
            print(f"[ffmpeg] ERROR converting {webm_path}:")
            print(f"[ffmpeg] stdout: {e.stdout.decode('utf-8', errors='ignore') if e.stdout else 'N/A'}")
            print(f"[ffmpeg] stderr: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else 'N/A'}")
            # 清理失败的输出文件
            if os.path.exists(wav_file.name):
                try:
                    os.unlink(wav_file.name)
                except:
                    pass
            raise RuntimeError(f"ffmpeg conversion failed: {e.stderr.decode('utf-8', errors='ignore')[:200] if e.stderr else 'Unknown error'}")

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
