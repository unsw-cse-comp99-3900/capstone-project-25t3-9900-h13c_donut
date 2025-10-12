"""
应用配置管理

使用Pydantic进行配置验证和类型安全。
支持从环境变量和.env文件读取配置。

配置优先级：
1. 环境变量（最高）
2. .env文件
3. 默认值

使用示例：
>>> from config.settings import settings
>>> print(settings.ELEVENLABS_API_KEY)
>>> print(settings.TTS_DEFAULT_PROVIDER)
"""
from __future__ import annotations
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Literal, Optional


class Settings(BaseSettings):
    """
    全局配置类
    
    所有配置项都应在此定义，确保类型安全和文档完整。
    """
    
    # ========== TTS Provider配置 ==========
    
    TTS_DEFAULT_PROVIDER: Literal["elevenlabs", "coqui"] = Field(
        default="elevenlabs",
        description="默认TTS provider"
    )
    
    # ========== ElevenLabs配置 ==========
    
    ELEVENLABS_API_KEY: str = Field(
        default="",
        description="ElevenLabs API密钥（必填）"
    )
    
    ELEVENLABS_BASE_URL: str = Field(
        default="https://api.elevenlabs.io",
        description="ElevenLabs API基础URL"
    )
    
    ELEVENLABS_WS_URL: str = Field(
        default="wss://api.elevenlabs.io",
        description="ElevenLabs WebSocket URL"
    )
    
    ELEVENLABS_MODEL_ID: str = Field(
        default="eleven_multilingual_v2",
        description="默认模型ID（支持多语言）"
    )
    
    ELEVENLABS_VOICE_DEFAULT: str = Field(
        default="EXAVITQu4vr4xnSDxMaL",  # Sarah - 年轻美国女性
        description="默认语音ID（使用voice_id而非name）"
    )
    
    ELEVENLABS_TIMEOUT: float = Field(
        default=20.0,
        ge=1.0,
        le=300.0,
        description="请求超时时间（秒）"
    )
    
    ELEVENLABS_MAX_RETRIES: int = Field(
        default=3,
        ge=0,
        le=10,
        description="最大重试次数"
    )
    
    # ========== Coqui XTTS-v2配置（预留） ==========
    
    COQUI_BASE_URL: Optional[str] = Field(
        default=None,
        description="Coqui XTTS-v2自托管服务URL"
    )
    
    COQUI_TIMEOUT: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Coqui请求超时时间（秒）"
    )
    
    # ========== 音频处理配置 ==========
    
    AUDIO_CHUNK_SIZE: int = Field(
        default=32_000,
        ge=1024,
        le=1_048_576,
        description="音频分块大小（字节），约160ms @ 44.1kHz"
    )
    
    AUDIO_OUTPUT_FORMAT: str = Field(
        default="mp3_44100_128",
        description="默认音频输出格式"
    )
    
    # ========== 缓存配置 ==========
    
    CACHE_ENABLED: bool = Field(
        default=False,
        description="是否启用TTS缓存（需要Redis支持）"
    )
    
    CACHE_TTL_SECONDS: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="缓存过期时间（秒）"
    )
    
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis连接URL（如启用缓存）"
    )
    
    # ========== HTTP配置 ==========
    
    HTTP_CONNECT_TIMEOUT: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="HTTP连接超时（秒）"
    )
    
    HTTP_READ_TIMEOUT: float = Field(
        default=20.0,
        ge=5.0,
        le=300.0,
        description="HTTP读取超时（秒）"
    )
    
    # ========== 日志配置 ==========
    
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="日志级别"
    )
    
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    # ========== 性能配置 ==========
    
    MAX_CONCURRENT_REQUESTS: int = Field(
        default=10,
        ge=1,
        le=100,
        description="最大并发请求数"
    )
    
    # ========== 验证器 ==========
    
    @field_validator("ELEVENLABS_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """验证API密钥不为空或默认值"""
        import os
        # 测试环境允许跳过验证
        if os.getenv("TESTING") == "1":
            return v or "test_api_key"
        
        if not v or v == "change-me":
            raise ValueError(
                "必须设置ELEVENLABS_API_KEY环境变量。\n"
                "获取API密钥：https://elevenlabs.io/app/settings/api-keys"
            )
        return v
    
    @field_validator("AUDIO_CHUNK_SIZE")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """验证分块大小是否合理"""
        # 建议：16KB-64KB之间，确保低延迟和高效传输
        if v < 8192:
            raise ValueError("音频分块过小，可能导致过多网络请求")
        if v > 131072:
            raise ValueError("音频分块过大，可能增加延迟")
        return v
    
    # ========== 配置 ==========
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # 忽略未定义的环境变量
    }


# ========== 全局配置实例 ==========

# 懒加载：首次导入时创建，避免import时验证失败
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取全局配置实例（懒加载）
    
    使用懒加载的好处：
    1. 测试时可以mock配置
    2. 允许在导入时暂不验证（避免测试失败）
    3. 支持运行时动态重载配置
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# 便利导出（保持向后兼容）
settings = get_settings()


# ========== 配置验证工具 ==========

def validate_settings() -> bool:
    """
    验证配置是否完整
    
    用于应用启动时的配置检查。
    
    Returns:
        bool: True表示配置有效，False表示存在问题
    """
    try:
        s = get_settings()
        
        # 必填项检查
        if not s.ELEVENLABS_API_KEY:
            print("❌ 错误：未设置ELEVENLABS_API_KEY")
            return False
        
        # 缓存配置检查
        if s.CACHE_ENABLED and not s.REDIS_URL:
            print("⚠️  警告：启用了缓存但未配置REDIS_URL，将使用内存缓存")
        
        print("✅ 配置验证通过")
        return True
    
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False


def print_settings():
    """
    打印当前配置（用于调试）
    
    注意：会隐藏敏感信息（如API密钥）
    """
    s = get_settings()
    
    print("=" * 60)
    print("当前配置")
    print("=" * 60)
    print(f"TTS Provider: {s.TTS_DEFAULT_PROVIDER}")
    print(f"ElevenLabs API Key: {'*' * 8}{s.ELEVENLABS_API_KEY[-4:] if s.ELEVENLABS_API_KEY else 'N/A'}")
    print(f"ElevenLabs Model: {s.ELEVENLABS_MODEL_ID}")
    print(f"Default Voice: {s.ELEVENLABS_VOICE_DEFAULT}")
    print(f"Timeout: {s.ELEVENLABS_TIMEOUT}s")
    print(f"Max Retries: {s.ELEVENLABS_MAX_RETRIES}")
    print(f"Chunk Size: {s.AUDIO_CHUNK_SIZE} bytes")
    print(f"Cache Enabled: {s.CACHE_ENABLED}")
    print(f"Log Level: {s.LOG_LEVEL}")
    print("=" * 60)


if __name__ == "__main__":
    # 配置验证脚本
    print_settings()
    validate_settings()

