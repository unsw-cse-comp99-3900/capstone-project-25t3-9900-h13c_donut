"""
ASR 服务工厂

根据配置自动选择可用的 ASR 服务
"""
from typing import Optional
from .asr_base import ASRService
from .asr_openai_adapter import openai_whisper_service
from .local_asr import local_whisper_service
from ..config import settings


def get_asr_service(prefer_local: bool = None) -> ASRService:
    """
    获取可用的 ASR 服务
    
    参数：
    - prefer_local: 是否优先使用本地 Whisper（如果可用）
                    如果为 None，则使用配置文件中的 USE_LOCAL_WHISPER 设置
    
    返回：
    - ASRService: 可用的 ASR 服务实例
    
    策略：
    1. 如果 prefer_local=True 且本地 Whisper 可用 → 使用本地 Whisper
    2. 否则使用 OpenAI Whisper API
    3. 如果都不可用 → 抛出异常
    """
    
    # 如果未指定 prefer_local，使用配置中的设置
    if prefer_local is None:
        prefer_local = settings.use_local_whisper
    
    # 优先使用本地 Whisper（如果可用）
    if prefer_local and local_whisper_service.is_available():
        print(f"[ASR] Using {local_whisper_service.name}")
        return local_whisper_service
    
    # 回退到 OpenAI API
    if openai_whisper_service.is_available():
        print(f"[ASR] Using {openai_whisper_service.name}")
        return openai_whisper_service
    
    raise RuntimeError(
        "No ASR service available. Please configure OPENAI_API_KEY or deploy local Whisper."
    )


# 便捷函数：直接转录音频
async def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
    word_timestamps: bool = False,
    prefer_local: bool = None
) -> 'TranscriptionResult':
    """
    便捷函数：使用可用的 ASR 服务转录音频
    
    参数：
    - audio_path: WAV 文件路径
    - language: 可选的语言提示
    - word_timestamps: 是否返回词级别时间戳
    - prefer_local: 是否优先使用本地 Whisper（None=使用配置文件设置）
    
    返回：
    - TranscriptionResult: 转录结果
    """
    service = get_asr_service(prefer_local=prefer_local)
    return await service.transcribe(
        audio_path=audio_path,
        language=language,
        word_timestamps=word_timestamps
    )



