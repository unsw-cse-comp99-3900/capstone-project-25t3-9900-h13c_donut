# TTS模块架构文档

## 📐 架构概览

本文档详细说明TTS模块的架构设计、技术决策和实现细节。

---

## 🏗️ 分层架构

TTS模块采用经典的**分层架构**，从上到下分为：

```
┌─────────────────────────────────────────────────┐
│           应用层（FastAPI等）                    │
├─────────────────────────────────────────────────┤
│           服务层（Business Logic）               │
│      - SynthesisService（合成服务）             │
│      - OrchestratorService（口音映射，预留）     │
├─────────────────────────────────────────────────┤
│           领域层（Domain Models）                │
│      - TTSRequest, TTSResponse（模型）          │
│      - TTSClientInterface（接口）               │
├─────────────────────────────────────────────────┤
│         适配器层（Adapters/Gateways）            │
│      - ElevenLabsClient（REST实现）             │
│      - ElevenLabsWebSocketClient（预留）        │
├─────────────────────────────────────────────────┤
│         基础设施层（Infrastructure）              │
│      - Config（配置管理）                        │
│      - Utils（异常、日志等）                     │
└─────────────────────────────────────────────────┘
```

### 各层职责

#### 1. 领域层（Domain Layer）
- **职责**：定义核心业务概念和规则
- **文件**：`domain/models.py`, `domain/interfaces.py`
- **特点**：
  - 不依赖任何外部库（除Pydantic）
  - 定义抽象接口，不关心具体实现
  - 不可变模型（`frozen=True`）

#### 2. 适配器层（Adapter Layer）
- **职责**：封装外部TTS服务的API调用
- **文件**：`adapters/elevenlabs_client.py`
- **特点**：
  - 实现领域层定义的接口
  - 处理API特定的认证、重试、错误映射
  - 隔离外部依赖

#### 3. 服务层（Service Layer）
- **职责**：实现业务逻辑和编排
- **文件**：`services/synthesis_service.py`
- **特点**：
  - 依赖抽象接口，而非具体实现
  - 提供高层次API
  - 实现缓存、监控等横切关注点

#### 4. 基础设施层（Infrastructure Layer）
- **职责**：提供通用工具和配置
- **文件**：`config/settings.py`, `utils/exceptions.py`
- **特点**：
  - 配置管理
  - 异常定义
  - 日志、监控（预留）

---

## 🎯 设计原则

### SOLID原则的应用

#### 1. 单一职责原则（SRP）
```python
# ✅ 每个类只负责一件事

# TTSClient：只负责API通信
class ElevenLabsClient:
    async def synthesize(self, request): ...

# SynthesisService：只负责业务逻辑
class SynthesisService:
    async def synthesize_whole(self, text, voice_id): ...

# Settings：只负责配置管理
class Settings(BaseSettings):
    ELEVENLABS_API_KEY: str
```

#### 2. 开闭原则（OCP）
```python
# ✅ 对扩展开放，对修改封闭

# 添加新的TTS provider不需要修改现有代码
class CoquiClient(TTSClientInterface):
    async def synthesize(self, request): ...

service = SynthesisService(tts_client=CoquiClient())  # 无需修改服务层
```

#### 3. 里氏替换原则（LSP）
```python
# ✅ 所有TTSClientInterface的实现都可以互换

def use_tts(client: TTSClientInterface):
    response = await client.synthesize(request)
    # 无论client是ElevenLabsClient还是CoquiClient，都能工作

use_tts(ElevenLabsClient())  # ✅
use_tts(CoquiClient())       # ✅
use_tts(MockClient())        # ✅ 测试时
```

#### 4. 接口隔离原则（ISP）
```python
# ✅ 分离不同能力的接口

class TTSClientInterface(ABC):
    """基础接口：所有客户端都必须实现"""
    async def synthesize(self, request): ...

class StreamingTTSClientInterface(TTSClientInterface):
    """流式接口：只有支持流式的客户端才实现"""
    async def synthesize_stream(self, request): ...
```

