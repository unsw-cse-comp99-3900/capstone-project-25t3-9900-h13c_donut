# TTS模块 - Accent Translator项目

## 📖 项目简介

这是Accent Translator项目的**TTS（Text-to-Speech）模块**，负责将文本合成为不同口音的语音。

### 核心特性

✅ **多Provider支持**
- ElevenLabs（已实现）
- Coqui XTTS-v2（预留）
- 易于扩展其他TTS服务

✅ **灵活的API**
- 同步合成：一次性生成完整音频
- 流式合成：逐块生成，降低延迟
- 语音参数调优：stability、similarity_boost等

✅ **企业级特性**
- 自动重试（指数退避）
- 详细的错误处理和映射
- 可选的缓存支持
- 完整的类型注解

✅ **高质量代码**
- 遵循SOLID原则
- 依赖注入，易于测试
- 38个单元测试，66%代码覆盖率
- 完整的中文注释

---

## 🏗️ 架构设计

### 分层架构

```
📦 tts/
├── config/                 # 配置层
│   └── settings.py         # 统一配置管理
├── domain/                 # 领域层
│   ├── models.py           # 领域模型（TTSRequest, TTSResponse等）
│   └── interfaces.py       # TTS客户端抽象接口
├── adapters/               # 适配器层
│   ├── elevenlabs_client.py      # ElevenLabs REST实现
│   └── elevenlabs_ws_client.py   # ElevenLabs WebSocket（预留）
├── services/               # 服务层
│   └── synthesis_service.py      # TTS业务逻辑
├── utils/                  # 工具层
│   └── exceptions.py       # 自定义异常
├── tests/                  # 测试
│   ├── test_models.py
│   ├── test_synthesis_service.py
│   ├── test_exceptions.py
│   └── test_integration.py
└── scripts/                # 脚本
    └── verify_tts.py       # 功能验证脚本
```

### 设计原则

1. **依赖倒置原则（DIP）**：业务层依赖抽象接口，而非具体实现
2. **接口隔离原则（ISP）**：分离同步和流式接口
3. **单一职责原则（SRP）**：每个模块职责明确
4. **开闭原则（OCP）**：对扩展开放，对修改封闭

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建`.env`文件（可参考下方配置模板）：

```bash
# ElevenLabs API密钥（必填）
ELEVENLABS_API_KEY=your_api_key_here

# 其他配置（可选）
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_VOICE_DEFAULT=Rachel
```

**获取API密钥**: https://elevenlabs.io/app/settings/api-keys

### 3. 验证安装

运行验证脚本：

```bash
python scripts/verify_tts.py
```

如果看到 `🎉 所有验证通过！` 说明安装成功。

---

## 📚 使用指南

### 基础用法

```python
from services.synthesis_service import create_synthesis_service

# 创建服务
service = create_synthesis_service(
    provider="elevenlabs",
    api_key="your_api_key",
)

# 合成音频
response = await service.synthesize_whole(
    text="Hello, this is a test.",
    voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah - 年轻美国女性
)

# 获取音频数据
audio_data = response.audio_data  # bytes
print(f"音频大小: {len(audio_data)} 字节")
```

### 高级用法

#### 1. 自定义语音参数

```python
from domain.models import VoiceSettings

response = await service.synthesize_whole(
    text="Hello world",
    voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah
    voice_settings=VoiceSettings(
        stability=0.5,           # 稳定性 [0.0-1.0]
        similarity_boost=0.75,   # 相似度增强 [0.0-1.0]
        style=0.3,               # 风格强度 [0.0-1.0]
        use_speaker_boost=True,  # 说话人增强
    ),
)
```

#### 2. 流式合成（适用于WebSocket）

```python
# 逐块接收音频，降低延迟
async for audio_chunk in service.synthesize_chunked(
    text="Long text...",
    voice_id="EXAVITQu4vr4xnSDxMaL",  # Sarah
):
    # 实时处理音频分块
    # 例如：发送到前端、写入音频流等
    print(f"收到分块: {len(audio_chunk)} 字节")
```

