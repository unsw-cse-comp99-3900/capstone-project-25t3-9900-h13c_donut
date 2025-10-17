# app/core/config.py
import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "Fast Accent Translator API"
    ENV: str = os.getenv("ENV", "dev")
    # 这里列出你前端的本地地址（注意：有 Cookie 时不能用 "*"）
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

settings = Settings()