#### 5. 依赖倒置原则（DIP）
```python
# ✅ 高层模块依赖抽象，而非具体实现

# ❌ 错误：直接依赖具体实现
class SynthesisService:
    def __init__(self):
        self.client = ElevenLabsClient()  # 绑死了

# ✅ 正确：依赖抽象接口
class SynthesisService:
    def __init__(self, tts_client: TTSClientInterface):
        self.client = tts_client  # 可注入任何实现
```

---

## 🔄 数据流

### 同步合成流程

```
用户请求
   ↓
[SynthesisService.synthesize_whole()]
   ↓
创建TTSRequest（领域模型）
   ↓
[ElevenLabsClient.synthesize()]
   ↓
HTTP POST → ElevenLabs API
   ↓
接收完整音频（bytes）
   ↓
创建TTSResponse（领域模型）
   ↓
（可选）写入缓存
   ↓
返回给用户
```

### 流式合成流程

```
用户请求
   ↓
[SynthesisService.synthesize_chunked()]
   ↓
[ElevenLabsClient.synthesize_stream()]
   ↓
HTTP POST → ElevenLabs API
   ↓
接收完整音频
   ↓
按chunk_size分块
   ↓
逐块yield给用户
   ↓
用户实时处理（播放/转发）
```

---

## 🔌 可扩展点

### 1. 添加新的TTS Provider

**步骤**：
1. 创建新的适配器类，实现`TTSClientInterface`
2. 在配置中添加provider相关设置
3. 在工厂函数中添加分支

**示例**：添加Google Cloud TTS

```python
# adapters/google_tts_client.py
from domain.interfaces import TTSClientInterface

class GoogleTTSClient(TTSClientInterface):
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        # 调用Google Cloud TTS API
        ...

# services/synthesis_service.py
def create_synthesis_service(provider: str, **kwargs):
    if provider == "google":
        from adapters.google_tts_client import GoogleTTSClient
        client = GoogleTTSClient(**kwargs)
        return SynthesisService(tts_client=client)
```

### 2. 添加Redis缓存

**步骤**：
1. 安装`redis`库
2. 在`SynthesisService`中替换内存缓存为Redis

```python
import redis.asyncio as redis

class SynthesisService:
    def __init__(self, tts_client, redis_client=None):
        self.client = tts_client
        self.redis = redis_client
    
    async def _get_from_cache(self, cache_key):
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                return pickle.loads(cached)
        return None
```

### 3. 添加监控指标

```python
# utils/metrics.py
from prometheus_client import Counter, Histogram

tts_requests_total = Counter('tts_requests_total', 'Total TTS requests')
tts_latency = Histogram('tts_latency_seconds', 'TTS request latency')

# 在SynthesisService中使用
async def synthesize_whole(self, ...):
    tts_requests_total.inc()
    with tts_latency.time():
        response = await self.client.synthesize(request)
```

---

## 🧪 测试策略

### 测试金字塔

```
        /\
       /  \      E2E测试（手动/集成测试）
      /    \     - 真实API调用
     /------\    - 验证端到端流程
    /        \
   /  集成测试 \   - 多组件协作
  /  (可选)    \  - Mock外部API
 /--------------\
/   单元测试      \ - 快速、隔离
/  (38个测试)     \ - Mock所有依赖
/------------------\
```

### 单元测试（Unit Tests）
- **目标**：测试各组件的独立功能
- **Mock**：所有外部依赖
- **覆盖率**：66%（Sprint 1）

```python
# tests/test_synthesis_service.py
async def test_synthesize_success(mock_tts_client):
    service = SynthesisService(tts_client=mock_tts_client)
    response = await service.synthesize_whole(text="Hello", voice_id="test")
    assert response.audio_data == b"MOCK_AUDIO"
```

### 集成测试（Integration Tests）
- **目标**：测试组件协作
- **要求**：真实API密钥
- **运行**：手动触发（`-m integration`）