#### 3. 启用缓存（避免重复合成）

```python
service = create_synthesis_service(
    provider="elevenlabs",
    api_key="your_api_key",
    enable_cache=True,
    cache_ttl_seconds=3600,  # 缓存1小时
)

# 第一次调用：API请求
response1 = await service.synthesize_whole(
    text="Hello", 
    voice_id="EXAVITQu4vr4xnSDxMaL"  # Sarah
)

# 第二次调用：从缓存返回（更快）
response2 = await service.synthesize_whole(
    text="Hello", 
    voice_id="EXAVITQu4vr4xnSDxMaL"  # Sarah
)
print(response2.metadata["cached"])  # True
```

#### 4. 获取可用语音列表

```python
voices = await service.get_available_voices()

for voice in voices:
    print(f"{voice.name} ({voice.voice_id})")
    print(f"  口音: {voice.accent}, 性别: {voice.gender}")
```

### 依赖注入（用于测试）

```python
from adapters.elevenlabs_client import ElevenLabsClient
from services.synthesis_service import SynthesisService

# 创建客户端
client = ElevenLabsClient(
    api_key="your_api_key",
    timeout_seconds=30.0,
    max_retries=3,
)

# 注入到服务
service = SynthesisService(tts_client=client)
```

---

## 🧪 测试

### 运行单元测试

```bash
# 运行所有单元测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov

# 只测试特定模块
pytest tests/test_models.py -v
```

### 运行集成测试（需要真实API密钥）

```bash
# 设置API密钥
export ELEVENLABS_API_KEY=your_api_key

# 运行集成测试
pytest tests/test_integration.py -m integration -v
```

### 运行验证脚本

```bash
python scripts/verify_tts.py --api-key your_api_key
```

---

## ⚙️ 配置说明

所有配置项都在 `config/settings.py` 中定义，支持环境变量覆盖。

### 核心配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ELEVENLABS_API_KEY` | ElevenLabs API密钥（必填） | - |
| `ELEVENLABS_MODEL_ID` | 默认模型ID | `eleven_multilingual_v2` |
| `ELEVENLABS_VOICE_DEFAULT` | 默认语音ID | `EXAVITQu4vr4xnSDxMaL` (Sarah) |
| `ELEVENLABS_TIMEOUT` | 请求超时（秒） | `20.0` |
| `AUDIO_CHUNK_SIZE` | 流式分块大小（字节） | `32000` |
| `CACHE_ENABLED` | 是否启用缓存 | `false` |

### 环境变量配置

创建 `.env` 文件：

```bash
# ========== ElevenLabs配置 ==========
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_VOICE_DEFAULT=EXAVITQu4vr4xnSDxMaL  # Sarah - 年轻美国女性
ELEVENLABS_TIMEOUT=20.0
ELEVENLABS_MAX_RETRIES=3

# ========== 音频处理配置 ==========
AUDIO_CHUNK_SIZE=32000
AUDIO_OUTPUT_FORMAT=mp3_44100_128

# ========== 缓存配置 ==========
CACHE_ENABLED=false
CACHE_TTL_SECONDS=3600

# ========== 日志配置 ==========
LOG_LEVEL=INFO
```

---

## 🔌 集成到FastAPI

### 示例：REST API端点

```python
from fastapi import FastAPI, HTTPException
from services.synthesis_service import create_synthesis_service
from domain.models import TTSRequest

app = FastAPI()

# 创建全局服务实例
tts_service = create_synthesis_service(
    provider="elevenlabs",
    api_key="your_api_key",
)

@app.post("/api/tts/synthesize")
async def synthesize(request: TTSRequest):
    """文本转语音"""
    try:
        response = await tts_service.synthesize_whole(
            text=request.text,
            voice_id=request.voice_id or "EXAVITQu4vr4xnSDxMaL",  # 默认使用Sarah
            voice_settings=request.voice_settings,
        )
        
        return {
            "audio_base64": base64.b64encode(response.audio_data).decode(),
            "format": response.format.value,
            "metadata": response.metadata,
        }
    except TTSError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tts/voices")
async def get_voices():
    """获取可用语音列表"""
    voices = await tts_service.get_available_voices()
    return {"voices": [v.dict() for v in voices]}
```

