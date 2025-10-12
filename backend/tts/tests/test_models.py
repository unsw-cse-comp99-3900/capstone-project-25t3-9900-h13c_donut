"""
领域模型单元测试

测试内容：
1. 模型创建和验证
2. 边界条件检查
3. 不可变性验证
"""
import pytest
from pydantic import ValidationError

from domain.models import (
    TTSRequest,
    VoiceSettings,
    TTSResponse,
    VoiceInfo,
    AudioFormat,
)


class TestVoiceSettings:
    """VoiceSettings模型测试"""
    
    def test_create_with_valid_params(self):
        """测试：使用有效参数创建"""
        settings = VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.3,
            use_speaker_boost=True,
        )
        assert settings.stability == 0.5
        assert settings.similarity_boost == 0.75
        assert settings.style == 0.3
        assert settings.use_speaker_boost is True
    
    def test_create_with_none_params(self):
        """测试：可选参数为None"""
        settings = VoiceSettings()
        assert settings.stability is None
        assert settings.similarity_boost is None
    
    def test_boundary_validation(self):
        """测试：边界值验证"""
        # stability超出范围
        with pytest.raises(ValidationError):
            VoiceSettings(stability=1.5)
        
        with pytest.raises(ValidationError):
            VoiceSettings(stability=-0.1)
    
    def test_immutability(self):
        """测试：不可变性（frozen=True）"""
        settings = VoiceSettings(stability=0.5)
        with pytest.raises(ValidationError):
            settings.stability = 0.8


class TestTTSRequest:
    """TTSRequest模型测试"""
    
    def test_create_minimal(self):
        """测试：最小参数创建"""
        request = TTSRequest(
            text="Hello",
            voice_id="test_voice",
        )
        assert request.text == "Hello"
        assert request.voice_id == "test_voice"
        assert request.model_id == "eleven_multilingual_v2"  # 默认值
    
    def test_create_full(self, sample_voice_settings: VoiceSettings):
        """测试：完整参数创建"""
        request = TTSRequest(
            text="Hello world",
            voice_id="test_voice",
            model_id="custom_model",
            output_format=AudioFormat.PCM_44100,
            voice_settings=sample_voice_settings,
        )
        assert request.output_format == AudioFormat.PCM_44100
        assert request.voice_settings == sample_voice_settings
    
    def test_text_validation(self):
        """测试：文本验证"""
        # 空文本
        with pytest.raises(ValidationError):
            TTSRequest(text="", voice_id="test")
        
        # 只有空白字符
        with pytest.raises(ValidationError):
            TTSRequest(text="   ", voice_id="test")
    
    def test_text_length_limit(self):
        """测试：文本长度限制"""
        # 超长文本（>5000字符）
        long_text = "a" * 5001
        with pytest.raises(ValidationError):
            TTSRequest(text=long_text, voice_id="test")


class TestTTSResponse:
    """TTSResponse模型测试"""
    
    def test_create_minimal(self):
        """测试：最小参数创建"""
        response = TTSResponse(
            audio_data=b"fake_audio",
            format=AudioFormat.MP3_44100_128,
        )
        assert response.audio_data == b"fake_audio"
        assert response.format == AudioFormat.MP3_44100_128
        assert response.duration_ms is None
        assert response.metadata == {}
    
    def test_create_with_metadata(self):
        """测试：带元数据创建"""
        metadata = {"provider": "test", "latency_ms": 123}
        response = TTSResponse(
            audio_data=b"audio",
            format=AudioFormat.MP3_44100_128,
            duration_ms=1500,
            metadata=metadata,
        )
        assert response.metadata == metadata


class TestVoiceInfo:
    """VoiceInfo模型测试"""
    
    def test_create_minimal(self):
        """测试：最小参数创建"""
        voice = VoiceInfo(
            voice_id="test_123",
            name="Test Voice",
        )
        assert voice.voice_id == "test_123"
        assert voice.name == "Test Voice"
        assert voice.accent is None
    
    def test_create_full(self):
        """测试：完整参数创建"""
        voice = VoiceInfo(
            voice_id="test_123",
            name="Test Voice",
            accent="american",
            gender="female",
            age="young",
            description="A test voice",
            preview_url="https://example.com/preview.mp3",
            labels={"language": "en-US"},
        )
        assert voice.accent == "american"
        assert voice.labels["language"] == "en-US"