```python
# tests/test_integration.py
@pytest.mark.integration
async def test_real_api():
    client = ElevenLabsClient(api_key=os.getenv("ELEVENLABS_API_KEY"))
    response = await client.synthesize(request)
    assert len(response.audio_data) > 1000
```

---

## 🔐 安全考虑

### 1. API密钥管理
- ✅ 使用环境变量，不硬编码
- ✅ `.env`文件加入`.gitignore`
- ✅ 日志中隐藏敏感信息

### 2. 输入验证
- ✅ 使用Pydantic验证所有输入
- ✅ 文本长度限制（5000字符）
- ✅ 参数范围检查

### 3. 错误处理
- ✅ 不泄露内部实现细节
- ✅ 统一的错误响应格式
- ✅ 详细的日志记录

---

## 🚀 性能优化

### 已实现
1. **连接池**：httpx的异步连接池
2. **重试机制**：指数退避，避免雪崩
3. **内存缓存**：避免重复合成相同文本

### 待优化（后续Sprint）
1. **Redis缓存**：分布式缓存，跨实例共享
2. **请求合并**：批量合成，减少API调用
3. **预加载**：常用语音预合成
4. **CDN**：音频文件CDN加速

---

## 📊 监控和可观测性（预留）

### 指标（Metrics）
- `tts_requests_total`: 总请求数
- `tts_requests_duration`: 请求延迟
- `tts_cache_hit_rate`: 缓存命中率
- `tts_errors_total`: 错误数（按类型）

### 日志（Logging）
```python
logger.info(
    "TTS合成成功",
    extra={
        "text_length": len(text),
        "voice_id": voice_id,
        "duration_ms": duration_ms,
        "audio_size": len(audio_data),
    }
)
```

### 追踪（Tracing）
- 使用OpenTelemetry追踪请求链路
- 集成到整个Accent Translator项目的追踪系统

---

## 🔄 演进路线

### Sprint 1（已完成）
- ✅ 基础架构搭建
- ✅ ElevenLabs REST集成
- ✅ 单元测试

### Sprint 2（计划中）
- ⏳ ElevenLabs WebSocket
- ⏳ Coqui XTTS-v2
- ⏳ Redis缓存

### Sprint 3（规划中）
- ⏳ 性能优化
- ⏳ 监控告警
- ⏳ 语音克隆

---

## 🤝 与其他模块的集成

### 与ASR模块
```python
# 流程：语音 → ASR → TTS
audio_input = ...
text = await asr_service.transcribe(audio_input)
audio_output = await tts_service.synthesize_whole(text, voice_id="new_accent")
```

### 与Orchestrator模块
```python
# Orchestrator决定口音映射
detected_accent = "british"
target_voice = orchestrator.map_accent_to_voice(detected_accent, target_accent="american")
audio = await tts_service.synthesize_whole(text, voice_id=target_voice)
```

### 与Stream模块
```python
# 实时流式合成和混音
async for tts_chunk in tts_service.synthesize_chunked(text, voice_id):
    mixed_audio = stream_service.mix(tts_chunk, background_audio)
    await websocket.send_bytes(mixed_audio)
```

---

## 📝 技术债务和改进点

### 当前技术债务
1. 内存缓存不适合生产环境（需要Redis）
2. 缺少监控和指标
3. 错误重试策略较简单（可考虑熔断器）

### 改进计划
1. **短期**（Sprint 2）：
   - 实现Redis缓存
   - 添加基础监控指标
   - 完善错误处理

2. **中期**（Sprint 3-4）：
   - 实现WebSocket真正的流式
   - 添加语音克隆功能
   - 性能压测和优化

3. **长期**：
   - 支持更多TTS provider
   - 实现智能降级和容错
   - A/B测试框架

---

**文档版本**: 1.0  
**最后更新**: 2025-10-11  
**维护者**: TTS模块负责人

