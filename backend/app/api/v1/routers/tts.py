"""
TTS HTTP API Router

提供简单的 HTTP TTS 接口，用于流式传译
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
import asyncio
import numpy as np

router = APIRouter()


class TtsRequest(BaseModel):
    text: str
    accent: str = "American English"
    model: str = "free"  # "free" = MelonTTS (本地), "paid" = ElevenLabs (API)


async def _generate_melotts_audio(text: str, accent: str) -> bytes:
    """
    使用 MelonTTS 生成音频（本地模型）
    
    Args:
        text: 要合成的文本
        accent: 口音类型
    
    Returns:
        bytes: MP3 音频数据
    """
    from app.services.tts_elevenlabs import (
        _get_melotts_model,
        _accent_to_speaker_id,
        _get_melotts_executor
    )
    
    # 根据口音确定语言模型
    accent_lower = (accent or "").lower()
    if "chinese" in accent_lower or "china" in accent_lower:
        language = 'ZH'
    else:
        language = 'EN'
    
    # 获取模型（使用缓存）
    model, speaker_ids = _get_melotts_model(language)
    speaker_id = _accent_to_speaker_id(accent, speaker_ids, language)
    
    print(f"[TTS API][MelonTTS] 合成语音: text='{text[:50]}...', accent={accent}, speaker_id={speaker_id}, language={language}")
    
    # 在线程池中生成音频
    executor = _get_melotts_executor()
    loop = asyncio.get_event_loop()
    
    def synthesize():
        """在线程池中执行的同步合成函数"""
        audio = model.tts_to_file(
            text=text,
            speaker_id=speaker_id,
            output_path=None,
            speed=1.0,
            quiet=True
        )
        sample_rate = model.hps.data.sampling_rate
        return audio, sample_rate
    
    audio, sample_rate = await loop.run_in_executor(executor, synthesize)
    
    # 转换为 MP3 字节
    audio = np.clip(audio, -1.0, 1.0)
    
    try:
        from pydub import AudioSegment
        
        # 转换为 16-bit PCM
        audio_int16 = (audio * 32767.0).astype(np.int16)
        
        # 创建 AudioSegment
        audio_segment = AudioSegment(
            audio_int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
        
        # 导出为 MP3
        mp3_buffer = io.BytesIO()
        audio_segment.export(mp3_buffer, format="mp3", bitrate="128k")
        mp3_buffer.seek(0)
        audio_bytes = mp3_buffer.read()
        print(f"[TTS API][MelonTTS] MP3 转换完成，大小: {len(audio_bytes)} bytes")
        return audio_bytes
    except ImportError:
        # 退化到 WAV
        import soundfile as sf
        audio = audio.astype(np.float32)
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio, sample_rate, format='WAV', subtype='PCM_16')
        wav_buffer.seek(0)
        audio_bytes = wav_buffer.read()
        print(f"[TTS API][MelonTTS] WAV 转换完成，大小: {len(audio_bytes)} bytes")
        return audio_bytes


async def _generate_elevenlabs_audio(text: str, accent: str) -> bytes:
    """
    使用 ElevenLabs 生成音频（API）
    
    Args:
        text: 要合成的文本
        accent: 口音类型
    
    Returns:
        bytes: MP3 音频数据
    """
    from app.services.tts_elevenlabs import _stream_elevenlabs, _pick_voice_id_by_accent
    
    voice_id = _pick_voice_id_by_accent(accent)
    
    print(f"[TTS API][ElevenLabs] 合成语音: text='{text[:50]}...', accent={accent}, voice_id={voice_id}")
    
    # 收集音频到内存
    audio_chunks = []
    async for chunk in _stream_elevenlabs(text, voice_id):
        audio_chunks.append(chunk)
    
    # 合并音频数据
    audio_data = b''.join(audio_chunks)
    print(f"[TTS API][ElevenLabs] 生成完成，大小: {len(audio_data)} bytes")
    return audio_data


@router.post("/synthesize")
async def synthesize_tts(req: TtsRequest):
    """
    合成 TTS 音频（用于流式传译）
    
    参数：
    - text: 要合成的文本
    - accent: 口音（American English, British English, 等）
    - model: 模型选择
      - "free": MelonTTS 本地模型（免费，较慢）
      - "paid": ElevenLabs API（付费，更快更自然）
    
    返回：
    - audio/mpeg 音频流
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    print(f"[TTS API] 收到请求: model={req.model}, accent={req.accent}, text_len={len(req.text)}")
    
    try:
        # 根据 model 参数选择 TTS 服务
        if req.model == "paid":
            audio_data = await _generate_elevenlabs_audio(req.text, req.accent)
        else:  # "free" 或其他值都使用 MelonTTS
            audio_data = await _generate_melotts_audio(req.text, req.accent)
        
        print(f"[TTS API] 生成完成: model={req.model}, size={len(audio_data)} bytes")
        
        # 返回音频流
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=tts.mp3",
                "Cache-Control": "no-cache",
            }
        )
    except Exception as e:
        print(f"[TTS API] ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

