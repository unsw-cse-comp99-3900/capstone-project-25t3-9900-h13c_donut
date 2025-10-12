"""
TTS领域模型

定义了TTS系统中的核心数据结构，使用Pydantic进行数据验证。
所有模型都是不可变的（frozen=True），确保线程安全。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class AudioFormat(str, Enum):
    """支持的音频输出格式"""
    MP3_44100_128 = "mp3_44100_128"
    MP3_44100_192 = "mp3_44100_192"
    PCM_16000 = "pcm_16000"
    PCM_22050 = "pcm_22050"
    PCM_24000 = "pcm_24000"
    PCM_44100 = "pcm_44100"


class TTSProvider(str, Enum):
    """TTS服务提供商"""
    ELEVENLABS = "elevenlabs"
    COQUI = "coqui"  # 预留用于Coqui XTTS-v2


class VoiceSettings(BaseModel):
    """
    语音合成参数配置
    
    Attributes:
        stability: 稳定性 [0.0-1.0]，越高越稳定但可能较单调
        similarity_boost: 相似度增强 [0.0-1.0]，越高越接近原始语音
        style: 风格强度 [0.0-1.0]，控制语音表现力（仅部分模型支持）
        use_speaker_boost: 是否启用说话人增强，提升语音清晰度
    """
    stability: Optional[float] = Field(None, ge=0.0, le=1.0)
    similarity_boost: Optional[float] = Field(None, ge=0.0, le=1.0)
    style: Optional[float] = Field(None, ge=0.0, le=1.0)
    use_speaker_boost: Optional[bool] = None

    class Config:
        frozen = True  # 不可变，确保线程安全


class TTSRequest(BaseModel):
    """
    TTS合成请求
    
    封装了所有TTS合成所需的参数，是服务层与适配器层的数据传输对象。
    """
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(..., min_length=1)
    model_id: str = Field(default="eleven_multilingual_v2")
    output_format: AudioFormat = Field(default=AudioFormat.MP3_44100_128)
    voice_settings: Optional[VoiceSettings] = None
    
    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """验证文本不为空白字符"""
        if not v or not v.strip():
            raise ValueError("文本内容不能为空")
        return v

    class Config:
        frozen = True


class TTSResponse(BaseModel):
    """
    TTS合成响应
    
    Attributes:
        audio_data: 音频二进制数据
        format: 实际返回的音频格式
        duration_ms: 音频时长（毫秒），可选
        metadata: 额外的元数据（如provider返回的调试信息）
    """
    audio_data: bytes
    format: AudioFormat
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True  # 允许bytes类型


class VoiceInfo(BaseModel):
    """
    语音信息
    
    用于表示TTS provider中可用的语音角色。
    """
    voice_id: str
    name: str
    accent: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)

    class Config:
        frozen = True

