# FastAPI WebSocket Server - BE-4 WebSocket 控制层

这是 Fast Accent Translator 项目的 WebSocket 控制层实现，负责处理实时音频流控制和协调 ASR/TTS 服务。

## 功能特性

### 核心功能
- ✅ **WebSocket 连接管理**: 支持多用户并发连接，连接数限制和生命周期管理
- ✅ **JWT 认证**: WebSocket 连接的安全认证机制
- ✅ **消息协议处理**: 支持 init/audio/stop 消息类型
- ✅ **伪流式处理**: 批处理 + 分块传输模拟实时流处理
- ✅ **心跳机制**: 自动检测和清理断开的连接
- ✅ **错误处理**: 完善的错误处理和恢复机制

### 消息协议
支持以下 WebSocket 消息类型：

#### 客户端 → 服务器
- `init`: 初始化会话，选择口音和模型
- `audio`: 发送音频数据块
- `stop`: 停止录音并触发处理
- `pong`: 心跳响应

#### 服务器 → 客户端
- `init_success`: 会话初始化成功
- `partial`: 部分转录结果
- `final`: 最终转录结果
- `tts_chunk`: TTS 音频数据块
- `done`: 会话处理完成
- `error`: 错误消息
- `ping`: 心跳检测

## 项目结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 镜像配置
├── docker-compose.yml     # Docker Compose 配置
├── Makefile              # 开发工具命令
├── app/
│   ├── __init__.py
│   ├── config.py         # 应用配置
│   ├── auth/
│   │   ├── __init__.py
│   │   └── dependencies.py  # JWT 认证依赖
│   ├── models/
│   │   ├── __init__.py
│   │   └── responses.py     # 响应模型定义
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asr_service.py   # ASR 服务接口
│   │   ├── tts_service.py   # TTS 服务接口
│   │   └── audio_processor.py # 音频处理工具
│   └── websocket/
│       ├── __init__.py
│       ├── manager.py       # WebSocket 连接管理
│       └── handlers.py      # WebSocket 消息处理
└── temp_audio/             # 临时音频文件目录
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd backend

# 安装依赖
make install

# 初始化项目
make init
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/accent_translator
REDIS_URL=redis://localhost:6379

# JWT 配置
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 外部 API 密钥
ELEVENLABS_API_KEY=your-elevenlabs-api-key
OPENAI_API_KEY=your-openai-api-key

# 应用设置
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

### 3. 启动服务

#### 开发模式
```bash
make dev
```

#### Docker 模式
```bash
make up
```

服务将在 `http://localhost:8000` 启动，WebSocket 端点为 `ws://localhost:8000/ws/realtime`

## API 文档

### WebSocket 连接

**端点**: `ws://localhost:8000/ws/realtime`

**查询参数**:
- `token`: JWT 认证令牌
- `session_id`: 可选，用于恢复现有会话

### 消息示例

#### 1. 初始化会话
```json
{
  "type": "init",
  "sessionId": "optional-session-id",
  "accent": "us",
  "model": "free"
}
```

#### 2. 发送音频数据
```json
{
  "type": "audio",
  "data": "base64-encoded-audio-data",
  "sequence": 1
}
```

#### 3. 停止录音
```json
{
  "type": "stop"
}
```

#### 4. 服务器响应示例
```json
{
  "type": "partial",
  "text": "Hello world",
  "sequence": 0,
  "startMs": 0,
  "endMs": 1000
}
```

## 开发指南

### 与其他模块的集成

#### ASR 服务集成 (BE-5)
`app/services/asr_service.py` 提供了 ASR 服务的接口，目前包含：
- OpenAI Whisper API 集成（付费模式）
- 本地 ASR 服务接口（免费模式，待 BE-5 实现）

#### TTS 服务集成 (BE-6)
`app/services/tts_service.py` 提供了 TTS 服务的接口，目前包含：
- ElevenLabs API 集成（付费模式）
- Coqui XTTS 接口（免费模式，待 BE-6 实现）

### 测试

```bash
# 运行测试（待实现）
make test

# 检查依赖
make check-deps

# 查看日志
make logs
```

### 部署

```bash
# 构建 Docker 镜像
make build

# 启动生产环境
make up

# 停止服务
make down
```

## 配置说明

### 主要配置项

- `WEBSOCKET_HEARTBEAT_INTERVAL`: 心跳间隔（秒）
- `MAX_CONNECTIONS_PER_USER`: 每用户最大连接数
- `MAX_AUDIO_DURATION_SECONDS`: 最大音频时长
- `AUDIO_CHUNK_SIZE_BYTES`: 音频分块大小
- `TEMP_AUDIO_DIR`: 临时音频文件目录

### 外部服务配置

- **OpenAI Whisper API**: 需要 `OPENAI_API_KEY`
- **ElevenLabs TTS**: 需要 `ELEVENLABS_API_KEY`
- **数据库**: PostgreSQL 连接字符串
- **缓存**: Redis 连接字符串

## 架构设计

### 伪流式处理流程

1. **音频收集**: WebSocket 接收音频块并缓存
2. **批处理**: 收到 stop 消息后，合并音频并调用 ASR
3. **分段传输**: 将 ASR 结果分段发送（模拟 partial）
4. **TTS 处理**: 调用 TTS 服务生成语音
5. **分块传输**: 将 TTS 音频分块发送
6. **会话结束**: 发送 done 消息并清理资源

### 连接管理

- **多用户支持**: 每个用户可有多个并发连接
- **会话隔离**: 每个会话独立处理，互不干扰
- **资源清理**: 自动清理断开连接和临时文件
- **错误恢复**: 连接断开时自动清理相关资源

## 故障排除

### 常见问题

1. **连接被拒绝**: 检查 JWT token 是否有效
2. **音频处理失败**: 检查外部 API 密钥配置
3. **连接断开**: 查看心跳机制和网络稳定性
4. **内存占用高**: 检查临时文件清理和连接数限制

### 日志查看

```bash
# 查看实时日志
make logs

# 查看特定服务日志
docker-compose logs fastapi-backend
```
