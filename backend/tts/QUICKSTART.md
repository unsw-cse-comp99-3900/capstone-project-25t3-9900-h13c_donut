# 🚀 快速开始指南

5分钟上手TTS模块！

---

## 📋 前置要求

1. Python 3.9+ 
2. ElevenLabs API密钥（[免费注册](https://elevenlabs.io)）

---

## ⚡ 快速安装

### 步骤1：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤2：配置API密钥

创建`.env`文件：

```bash
# .env
ELEVENLABS_API_KEY=your_api_key_here
```

或者设置环境变量（Linux/Mac）：
```bash
export ELEVENLABS_API_KEY=your_api_key_here
```

Windows PowerShell：
```powershell
$env:ELEVENLABS_API_KEY="your_api_key_here"
```

### 步骤3：验证安装

```bash
python scripts/verify_tts.py
```

如果看到 `✅ 所有验证通过！`，恭喜！安装成功。

---

## 🎯 第一个TTS程序

创建`my_first_tts.py`：

```python
import asyncio
import os
from dotenv import load_dotenv
from services.synthesis_service import create_synthesis_service

load_dotenv()

async def main():
    # 1. 创建TTS服务
    service = create_synthesis_service(
        provider="elevenlabs",
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    
    # 2. 合成音频
    response = await service.synthesize_whole(
        text="Hello, this is my first text-to-speech program!",
        voice_id="Rachel",
    )
    
    # 3. 保存音频
    with open("my_first_tts.mp3", "wb") as f:
        f.write(response.audio_data)
    
    print(f"✅ 成功！音频已保存到 my_first_tts.mp3")
    print(f"   大小: {len(response.audio_data):,} 字节")
    print(f"   耗时: {response.metadata['synthesis_time_ms']}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

运行：
```bash
python my_first_tts.py
```

---

## 📚 更多示例

运行完整示例集：

```bash
python example.py
```

这会演示：
- ✅ 基础合成
- ✅ 自定义语音参数
- ✅ 流式合成
- ✅ 获取语音列表
- ✅ 缓存功能
- ✅ 错误处理

---

## 🧪 运行测试

### 单元测试（无需API密钥）

```bash
# 运行所有测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov

# 生成HTML覆盖率报告
pytest tests/ --cov --cov-report=html
# 然后打开 htmlcov/index.html
```

### 集成测试（需要API密钥）

```bash
export ELEVENLABS_API_KEY=your_api_key
pytest tests/test_integration.py -m integration -v
```

---

## 🔧 常见问题

### Q: 为什么提示"未设置ELEVENLABS_API_KEY"？

**A**: 请确保：
1. 创建了`.env`文件并填写了API密钥
2. 或设置了环境变量`ELEVENLABS_API_KEY`

### Q: 测试失败怎么办？

**A**: 
1. 检查网络连接
2. 确认API密钥有效
3. 查看详细错误：`pytest tests/ -v --tb=long`

### Q: 如何获取更多语音？

**A**:
```python
voices = await service.get_available_voices()
for voice in voices:
    print(f"{voice.name} - {voice.voice_id}")
```

### Q: 支持中文吗？

**A**: 支持！使用`eleven_multilingual_v2`模型（默认）支持29种语言，包括中文。

```python
response = await service.synthesize_whole(
    text="你好，这是一个中文测试。",
    voice_id="Rachel",
)
```

---

## 📖 下一步

- 📚 阅读[完整文档](README.md)
- 🏗️ 了解[架构设计](ARCHITECTURE.md)
- 🔌 查看[集成示例](example.py)

---

## 💬 需要帮助？

- 📧 联系团队成员
- 📝 查看项目Wiki
- 🐛 提交Issue

---

**祝你使用愉快！🎉**