### 示例：WebSocket流式端点

```python
from fastapi import WebSocket

@app.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket):
    """WebSocket流式TTS"""
    await websocket.accept()
    
    try:
        # 接收文本
        data = await websocket.receive_json()
        text = data["text"]
        voice_id = data.get("voice_id", "EXAVITQu4vr4xnSDxMaL")  # 默认Sarah
        
        # 流式合成并发送
        async for chunk in tts_service.synthesize_chunked(text, voice_id):
            await websocket.send_bytes(chunk)
        
        await websocket.close()
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
```

---

## 🛠️ 错误处理

模块定义了详细的异常层次结构：

```python
TTSError (基类)
├── ValidationError          # 输入验证错误
├── NetworkError            # 网络错误
│   ├── ConnectionError     # 连接失败
│   ├── TimeoutError        # 超时
│   └── RateLimitError      # 限流
├── ProviderError           # Provider错误
│   ├── AuthenticationError # 认证失败
│   ├── QuotaExceededError  # 配额超限
│   └── ServiceUnavailableError  # 服务不可用
└── AudioProcessingError    # 音频处理错误
```

### 错误处理示例

```python
from utils.exceptions import (
    TTSError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
)

try:
    response = await service.synthesize_whole(text="Hello", voice_id="Rachel")
except ValidationError as e:
    print(f"输入错误: {e}")
except AuthenticationError as e:
    print(f"认证失败: {e}")
except RateLimitError as e:
    print(f"限流，建议 {e.retry_after} 秒后重试")
except TTSError as e:
    print(f"TTS错误: {e.error_code} - {e.message}")
```

---

## 🚧 已知限制和TODO

### Sprint 1已完成
- ✅ ElevenLabs REST API集成
- ✅ 抽象接口设计
- ✅ 服务层实现
- ✅ 单元测试（66%覆盖率）
- ✅ 集成测试和验证脚本

### 待实现（后续Sprint）
- ⏳ ElevenLabs WebSocket客户端（等待协议文档）
- ⏳ Coqui XTTS-v2适配器（开源本地方案）
- ⏳ Redis缓存集成
- ⏳ 性能监控和指标
- ⏳ 语音克隆功能

---

## 📞 技术支持

### 常见问题

**Q: 为什么合成速度慢？**
A: 检查网络连接和`ELEVENLABS_TIMEOUT`配置，考虑启用缓存。

**Q: 如何切换到其他语音？**
A: 运行`python scripts/list_voices.py`查看所有可用语音，然后使用对应的`voice_id`。详见[语音选择指南](VOICE_GUIDE.md)。

**Q: 支持哪些语言？**
A: `eleven_multilingual_v2`模型支持29种语言，包括中文、英文、日文等。

**Q: 如何降低延迟？**
A: 使用流式合成（`synthesize_chunked`），并在获得WebSocket协议后切换到`ElevenLabsWebSocketClient`。

### 贡献指南

1. 遵循项目的代码规范（中文注释、SOLID原则）
2. 所有新功能必须附带单元测试
3. 提交前运行 `pytest tests/ -v` 确保测试通过
4. 使用 `black` 格式化代码：`black .`

---

## 📄 许可证

本项目为Accent Translator项目的一部分，遵循项目整体许可证。

---

## 🙏 致谢

- [ElevenLabs](https://elevenlabs.io) - 提供高质量TTS API
- [Coqui](https://github.com/coqui-ai/TTS) - 开源TTS解决方案
- 团队成员的协作与支持

---

**最后更新**: 2025-10-11  
**版本**: Sprint 1  
**维护者**: TTS模块负责人

