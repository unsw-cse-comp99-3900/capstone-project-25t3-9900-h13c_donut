#!/usr/bin/env python3
"""
列出ElevenLabs账户中可用的语音

使用方法：
$ python scripts/list_voices.py
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

from services.synthesis_service import create_synthesis_service


async def main():
    print("=" * 70)
    print("查询ElevenLabs可用语音")
    print("=" * 70)
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("\n❌ 错误：未设置ELEVENLABS_API_KEY环境变量")
        print("请在.env文件中设置或export ELEVENLABS_API_KEY=your_api_key")
        return
    
    try:
        # 创建服务
        print("\n🔌 连接到ElevenLabs...")
        service = create_synthesis_service(
            provider="elevenlabs",
            api_key=api_key,
        )
        
        # 获取语音列表
        print("📋 正在获取语音列表...\n")
        voices = await service.get_available_voices()
        
        if not voices:
            print("⚠️  未找到任何可用语音")
            return
        
        print(f"✅ 找到 {len(voices)} 个可用语音:\n")
        print("-" * 70)
        
        for i, voice in enumerate(voices, 1):
            print(f"{i:2d}. {voice.name}")
            print(f"    Voice ID: {voice.voice_id}")
            
            # 显示标签信息
            labels = []
            if voice.accent:
                labels.append(f"口音: {voice.accent}")
            if voice.gender:
                labels.append(f"性别: {voice.gender}")
            if voice.age:
                labels.append(f"年龄: {voice.age}")
            
            if labels:
                print(f"    {' | '.join(labels)}")
            
            if voice.description:
                desc = voice.description[:60] + "..." if len(voice.description) > 60 else voice.description
                print(f"    描述: {desc}")
            
            print()
        
        print("-" * 70)
        print(f"\n💡 提示：在代码中使用 voice_id（而非name）来指定语音")
        print(f"    例如：voice_id=\"{voices[0].voice_id}\"")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

