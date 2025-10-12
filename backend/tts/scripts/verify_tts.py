#!/usr/bin/env python3
"""
TTS功能验证脚本

用于验证TTS模块的各项功能，包括：
1. 配置验证
2. API连接测试
3. 语音合成测试
4. 流式合成测试
5. 性能测试

使用方法：
$ export ELEVENLABS_API_KEY=your_api_key
$ python scripts/verify_tts.py

或者：
$ python scripts/verify_tts.py --api-key your_api_key
"""
import asyncio
import argparse
import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.synthesis_service import create_synthesis_service
from domain.models import VoiceSettings
from config.settings import get_settings
from utils.exceptions import TTSError


class TTSVerifier:
    """TTS功能验证器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.service = None
        self.results = []
    
    def log_success(self, test_name: str, details: str = ""):
        """记录成功"""
        self.results.append((test_name, True, details))
        print(f"✅ {test_name}")
        if details:
            print(f"   {details}")
    
    def log_failure(self, test_name: str, error: str):
        """记录失败"""
        self.results.append((test_name, False, error))
        print(f"❌ {test_name}")
        print(f"   错误: {error}")
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        print(f"总计: {total} 项测试")
        print(f"通过: {passed} 项")
        print(f"失败: {total - passed} 项")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        print("=" * 60)
        
        return passed == total
    
    async def verify_config(self):
        """验证配置"""
        print("\n📋 验证配置...")
        
        try:
            settings = get_settings()
            
            # 检查API密钥
            if not self.api_key or self.api_key == "change-me":
                self.log_failure("配置验证", "未设置有效的API密钥")
                return False
            
            self.log_success(
                "配置验证",
                f"Provider: {settings.TTS_DEFAULT_PROVIDER}, "
                f"Model: {settings.ELEVENLABS_MODEL_ID}"
            )
            return True
        
        except Exception as e:
            self.log_failure("配置验证", str(e))
            return False
    
    async def verify_connection(self):
        """验证API连接"""
        print("\n🔌 验证API连接...")
        
        try:
            self.service = create_synthesis_service(
                provider="elevenlabs",
                api_key=self.api_key,
            )
            
            # 健康检查
            is_healthy = await self.service.health_check()
            
            if is_healthy:
                self.log_success("API连接", "服务可用")
                return True
            else:
                self.log_failure("API连接", "健康检查失败")
                return False
        
        except Exception as e:
            self.log_failure("API连接", str(e))
            return False
    
    async def verify_get_voices(self):
        """验证获取语音列表"""
        print("\n📢 验证语音列表...")
        
        try:
            voices = await self.service.get_available_voices()
            
            if len(voices) == 0:
                self.log_failure("获取语音列表", "未找到可用语音")
                return False
            
            self.log_success(
                "获取语音列表",
                f"找到 {len(voices)} 个可用语音"
            )
            
            # 打印前5个语音
            print("\n   可用语音（前5个）：")
            for voice in voices[:5]:
                accent = voice.accent or "未知"
                gender = voice.gender or "未知"
                print(f"   - {voice.name} ({voice.voice_id}) - {accent}, {gender}")
            
            return True
        
        except Exception as e:
            self.log_failure("获取语音列表", str(e))
            return False
    
    async def verify_basic_synthesis(self):
        """验证基础合成"""
        print("\n🎤 验证基础合成...")
        
        try:
            start_time = time.time()
            
            response = await self.service.synthesize_whole(
                text="Hello, this is a basic synthesis test.",
                voice_id="Rachel",
            )
            
            elapsed = int((time.time() - start_time) * 1000)
            audio_size = len(response.audio_data)
            
            if audio_size < 1000:
                self.log_failure("基础合成", f"音频数据太小: {audio_size} 字节")
                return False
            
            self.log_success(
                "基础合成",
                f"音频大小: {audio_size:,} 字节, 耗时: {elapsed}ms"
            )
            return True
        
        except Exception as e:
            self.log_failure("基础合成", str(e))
            return False
    
    async def verify_advanced_synthesis(self):
        """验证高级合成（带参数）"""
        print("\n🎛️  验证高级合成...")
        
        try:
            response = await self.service.synthesize_whole(
                text="This is an advanced synthesis test with custom voice settings.",
                voice_id="Rachel",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.3,
                    use_speaker_boost=True,
                ),
            )
            
            audio_size = len(response.audio_data)
            
            self.log_success(
                "高级合成",
                f"音频大小: {audio_size:,} 字节"
            )
            return True
        
        except Exception as e:
            self.log_failure("高级合成", str(e))
            return False
    
    async def verify_streaming(self):
        """验证流式合成"""
        print("\n📡 验证流式合成...")
        
        try:
            chunks = []
            chunk_count = 0
            
            async for chunk in self.service.synthesize_chunked(
                text="This is a streaming synthesis test.",
                voice_id="Rachel",
            ):
                chunks.append(chunk)
                chunk_count += 1
            
            total_size = sum(len(chunk) for chunk in chunks)
            
            if chunk_count == 0:
                self.log_failure("流式合成", "未收到任何音频分块")
                return False
            
            self.log_success(
                "流式合成",
                f"收到 {chunk_count} 个分块，总大小: {total_size:,} 字节"
            )
            return True
        
        except Exception as e:
            self.log_failure("流式合成", str(e))
            return False
    
    async def verify_cache(self):
        """验证缓存功能"""
        print("\n💾 验证缓存功能...")
        
        try:
            # 创建启用缓存的服务
            cached_service = create_synthesis_service(
                provider="elevenlabs",
                api_key=self.api_key,
                enable_cache=True,
            )
            
            test_text = "Cache test message for verification."
            
            # 第一次调用
            start1 = time.time()
            response1 = await cached_service.synthesize_whole(
                text=test_text,
                voice_id="Rachel",
            )
            time1 = int((time.time() - start1) * 1000)
            
            # 第二次调用（应该命中缓存）
            start2 = time.time()
            response2 = await cached_service.synthesize_whole(
                text=test_text,
                voice_id="Rachel",
            )
            time2 = int((time.time() - start2) * 1000)
            
            # 验证缓存
            if not response2.metadata.get("cached"):
                self.log_failure("缓存功能", "第二次调用未命中缓存")
                return False
            
            if response1.audio_data != response2.audio_data:
                self.log_failure("缓存功能", "缓存数据不一致")
                return False
            
            self.log_success(
                "缓存功能",
                f"第一次: {time1}ms（API调用）, 第二次: {time2}ms（缓存命中）"
            )
            return True
        
        except Exception as e:
            self.log_failure("缓存功能", str(e))
            return False
    
    async def verify_error_handling(self):
        """验证错误处理"""
        print("\n⚠️  验证错误处理...")
        
        try:
            from utils.exceptions import ValidationError
            
            # 测试空文本错误
            try:
                await self.service.synthesize_whole(
                    text="",
                    voice_id="Rachel",
                )
                self.log_failure("错误处理", "空文本未抛出异常")
                return False
            except ValidationError:
                pass  # 预期行为
            
            self.log_success("错误处理", "空文本验证正确")
            return True
        
        except Exception as e:
            self.log_failure("错误处理", str(e))
            return False
    
    async def run_all(self):
        """运行所有验证"""
        print("=" * 60)
        print("TTS模块功能验证")
        print("=" * 60)
        
        # 按顺序运行所有测试
        await self.verify_config()
        await self.verify_connection()
        
        if self.service:  # 如果连接成功才继续
            await self.verify_get_voices()
            await self.verify_basic_synthesis()
            await self.verify_advanced_synthesis()
            await self.verify_streaming()
            await self.verify_cache()
            await self.verify_error_handling()
        
        # 打印摘要
        all_passed = self.print_summary()
        
        return all_passed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TTS功能验证脚本")
    parser.add_argument(
        "--api-key",
        help="ElevenLabs API密钥（也可通过环境变量ELEVENLABS_API_KEY设置）"
    )
    
    args = parser.parse_args()
    
    # 获取API密钥
    api_key = args.api_key or os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("❌ 错误：未提供API密钥")
        print("\n使用方法:")
        print("  方式1: python scripts/verify_tts.py --api-key YOUR_API_KEY")
        print("  方式2: export ELEVENLABS_API_KEY=YOUR_API_KEY && python scripts/verify_tts.py")
        sys.exit(1)
    
    # 运行验证
    verifier = TTSVerifier(api_key)
    
    try:
        all_passed = asyncio.run(verifier.run_all())
        
        if all_passed:
            print("\n🎉 所有验证通过！TTS模块工作正常。")
            sys.exit(0)
        else:
            print("\n⚠️  部分验证失败，请检查上述错误信息。")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  验证被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

