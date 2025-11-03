# SystemX 部署和运行指南

本文档介绍如何在本地开发环境和生产环境中部署和运行 SystemX 项目。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [后端配置和运行](#后端配置和运行)
- [前端配置和运行](#前端配置和运行)
- [管理员功能说明](#管理员功能说明)
- [生产环境部署](#生产环境部署)
- [常见问题](#常见问题)

---

## 系统要求

### 必需软件

- **Python**: 3.10+ (后端)
- **Node.js**: 18+ (前端)
- **PostgreSQL**: 14+ (数据库)
- **FFmpeg**: 用于音频处理

### 外部服务

- **OpenAI API**: 语音识别 (Whisper)
- **ElevenLabs API**: 文本转语音 (TTS)

---

## 快速开始

### 1. 克隆仓库

```bash
git clone git@github.com:Rachel-Huang77/SystemX.git
cd SystemX
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env
# 编辑 .env 文件，填入必要的配置

# 初始化数据库
aerich init-db

# 启动后端服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将运行在 `http://localhost:8000`

### 3. 前端设置

```bash
cd ../frontend

# 安装依赖
npm install

# 复制环境配置
cp .env.example .env
# 编辑 .env 文件（一般使用默认值即可）

# 启动前端开发服务器
npm run dev
```

前端服务将运行在 `http://localhost:5173`

---

## 后端配置和运行

### 环境变量配置 (.env)

在 `backend/.env` 文件中配置以下变量：

```bash
# 数据库配置
DATABASE_URL=postgres://用户名:密码@localhost:5432/systemx

# JWT 配置
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# 管理员账户（首次运行时自动创建）
ADMIN_PASSWORD=your-admin-password

# OpenAI API 配置
OPENAI_API_KEY=sk-your-openai-api-key
WHISPER_MODEL=whisper-1

# ElevenLabs API 配置
ELEVENLABS_API_KEY=your-elevenlabs-api-key
VOICE_ID_AMERICAN=xxxxx
VOICE_ID_AUSTRALIA=xxxxx
VOICE_ID_BRITISH=xxxxx
VOICE_ID_CHINESE=xxxxx
VOICE_ID_INDIAN=xxxxx

# CORS 配置
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 数据库迁移

```bash
# 初始化 Aerich（仅第一次）
aerich init -t app.core.db.TORTOISE_ORM

# 初始化数据库
aerich init-db

# 后续迁移（如果数据库模型有更新）
aerich migrate --name "describe_your_changes"
aerich upgrade
```

### 启动后端

#### 开发模式（带热重载）

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 生产模式

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 验证后端运行

访问以下端点验证后端是否正常运行：

- **健康检查**: `http://localhost:8000/healthz`
- **API 文档**: `http://localhost:8000/docs`

---

## 前端配置和运行

### 环境变量配置 (.env)

在 `frontend/.env` 文件中配置以下变量：

```bash
# API Base URL (后端 API 地址)
VITE_API_BASE_URL=http://localhost:8000

# WebSocket Base URL (WebSocket 服务地址)
VITE_WS_BASE_URL=ws://localhost:8000

# 是否使用本地语音识别（0=使用后端，1=使用浏览器本地）
VITE_USE_LOCAL_SPEECH=0
```

### 启动前端

#### 开发模式

```bash
npm run dev
```

前端将运行在 `http://localhost:5173`

#### 构建生产版本

```bash
npm run build
```

构建产物将生成在 `dist/` 目录。

#### 预览生产构建

```bash
npm run preview
```

---

## 管理员功能说明

### 默认管理员账户

系统在第一次启动时会自动创建管理员账户，使用后端 `.env` 文件中配置的 `ADMIN_PASSWORD`。

### 管理员登录

1. 访问 `http://localhost:5173/login`
2. 使用管理员账户登录（用户名由后端配置决定，默认可能是 `admin`）
3. 登录成功后自动跳转到管理员仪表盘 `/admin`

### 管理员功能

#### 1. 用户管理

- **查看用户列表**: 显示所有注册用户
- **搜索用户**: 按用户名或邮箱搜索
- **编辑用户**: 修改用户名、邮箱、角色
- **删除用户**: 删除指定用户（不能删除自己和最后一个管理员）
- **重置密码**: 为用户重置密码

#### 2. 密钥管理

- **批量生成密钥**:
  - 支持生成 1-200 个密钥
  - 可设置密钥类型（paid/trial/promotion）
  - 可设置过期天数（留空表示永久有效）
  - 可自定义密钥前缀（用于标识渠道）
- **导出密钥**: 生成的密钥可复制或导出为文本文件
- **密钥格式**: `PREFIX-XXXX-XXXX-XXXX-XXXX`

**重要**: 密钥明文仅在生成时显示一次，请及时保存！

---

## 生产环境部署

### 后端部署

#### 使用 Docker

```bash
cd backend
docker build -t systemx-backend .
docker run -p 8000:8000 --env-file .env systemx-backend
```

#### 使用 systemd

创建 `/etc/systemd/system/systemx-backend.service`:

```ini
[Unit]
Description=SystemX Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/SystemX/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable systemx-backend
sudo systemctl start systemx-backend
```

### 前端部署

#### 构建并部署到 Nginx

```bash
# 构建前端
cd frontend
npm run build

# 复制到 Nginx 目录
sudo cp -r dist/* /var/www/systemx/

# 配置 Nginx
sudo nano /etc/nginx/sites-available/systemx
```

Nginx 配置示例：

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/systemx;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

启用并重启 Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/systemx /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 常见问题

### 1. 后端启动失败

**问题**: `ModuleNotFoundError: No module named 'app'`

**解决**: 确保在 `backend/` 目录下运行命令，且虚拟环境已激活。

### 2. 数据库连接失败

**问题**: `asyncpg.exceptions.InvalidCatalogNameError: database "systemx" does not exist`

**解决**:
```bash
# 创建数据库
psql -U postgres
CREATE DATABASE systemx;
\q

# 重新运行迁移
aerich init-db
```

### 3. 前端无法连接后端

**问题**: `Network error` 或 `CORS` 错误

**解决**:
- 检查后端是否正常运行：`curl http://localhost:8000/healthz`
- 检查 `.env` 文件中的 `VITE_API_BASE_URL` 配置
- 检查后端 `CORS_ORIGINS` 配置是否包含前端地址

### 4. 管理员账户无法登录

**问题**: 使用管理员密码无法登录

**解决**:
- 检查后端 `.env` 文件中的 `ADMIN_PASSWORD` 是否配置
- 重启后端服务，确保管理员账户已创建
- 查看后端日志确认管理员创建过程

### 5. 密钥生成后无法使用

**问题**: 普通用户输入密钥后提示"密钥无效"

**解决**:
- 确保密钥复制完整，包含所有破折号（-）
- 密钥只能使用一次，检查是否已被使用
- 检查密钥是否已过期

---

## 技术支持

如有问题，请访问：
- GitHub Issues: https://github.com/Rachel-Huang77/SystemX/issues
- 项目文档: 参见 `README.md`

---

**文档版本**: 1.0
**最后更新**: 2025-01-03
