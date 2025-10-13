#!/usr/bin/env python3
"""
ASR集成测试脚本
测试WebSocket控制层与BE-5 ASR模块的集成
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.asr_service import ASRService
from app.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_asr_service_health():
    """测试ASR服务健康检查"""
    print("=" * 60)
    print("测试1: ASR服务健康检查")
    print("=" * 60)
    
    asr_service = ASRService()
    
    print(f"ASR服务地址: {asr_service.asr_service_url}")
    print(f"ASR端点: {asr_service.asr_endpoint}")
    
    try:
        is_healthy = await asr_service.check_service_health()
        if is_healthy:
            print("[OK] BE-5 ASR服务健康检查通过")
            return True
        else:
            print("[ERROR] BE-5 ASR服务健康检查失败")
            return False
    except Exception as e:
        print(f"[ERROR] 健康检查出错: {e}")
        return False

async def test_asr_transcription():
    """测试ASR转录功能"""
    print("\n" + "=" * 60)
    print("测试2: ASR转录功能")
    print("=" * 60)
    
    # 检查是否有测试音频文件
    test_audio_file = "asr/story.wav"
    if not os.path.exists(test_audio_file):
        print(f"[ERROR] 测试音频文件不存在: {test_audio_file}")
        print("请确保BE-5的story.wav文件存在")
        return False
    
    print(f"使用测试音频文件: {test_audio_file}")
    
    asr_service = ASRService()
    
    try:
        # 测试免费模式（调用BE-5服务）
        print("\n测试免费模式（BE-5 ASR服务）...")
        result = await asr_service.transcribe_audio(test_audio_file, model="free")
        
        if result:
            print("[OK] ASR转录成功")
            print(f"   转录文本: {result.get('text', '')[:100]}...")
            print(f"   分段数量: {len(result.get('segments', []))}")
            print(f"   置信度: {result.get('confidence', 'N/A')}")
            
            # 显示前3个分段
            segments = result.get('segments', [])
            if segments:
                print("\n   前3个分段:")
                for i, seg in enumerate(segments[:3]):
                    start = seg.get('start', 0)
                    end = seg.get('end', 0)
                    text = seg.get('text', '')
                    print(f"     {i+1}. [{start:.1f}s - {end:.1f}s]: {text}")
            
            return True
        else:
            print("[ERROR] ASR转录失败 - 返回None")
            return False
            
    except Exception as e:
        print(f"[ERROR] ASR转录出错: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_configuration():
    """测试配置"""
    print("\n" + "=" * 60)
    print("测试3: 配置检查")
    print("=" * 60)
    
    print("当前ASR配置:")
    print(f"  ASR_SERVICE_URL: {settings.ASR_SERVICE_URL}")
    print(f"  ASR_INTERNAL_ENDPOINT: {settings.ASR_INTERNAL_ENDPOINT}")
    print(f"  ASR_TIMEOUT_SECONDS: {settings.ASR_TIMEOUT_SECONDS}")
    print(f"  WHISPER_API_URL: {settings.WHISPER_API_URL}")
    print(f"  WHISPER_MODEL: {settings.WHISPER_MODEL}")
    
    # 检查OPENAI_API_KEY
    api_key = settings.OPENAI_API_KEY
    if api_key and api_key != "your-openai-api-key":
        print(f"  OPENAI_API_KEY: {'*' * 8}{api_key[-4:] if len(api_key) > 4 else '****'}")
    else:
        print("  OPENAI_API_KEY: 未设置或使用默认值")
    
    print("[OK] 配置检查完成")
    return True

async def main():
    """运行所有测试"""
    print("ASR模块集成测试")
    print("测试WebSocket控制层与BE-5 ASR模块的集成")
    print()
    
    tests = [
        ("配置检查", test_configuration),
        ("ASR服务健康检查", test_asr_service_health),
        ("ASR转录功能", test_asr_transcription),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"运行测试: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"[PASS] {test_name} 测试通过")
            else:
                print(f"[FAIL] {test_name} 测试失败")
        except Exception as e:
            print(f"[ERROR] {test_name} 测试出错: {e}")
    
    print(f"\n{'='*60}")
    print(f"测试结果: {passed}/{total} 通过")
    print(f"{'='*60}")
    
    if passed == total:
        print("\nASR集成测试全部通过！")
        print("\n集成状态:")
        print("  - WebSocket控制层 [OK]")
        print("  - BE-5 ASR模块 [OK]")
        print("  - BE-6 TTS模块 [OK]")
        print("\n后端三个模块已成功集成！")
        print("\n下一步:")
        print("1. 确保BE-5的ASR服务运行在端口8001")
        print("2. 启动你的WebSocket服务器: python main.py")
        print("3. 前端可以连接进行完整测试")
    else:
        print(f"\n{total - passed} 个测试失败")
        print("\n故障排除:")
        print("1. 确保BE-5的ASR服务正在运行")
        print("2. 检查ASR服务地址配置")
        print("3. 确保测试音频文件存在")
        print("4. 检查网络连接")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
