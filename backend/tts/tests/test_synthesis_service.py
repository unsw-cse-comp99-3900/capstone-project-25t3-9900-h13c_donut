"""
SynthesisService单元测试

测试内容：
1. 服务初始化和依赖注入
2. 整段合成功能
3. 流式合成功能
4. 缓存逻辑
5. 错误处理
"""
import pytest
from unittest.mock import AsyncMock, patch

from services.synthesis_service import SynthesisService, create_synthesis_service
from domain.models import VoiceSettings, TTSResponse, AudioFormat
from utils.exceptions import ValidationError, TTSError


class TestSynthesisServiceInit:
    """服务初始化测试"""
    
    def test_init_with_client(self, mock_tts_client):
        """测试：使用客户端初始化"""
        service = SynthesisService(tts_client=mock_tts_client)
        assert service.client == mock_tts_client
        assert service.enable_cache is False
    
    def test_init_with_cache(self, mock_tts_client):
        """测试：启用缓存"""
        service = SynthesisService(
            tts_client=mock_tts_client,
            enable_cache=True,
            cache_ttl_seconds=1800,
        )
        assert service.enable_cache is True
        assert service.cache_ttl_seconds == 1800


class TestSynthesizeWhole:
    """整段合成功能测试"""
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self, mock_tts_client):
        """测试：成功合成"""
        service = SynthesisService(tts_client=mock_tts_client)
        
        response = await service.synthesize_whole(
            text="Hello world",
            voice_id="test_voice",
        )
        
        assert isinstance(response, TTSResponse)
        assert response.audio_data == b"MOCK_AUDIO" * 100
        assert mock_tts_client.synthesize_called
    
    @pytest.mark.asyncio
    async def test_synthesize_with_settings(
        self, mock_tts_client, sample_voice_settings
    ):
        """测试：使用语音设置合成"""
        service = SynthesisService(tts_client=mock_tts_client)
        
        response = await service.synthesize_whole(
            text="Hello",
            voice_id="test_voice",
            voice_settings=sample_voice_settings,
        )
        
        assert isinstance(response, TTSResponse)
        assert mock_tts_client.synthesize_called
    
    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self, mock_tts_client):
        """测试：空文本验证"""
        service = SynthesisService(tts_client=mock_tts_client)
        
        with pytest.raises(ValidationError, match="文本内容不能为空"):
            await service.synthesize_whole(text="", voice_id="test_voice")
    
    @pytest.mark.asyncio
    async def test_synthesize_whitespace_text(self, mock_tts_client):
        """测试：空白字符文本验证"""
        service = SynthesisService(tts_client=mock_tts_client)
        
        with pytest.raises(ValidationError):
            await service.synthesize_whole(text="   ", voice_id="test_voice")
    
    @pytest.mark.asyncio
    async def test_synthesize_empty_voice_id(self, mock_tts_client):
        """测试：空voice_id验证"""
        service = SynthesisService(tts_client=mock_tts_client)
        
        with pytest.raises(ValidationError, match="voice_id不能为空"):
            await service.synthesize_whole(text="Hello", voice_id="")
    
    @pytest.mark.asyncio
    async def test_synthesize_with_failing_client(self, mock_tts_client_failing):
        """测试：客户端失败时的错误传播"""
        service = SynthesisService(tts_client=mock_tts_client_failing)
        
        with pytest.raises(TTSError):
            await service.synthesize_whole(text="Hello", voice_id="test_voice")


class TestSynthesizeChunked:
    """流式合成功能测试"""
    
    @pytest.mark.asyncio
    async def test_chunked_synthesis(self, mock_tts_client):
        """测试：分块合成"""
        service = SynthesisService(
            tts_client=mock_tts_client,
            chunk_size=100,  # 小分块用于测试
        )
        
        chunks = []
        async for chunk in service.synthesize_chunked(
            text="Hello", voice_id="test_voice"
        ):
            chunks.append(chunk)
        
        # 验证收到了分块数据
        assert len(chunks) > 0
        
        # 验证重组后的数据与原始数据一致
        full_audio = b"".join(chunks)
        assert full_audio == b"MOCK_AUDIO" * 100


class TestCaching:
    """缓存功能测试"""
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_tts_client):
        """测试：缓存命中"""
        service = SynthesisService(
            tts_client=mock_tts_client,
            enable_cache=True,
        )
        
        # 第一次调用（缓存miss）
        response1 = await service.synthesize_whole(
            text="Hello", voice_id="test_voice"
        )
        assert response1.metadata.get("cached") is False
        
        # 第二次调用（缓存hit）
        response2 = await service.synthesize_whole(
            text="Hello", voice_id="test_voice"
        )
        assert response2.metadata.get("cached") is True
        
        # 验证音频数据一致
        assert response1.audio_data == response2.audio_data
    
    @pytest.mark.asyncio
    async def test_cache_disabled(self, mock_tts_client):
        """测试：禁用缓存时每次都调用客户端"""
        service = SynthesisService(
            tts_client=mock_tts_client,
            enable_cache=False,
        )
        
        # 两次调用都应该触发客户端
        await service.synthesize_whole(text="Hello", voice_id="test_voice")
        mock_tts_client.synthesize_called = False  # 重置标志
        
        await service.synthesize_whole(text="Hello", voice_id="test_voice")
        assert mock_tts_client.synthesize_called


class TestHelperMethods:
    """辅助方法测试"""
    
    @pytest.mark.asyncio
    async def test_get_available_voices(self, mock_tts_client):
        """测试：获取语音列表"""
        service = SynthesisService(tts_client=mock_tts_client)
        
        voices = await service.get_available_voices()
        
        assert len(voices) == 2
        assert voices[0].voice_id == "mock_voice_1"
        assert mock_tts_client.get_voices_called
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_tts_client):
        """测试：健康检查"""
        service = SynthesisService(tts_client=mock_tts_client)
        
        is_healthy = await service.health_check()
        
        assert is_healthy is True
        assert mock_tts_client.health_check_called


class TestFactoryFunction:
    """工厂函数测试"""
    
    def test_create_elevenlabs_service(self, mock_api_key):
        """测试：创建ElevenLabs服务"""
        service = create_synthesis_service(
            provider="elevenlabs",
            api_key=mock_api_key,
        )
        
        assert isinstance(service, SynthesisService)
    
    def test_create_without_api_key(self):
        """测试：缺少API密钥时报错"""
        with pytest.raises(ValueError, match="需要提供api_key"):
            create_synthesis_service(provider="elevenlabs")
    
    def test_create_unsupported_provider(self, mock_api_key):
        """测试：不支持的provider"""
        with pytest.raises(ValueError, match="不支持的provider"):
            create_synthesis_service(
                provider="unknown_provider",
                api_key=mock_api_key,
            )

