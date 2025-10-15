# app/core/config.py
from pydantic import BaseModel
import os

class Settings(BaseModel):
    APP_NAME: str = "Fast Accent Translator API"
    ENV: str = os.getenv("ENV", "dev")
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

settings = Settings()
