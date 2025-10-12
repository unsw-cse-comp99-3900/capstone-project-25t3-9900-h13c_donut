"""
TTS模块使用示例

演示如何使用TTS模块的各项功能。
"""
import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from services.synthesis_service import create_synthesis_service
from domain.models import VoiceSettings


async def example_basic_synthesis():
    """示例1：基础合成"""
    print("=" * 60)
    print("示例1：基础文本转语音")
    print("=" * 60)
    
    # 创建服务
    service = create_synthesis_service(
        provider="elevenlabs",
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    
    # 合成音频（使用Sarah - 年轻美国女性声音）
    response = await service.synthesize_whole(
        text="Hello, this is a basic text-to-speech example.",
        voice_id="YLbQE9U7P1K6rBNJWNSv",  # Sarah
    )
    
    print(f"✅ 合成成功！")
    print(f"   音频大小: {len(response.audio_data):,} 字节")
    print(f"   格式: {response.format.value}")
    print(f"   耗时: {response.metadata.get('synthesis_time_ms')}ms")
    
    # 可选：保存音频文件
    with open("output_basic.mp3", "wb") as f:
        f.write(response.audio_data)
    print(f"   已保存到: output_basic.mp3")


async def example_advanced_synthesis():
    """示例2：高级合成（自定义参数）"""
    print("\n" + "=" * 60)
    print("示例2：自定义语音参数")
    print("=" * 60)
    
    service = create_synthesis_service(
        provider="elevenlabs",
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    
    # 使用自定义语音设置
    response = await service.synthesize_whole(
        text="This example demonstrates advanced voice customization.",
        voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah
        voice_settings=VoiceSettings(
            stability=0.5,           # 稳定性
            similarity_boost=0.75,   # 相似度增强
            style=0.3,               # 风格强度
            use_speaker_boost=True,  # 说话人增强
        ),
    )
    
    print(f"✅ 高级合成成功！")
    print(f"   音频大小: {len(response.audio_data):,} 字节")
    
    with open("output_advanced.mp3", "wb") as f:
        f.write(response.audio_data)
    print(f"   已保存到: output_advanced.mp3")


async def example_streaming():
    """示例3：流式合成"""
    print("\n" + "=" * 60)
    print("示例3：流式合成（分块接收）")
    print("=" * 60)
    
    service = create_synthesis_service(
        provider="elevenlabs",
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    
    chunks = []
    chunk_count = 0
    
    # 流式接收音频分块
    async for chunk in service.synthesize_chunked(
        text="This is a streaming synthesis example with multiple audio chunks.",
        voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah
    ):
        chunks.append(chunk)
        chunk_count += 1
        print(f"   收到分块 {chunk_count}: {len(chunk)} 字节")
    
    # 合并所有分块
    full_audio = b"".join(chunks)
    
    print(f"✅ 流式合成完成！")
    print(f"   总分块数: {chunk_count}")
    print(f"   总大小: {len(full_audio):,} 字节")
    
    with open("output_streaming.mp3", "wb") as f:
        f.write(full_audio)
    print(f"   已保存到: output_streaming.mp3")


async def example_get_voices():
    """示例4：获取可用语音列表"""
    print("\n" + "=" * 60)
    print("示例4：获取可用语音列表")
    print("=" * 60)
    
    service = create_synthesis_service(
        provider="elevenlabs",
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    
    voices = await service.get_available_voices()
    
    print(f"✅ 找到 {len(voices)} 个可用语音\n")
    
    # 打印前10个语音
    for i, voice in enumerate(voices[:10], 1):
        accent = voice.accent or "未知"
        gender = voice.gender or "未知"
        print(f"{i:2d}. {voice.name:20s} ({voice.voice_id})")
        print(f"    口音: {accent:10s} 性别: {gender}")


async def example_caching():
    """示例5：缓存功能"""
    print("\n" + "=" * 60)
    print("示例5：缓存功能（提升性能）")
    print("=" * 60)
    
    # 创建启用缓存的服务
    service = create_synthesis_service(
        provider="elevenlabs",
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        enable_cache=True,
        cache_ttl_seconds=3600,
    )
    
    test_text = "This is a cache test message."
    
    # 第一次调用（缓存miss）
    print("\n第一次调用（API请求）...")
    response1 = await service.synthesize_whole(
        text=test_text,
        voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah
    )
    time1 = response1.metadata.get("synthesis_time_ms")
    print(f"   耗时: {time1}ms")
    print(f"   缓存命中: {response1.metadata.get('cached', False)}")
    
    # 第二次调用（缓存hit）
    print("\n第二次调用（从缓存）...")
    response2 = await service.synthesize_whole(
        text=test_text,
        voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah
    )
    time2 = response2.metadata.get("synthesis_time_ms", 0)
    print(f"   耗时: {time2}ms")
    print(f"   缓存命中: {response2.metadata.get('cached', False)}")
    
    print(f"\n✅ 缓存加速比: {time1 / max(time2, 1):.1f}x")


async def example_error_handling():
    """示例6：错误处理"""
    print("\n" + "=" * 60)
    print("示例6：错误处理")
    print("=" * 60)
    
    from utils.exceptions import ValidationError, TTSError
    
    service = create_synthesis_service(
        provider="elevenlabs",
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    
    # 测试1：空文本错误
    print("\n测试1：空文本验证")
    try:
        await service.synthesize_whole(text="", voice_id="EXAVITQu4vr4xnSDxMaL")
    except ValidationError as e:
        print(f"   ✅ 捕获到预期错误: {e}")
    
    # 测试2：无效voice_id（如果需要真实测试，取消注释）
    # print("\n测试2：无效voice_id")
    # try:
    #     await service.synthesize_whole(text="Test", voice_id="INVALID_ID")
    # except TTSError as e:
    #     print(f"   ✅ 捕获到错误: {e.error_code} - {e.message}")
    
    print("\n✅ 错误处理测试完成")


async def main():
    """运行所有示例"""
    print("\n" + "🎤" * 30)
    print("TTS模块使用示例")
    print("🎤" * 30 + "\n")
    
    # 检查API密钥
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("❌ 错误：未设置ELEVENLABS_API_KEY环境变量")
        print("\n请创建.env文件并添加:")
        print("ELEVENLABS_API_KEY=your_api_key_here")
        return
    
    try:
        # 运行各个示例
        await example_basic_synthesis()
        await example_advanced_synthesis()
        await example_streaming()
        await example_get_voices()
        await example_caching()
        await example_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成！")
        print("=" * 60)
        print("\n生成的音频文件:")
        print("  - output_basic.mp3")
        print("  - output_advanced.mp3")
        print("  - output_streaming.mp3")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  示例被用户中断")
    except Exception as e:
        print(f"\n\n❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

