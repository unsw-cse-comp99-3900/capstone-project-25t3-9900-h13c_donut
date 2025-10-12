"""
Configuration settings for the FastAPI WebSocket application
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/accent_translator"
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External API Keys
    ELEVENLABS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # Application Settings
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Audio Processing
    TEMP_AUDIO_DIR: str = "./temp_audio"
    MAX_AUDIO_DURATION_SECONDS: int = 300
    AUDIO_CHUNK_SIZE_BYTES: int = 4096
    
    # WebSocket Settings
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
    MAX_CONNECTIONS_PER_USER: int = 3
    
    # ASR Settings (Whisper API)
    WHISPER_API_URL: str = "https://api.openai.com/v1/audio/transcriptions"
    WHISPER_MODEL: str = "whisper-1"
    
    # TTS Settings
    ELEVENLABS_API_URL: str = "https://api.elevenlabs.io/v1"
    DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()

# Ensure temp audio directory exists
os.makedirs(settings.TEMP_AUDIO_DIR, exist_ok=True)

