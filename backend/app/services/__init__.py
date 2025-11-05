"""
Services 模块

提供各种外部服务的接口：
- ASR (Automatic Speech Recognition): OpenAI Whisper / 本地 Whisper
- TTS (Text-to-Speech): ElevenLabs
- Diarization (Speaker Recognition): pyannote.audio
"""

# ASR 服务（新接口）
from .asr_base import (
    ASRService,
    TranscriptionResult,
    TranscriptSegment,
    WordTimestamp,
)
from .asr_factory import (
    get_asr_service,
    transcribe_audio,
)
from .asr_openai_adapter import openai_whisper_service

# ASR 工具函数（音频转换）
from .asr_openai import webm_to_wav_16k_mono

# TTS 服务
from .tts_elevenlabs import (
    synth_and_stream_free,
    synth_and_stream_paid,
)

# Diarization 服务
from .diarization import diarization_service

__all__ = [
    # ASR - 服务接口
    "ASRService",
    "TranscriptionResult",
    "TranscriptSegment",
    "WordTimestamp",
    "get_asr_service",
    "transcribe_audio",
    "openai_whisper_service",
    # ASR - 工具函数
    "webm_to_wav_16k_mono",
    # TTS
    "synth_and_stream_free",
    "synth_and_stream_paid",
    # Diarization
    "diarization_service",
]



