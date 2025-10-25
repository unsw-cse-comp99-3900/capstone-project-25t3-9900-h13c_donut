# app/config.py
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的环境变量

class Settings(BaseModel):
    # General app settings
    APP_NAME: str = "Fast Accent Translator API"
    env: str = os.getenv("ENV", "dev")
    
    # Host & Port settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # CORS origins for frontend
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # OpenAI Whisper API Settings (for ASR)
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    whisper_api_url: str = os.getenv("WHISPER_API_URL", "https://api.openai.com/v1/audio/transcriptions")
    whisper_model: str = os.getenv("WHISPER_MODEL", "whisper-1")
    
    # ElevenLabs API Settings (for TTS)
    eleven_api_key: str | None = os.getenv("ELEVENLABS_API_KEY")
    eleven_api_base: str = os.getenv("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1")
    default_voice_id: str = os.getenv("DEFAULT_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
    # Voice Mapping for accents
    voice_map: dict[str, str] = {
        "American English": os.getenv("VOICE_ID_AMERICAN", ""),
        "Australia English": os.getenv("VOICE_ID_AUSTRALIA", ""),
        "British English": os.getenv("VOICE_ID_BRITISH", ""),
        "Chinese English": os.getenv("VOICE_ID_CHINESE", ""),
        "India English": os.getenv("VOICE_ID_INDIA", ""),
    }

settings = Settings()  # 实例化配置
