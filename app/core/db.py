# app/core/db.py
import os
from tortoise import Tortoise
from dotenv import load_dotenv
from pathlib import Path

# 明确从项目根目录加载 .env
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

DB_URL = os.getenv("DATABASE_URL", "postgres://postgres:Postgre@127.0.0.1:5432/fat")

# Tortoise 配置字典（Aerich 也会用到）
TORTOISE_ORM = {
    "connections": {"default": DB_URL},
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "app.models.conversation",
                "app.models.transcript",
                "aerich.models",   # 必须：让 Aerich 管理迁移表
            ],
            "default_connection": "default",
        },
    },
}

async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    # 生产环境不要自动生成表；开发期可用 generate_schemas=True 快速起步
    # await Tortoise.generate_schemas()

async def close_db():
    await Tortoise.close_connections()
