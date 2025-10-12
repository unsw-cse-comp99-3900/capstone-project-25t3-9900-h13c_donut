"""
Pytest配置和共享fixture

提供测试所需的通用fixture和配置。
"""
import pytest
from unittest.mock import AsyncMock, Mock
from typing import AsyncIterator

from domain.models import (
    TTSRequest,
    TTSResponse,
    VoiceInfo,
    VoiceSettings,
    AudioFormat,
)
from domain.interfaces import TTSClientInterface


# ========== Mock配置 ==========

@pytest.fixture
def mock_api_key() -> str:
    """测试用API密钥"""
    return "test_api_key_12345678"


@pytest.fixture
def sample_text() -> str:
    """测试用文本"""
    return "Hello, this is a test."


@pytest.fixture
def sample_voice_id() -> str:
    """测试用语音ID"""
    return "TestVoice123"


@pytest.fixture
def sample_voice_settings() -> VoiceSettings:
    """测试用语音设置"""
    return VoiceSettings(
        stability=0.5,
        similarity_boost=0.75,
        style=0.3,
        use_speaker_boost=True,
    )


@pytest.fixture
def sample_tts_request(
    sample_text: str,
    sample_voice_id: str,
    sample_voice_settings: VoiceSettings,
) -> TTSRequest:
    """测试用TTS请求"""
    return TTSRequest(
        text=sample_text,
        voice_id=sample_voice_id,
        model_id="test_model",
        voice_settings=sample_voice_settings,
    )


@pytest.fixture
def sample_audio_data() -> bytes:
    """测试用音频数据（假数据）"""
    # 生成一些假的音频字节
    return b"FAKE_AUDIO_DATA" * 1000


@pytest.fixture
def sample_tts_response(sample_audio_data: bytes) -> TTSResponse:
    """测试用TTS响应"""
    return TTSResponse(
        audio_data=sample_audio_data,
        format=AudioFormat.MP3_44100_128,
        duration_ms=1500,
        metadata={"test": True},
    )


@pytest.fixture
def sample_voice_info() -> VoiceInfo:
    """测试用语音信息"""
    return VoiceInfo(
        voice_id="test_voice_123",
        name="Test Voice",
        accent="american",
        gender="female",
        age="young",
        description="A test voice",
        labels={"accent": "american", "gender": "female"},
    )


# ========== Mock客户端 ==========

class MockTTSClient(TTSClientInterface):
    """Mock TTS客户端（用于服务层测试）"""
    
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.synthesize_called = False
        self.get_voices_called = False
        self.health_check_called = False
    
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        self.synthesize_called = True
        if self.should_fail:
            from utils.exceptions import ServiceUnavailableError
            raise ServiceUnavailableError("Mock service unavailable")
        
        return TTSResponse(
            audio_data=b"MOCK_AUDIO" * 100,
            format=AudioFormat.MP3_44100_128,
            metadata={"mock": True},
        )
    
    async def get_voices(self) -> list[VoiceInfo]:
        self.get_voices_called = True
        if self.should_fail:
            from utils.exceptions import NetworkError
            raise NetworkError("Mock network error")
        
        return [
            VoiceInfo(
                voice_id="mock_voice_1",
                name="Mock Voice 1",
                accent="american",
            ),
            VoiceInfo(
                voice_id="mock_voice_2",
                name="Mock Voice 2",
                accent="british",
            ),
        ]
    
    async def health_check(self) -> bool:
        self.health_check_called = True
        return not self.should_fail


@pytest.fixture
def mock_tts_client() -> MockTTSClient:
    """Mock TTS客户端fixture"""
    return MockTTSClient(should_fail=False)


@pytest.fixture
def mock_tts_client_failing() -> MockTTSClient:
    """失败的Mock TTS客户端fixture"""
    return MockTTSClient(should_fail=True)


# ========== 环境变量Mock ==========

@pytest.fixture
def mock_env(monkeypatch, mock_api_key: str):
    """Mock环境变量（避免测试时加载真实配置）"""
    monkeypatch.setenv("ELEVENLABS_API_KEY", mock_api_key)
    monkeypatch.setenv("ELEVENLABS_TIMEOUT", "10.0")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

