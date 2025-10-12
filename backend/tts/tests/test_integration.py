"""
集成测试（需要真实API密钥）

这些测试会调用真实的ElevenLabs API，需要：
1. 设置环境变量 ELEVENLABS_API_KEY
2. 运行时添加 -m integration 标记

运行集成测试：
$ ELEVENLABS_API_KEY=your_key pytest tests/test_integration.py -m integration -v

注意：
- 集成测试会消耗API配额
- 默认情况下不运行（需要显式标记）
- 适用于发布前的完整功能验证
"""
import pytest
import os

from adapters.elevenlabs_client import ElevenLabsClient
from services.synthesis_service import SynthesisService, create_synthesis_service
from domain.models import TTSRequest, VoiceSettings, AudioFormat


# 跳过条件：没有设置真实API密钥
skip_if_no_api_key = pytest.mark.skipif(
    not os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY") == "test_api_key",
    reason="需要设置真实的ELEVENLABS_API_KEY环境变量"
)


@pytest.mark.integration
@skip_if_no_api_key
class TestElevenLabsClientIntegration:
    """ElevenLabs客户端集成测试"""
    
    @pytest.mark.asyncio
    async def test_synthesize_real_api(self):
        """测试：真实API合成"""
        api_key = os.getenv("ELEVENLABS_API_KEY")
        client = ElevenLabsClient(api_key=api_key)
        
        request = TTSRequest(
            text="Hello, this is a test.",
            voice_id="Rachel",  # ElevenLabs的预设语音
            model_id="eleven_multilingual_v2",
        )
        
        response = await client.synthesize(request)
        
        # 验证响应
        assert response.audio_data is not None
        assert len(response.audio_data) > 1000  # 至少有一些音频数据
        assert response.format == AudioFormat.MP3_44100_128
        assert "provider" in response.metadata
        assert response.metadata["provider"] == "elevenlabs"
        
        print(f"✅ 合成成功，音频大小: {len(response.audio_data)} 字节")
    
    @pytest.mark.asyncio
    async def test_get_voices_real_api(self):
        """测试：获取真实语音列表"""
        api_key = os.getenv("ELEVENLABS_API_KEY")
        client = ElevenLabsClient(api_key=api_key)
        
        voices = await client.get_voices()
        
        # 验证响应
        assert len(voices) > 0
        assert voices[0].voice_id is not None
        assert voices[0].name is not None
        
        print(f"✅ 获取到 {len(voices)} 个语音")
        for voice in voices[:5]:  # 打印前5个
            print(f"  - {voice.name} ({voice.voice_id})")
    
    @pytest.mark.asyncio
    async def test_synthesize_stream_real_api(self):
        """测试：流式合成"""
        api_key = os.getenv("ELEVENLABS_API_KEY")
        client = ElevenLabsClient(api_key=api_key, chunk_size=10_000)
        
        request = TTSRequest(
            text="This is a longer text for testing streaming.",
            voice_id="Rachel",
        )
        
        chunks = []
        async for chunk in client.synthesize_stream(request):
            chunks.append(chunk)
        
        # 验证
        assert len(chunks) > 1  # 应该有多个分块
        total_size = sum(len(chunk) for chunk in chunks)
        assert total_size > 1000
        
        print(f"✅ 流式合成成功，收到 {len(chunks)} 个分块，总大小 {total_size} 字节")


@pytest.mark.integration
@skip_if_no_api_key
class TestSynthesisServiceIntegration:
    """SynthesisService集成测试"""
    
    @pytest.mark.asyncio
    async def test_service_end_to_end(self):
        """测试：端到端服务调用"""
        api_key = os.getenv("ELEVENLABS_API_KEY")
        service = create_synthesis_service(
            provider="elevenlabs",
            api_key=api_key,
        )
        
        response = await service.synthesize_whole(
            text="Integration test message.",
            voice_id="Rachel",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
            ),
        )
        
        # 验证
        assert response.audio_data is not None
        assert len(response.audio_data) > 1000
        assert "synthesis_time_ms" in response.metadata
        
        print(f"✅ 服务调用成功，耗时: {response.metadata['synthesis_time_ms']}ms")
    
    @pytest.mark.asyncio
    async def test_service_with_cache(self):
        """测试：缓存功能（真实API）"""
        api_key = os.getenv("ELEVENLABS_API_KEY")
        service = create_synthesis_service(
            provider="elevenlabs",
            api_key=api_key,
            enable_cache=True,
        )
        
        # 第一次调用（miss）
        response1 = await service.synthesize_whole(
            text="Cache test message.",
            voice_id="Rachel",
        )
        time1 = response1.metadata.get("synthesis_time_ms")
        
        # 第二次调用（hit）
        response2 = await service.synthesize_whole(
            text="Cache test message.",
            voice_id="Rachel",
        )
        time2 = response2.metadata.get("synthesis_time_ms", 0)
        
        # 验证
        assert response2.metadata.get("cached") is True
        assert response1.audio_data == response2.audio_data
        # 缓存命中应该更快
        assert time2 < time1
        
        print(f"✅ 缓存测试通过")
        print(f"  第一次: {time1}ms（API调用）")
        print(f"  第二次: {time2}ms（缓存命中）")


@pytest.mark.integration
@skip_if_no_api_key
class TestErrorHandlingIntegration:
    """错误处理集成测试"""
    
    @pytest.mark.asyncio
    async def test_invalid_voice_id(self):
        """测试：无效的voice_id"""
        from utils.exceptions import VoiceNotFoundError
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        client = ElevenLabsClient(api_key=api_key)
        
        request = TTSRequest(
            text="Test",
            voice_id="INVALID_VOICE_ID_123456",
        )
        
        # 应该抛出VoiceNotFoundError
        with pytest.raises(VoiceNotFoundError):
            await client.synthesize(request)
        
        print("✅ 无效voice_id错误处理正确")
    
    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """测试：无效的API密钥"""
        from utils.exceptions import AuthenticationError
        
        client = ElevenLabsClient(api_key="invalid_key_123")
        
        request = TTSRequest(
            text="Test",
            voice_id="Rachel",
        )
        
        # 应该抛出AuthenticationError
        with pytest.raises(AuthenticationError):
            await client.synthesize(request)
        
        print("✅ 无效API密钥错误处理正确")


if __name__ == "__main__":
    # 直接运行集成测试的便利脚本
    import asyncio
    import sys
    
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("❌ 错误：未设置ELEVENLABS_API_KEY环境变量")
        print("请运行: export ELEVENLABS_API_KEY=your_api_key")
        sys.exit(1)
    
    print("=" * 60)
    print("运行ElevenLabs集成测试")
    print("=" * 60)
    
    # 运行一个简单的端到端测试
    async def quick_test():
        from services.synthesis_service import create_synthesis_service
        
        print("\n🔧 创建服务...")
        service = create_synthesis_service(
            provider="elevenlabs",
            api_key=os.getenv("ELEVENLABS_API_KEY"),
        )
        
        print("🎤 合成测试音频...")
        response = await service.synthesize_whole(
            text="Hello, this is a quick integration test.",
            voice_id="Rachel",
        )
        
        print(f"✅ 成功！音频大小: {len(response.audio_data)} 字节")
        print(f"   耗时: {response.metadata.get('synthesis_time_ms')}ms")
        
        print("\n📋 获取可用语音...")
        voices = await service.get_available_voices()
        print(f"✅ 找到 {len(voices)} 个可用语音")
        
        print("\n" + "=" * 60)
        print("✅ 集成测试通过！")
        print("=" * 60)
    
    asyncio.run(quick_test())

