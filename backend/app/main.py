# app/main.py
import os
import shutil
import logging
from pathlib import Path
from glob import glob

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 你的配置与 DB
from app.config import settings
from app.core.db import init_db, close_db

from app.api.v1.routers import auth, accents, session as session_router, conversations, admin


from app.api.v1.routers.ws_text import router as ws_text_router
from app.api.v1.routers.ws_upload import router as ws_upload_router
from app.api.v1.routers.ws_tts import router as ws_tts_router

logger = logging.getLogger("uvicorn.error")

def _ensure_ffmpeg_on_path() -> None:
    """
    目标：不写死绝对路径；在启动时自动把常见安装目录加入 PATH。
    优先级：
      1) 环境变量 FFMPEG_DIR / FFPROBE_DIR（可配置为目录，不是exe）
      2) winget 常见安装目录（Gyan.FFmpeg）
      3) Chocolatey 常见安装目录
      4) Program Files 常见安装目录
    找到后将其 bin 目录 prepend 到 os.environ['PATH']，再检测 which(ffmpeg)。
    """
    # 已经可用就不处理
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        logger.info("[ffmpeg] found on PATH: ffmpeg=%s ffprobe=%s",
                    shutil.which("ffmpeg"), shutil.which("ffprobe"))
        return

    candidates: list[Path] = []

    # 1) 显式目录（团队可在 .env 配置 FFMPEG_DIR / FFPROBE_DIR）
    ffmpeg_dir = os.getenv("FFMPEG_DIR")
    ffprobe_dir = os.getenv("FFPROBE_DIR")
    if ffmpeg_dir:
        p = Path(ffmpeg_dir)
        candidates.append(p if p.name.lower() == "bin" else p / "bin")
    if ffprobe_dir:
        p = Path(ffprobe_dir)
        candidates.append(p if p.name.lower() == "bin" else p / "bin")

    # 2) winget 路径（Gyan.FFmpeg 的典型结构）
    local = os.getenv("LOCALAPPDATA", "")
    if local:
        winget_root = Path(local) / "Microsoft" / "WinGet" / "Packages"
        # 例如：.../Gyan.FFmpeg_8.0.0.0_x64__xxx/ffmpeg-8.0-full_build/bin
        for pkg_dir in winget_root.glob("Gyan.FFmpeg_*"):
            for ff_root in pkg_dir.glob("ffmpeg-*"):
                candidates.append(ff_root / "bin")

    # 3) Chocolatey
    candidates += [
        Path(r"C:\ProgramData\chocolatey\bin"),
        Path(r"C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin"),
    ]

    # 4) Program Files 经典安装
    candidates += [
        Path(r"C:\Program Files\ffmpeg\bin"),
        Path(r"C:\Program Files (x86)\ffmpeg\bin"),
    ]

    # 追加到 PATH（只要目录存在且里面有 ffmpeg.exe 即加入）
    added = []
    for c in candidates:
        try:
            if c.is_dir() and (c / "ffmpeg.exe").exists():
                # prepend，确保优先生效
                os.environ["PATH"] = str(c) + os.pathsep + os.environ.get("PATH", "")
                added.append(str(c))
        except Exception:
            pass

    logger.info("[ffmpeg] PATH extended by: %s", added if added else "[]")
    logger.info("[ffmpeg] which(ffmpeg)=%s", shutil.which("ffmpeg"))
    logger.info("[ffmpeg] which(ffprobe)=%s", shutil.which("ffprobe"))

app = FastAPI(title=settings.APP_NAME)

# CORS（带 Cookie）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    # 先确保 ffmpeg 在 PATH（为 ASR 转码做准备）
    _ensure_ffmpeg_on_path()
    # 你的 DB 初始化
    await init_db()

@app.on_event("shutdown")
async def on_shutdown():
    await close_db()

# REST
app.include_router(auth.router, prefix="/api/v1")
app.include_router(accents.router, prefix="/api/v1")
app.include_router(session_router.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

# WebSocket（保持他原装装饰器路径）
app.include_router(ws_text_router)
app.include_router(ws_upload_router)
app.include_router(ws_tts_router)

@app.get("/healthz")
def healthz():
    return {"ok": True}
