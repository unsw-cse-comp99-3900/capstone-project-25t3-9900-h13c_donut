from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # OpenAI Whisper（URL 直调所需）
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    whisper_api_url: str = os.getenv("WHISPER_API_URL", "https://api.openai.com/v1/audio/transcriptions")
    whisper_model: str = os.getenv("WHISPER_MODEL", "whisper-1")

    # ElevenLabs（如果你已有 TTS，不涉及此次改动）
    eleven_api_key: str | None = os.getenv("ELEVENLABS_API_KEY")
    eleven_api_base: str = os.getenv("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1")
    default_voice_id: str = os.getenv("DEFAULT_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    voice_map: dict[str, str] = {
        "American English": os.getenv("VOICE_ID_AMERICAN", ""),
        "Australia English": os.getenv("VOICE_ID_AUSTRALIA", ""),
        "British English": os.getenv("VOICE_ID_BRITISH", ""),
        "Chinese English": os.getenv("VOICE_ID_CHINESE", ""),
        "India English": os.getenv("VOICE_ID_INDIA", ""),
    }

settings = Settings()
