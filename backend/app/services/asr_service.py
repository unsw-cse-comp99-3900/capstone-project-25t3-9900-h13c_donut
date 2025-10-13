"""
ASR (Automatic Speech Recognition) Service
Interface for calling ASR processing (will be implemented by BE-5 team member)
"""

import logging
import httpx
from typing import Dict, Optional, List
import aiofiles
import json

from app.config import settings

logger = logging.getLogger(__name__)

class ASRService:
    """
    ASR service for speech-to-text conversion
    This is a placeholder interface that will call the actual ASR module developed by BE-5
    """
    
    def __init__(self):
        # BE-5 ASR服务配置
        self.asr_service_url = settings.ASR_SERVICE_URL
        self.asr_endpoint = settings.ASR_INTERNAL_ENDPOINT
        self.asr_timeout = settings.ASR_TIMEOUT_SECONDS
        
        # 备用Whisper API配置
        self.whisper_api_url = settings.WHISPER_API_URL
        self.api_key = settings.OPENAI_API_KEY
        
    async def transcribe_audio(self, audio_file_path: str, model: str = "free") -> Optional[Dict]:
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to the audio file
            model: Model type ("free" or "paid")
            
        Returns:
            Dict containing transcription result:
            {
                "text": "transcribed text",
                "segments": [
                    {
                        "start": 0.0,
                        "end": 2.5,
                        "text": "Hello world"
                    }
                ],
                "confidence": 0.95
            }
        """
        try:
            logger.info(f"Starting ASR transcription for: {audio_file_path}")
            
            if model == "paid" and self.api_key:
                # Use OpenAI Whisper API for paid model
                result = await self._transcribe_with_whisper_api(audio_file_path)
            else:
                # Use local/free ASR service (placeholder - will be implemented by BE-5)
                result = await self._transcribe_with_local_asr(audio_file_path)
            
            logger.info(f"ASR transcription completed: {len(result.get('text', ''))} characters")
            return result
            
        except Exception as e:
            logger.error(f"ASR transcription failed: {e}")
            return None
    
    async def _transcribe_with_whisper_api(self, audio_file_path: str) -> Dict:
        """
        Transcribe using OpenAI Whisper API
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcription result
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with aiofiles.open(audio_file_path, 'rb') as audio_file:
                    audio_data = await audio_file.read()
                
                files = {
                    'file': ('audio.wav', audio_data, 'audio/wav')
                }
                
                data = {
                    'model': settings.WHISPER_MODEL,
                    'response_format': 'verbose_json',
                    'timestamp_granularities[]': 'segment'
                }
                
                headers = {
                    'Authorization': f'Bearer {self.api_key}'
                }
                
                response = await client.post(
                    self.whisper_api_url,
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Convert to our standard format
                    return {
                        "text": result.get("text", ""),
                        "segments": [
                            {
                                "start": seg.get("start", 0),
                                "end": seg.get("end", 0),
                                "text": seg.get("text", "")
                            }
                            for seg in result.get("segments", [])
                        ],
                        "confidence": None  # Whisper API doesn't provide confidence
                    }
                else:
                    logger.error(f"Whisper API error: {response.status_code} - {response.text}")
                    return self._get_fallback_result()
                    
        except Exception as e:
            logger.error(f"Whisper API transcription error: {e}")
            return self._get_fallback_result()
    
    async def _transcribe_with_local_asr(self, audio_file_path: str) -> Dict:
        """
        Transcribe using BE-5's ASR service
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcription result
        """
        try:
            logger.info(f"Calling BE-5 ASR service: {self.asr_service_url}{self.asr_endpoint}")
            
            # 准备文件上传
            async with aiofiles.open(audio_file_path, 'rb') as audio_file:
                audio_data = await audio_file.read()
            
            files = {
                'file': ('audio.wav', audio_data, 'audio/wav')
            }
            
            # 调用BE-5的ASR服务
            async with httpx.AsyncClient(timeout=self.asr_timeout) as client:
                response = await client.post(
                    f"{self.asr_service_url}{self.asr_endpoint}",
                    files=files
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        # BE-5返回格式: {"success": True, "data": {"text": "...", "segments": [...]}}
                        data = result.get("data", {})
                        
                        # 转换为我们的标准格式
                        segments = []
                        for seg in data.get("segments", []):
                            segments.append({
                                "start": seg.get("startMs", 0) / 1000.0,  # 转换毫秒到秒
                                "end": seg.get("endMs", 0) / 1000.0,
                                "text": seg.get("text", "")
                            })
                        
                        return {
                            "text": data.get("text", ""),
                            "segments": segments,
                            "confidence": 0.9  # BE-5暂时不提供confidence，使用默认值
                        }
                    else:
                        # BE-5返回错误
                        error_msg = result.get("error", {}).get("message", "Unknown error")
                        logger.error(f"BE-5 ASR service error: {error_msg}")
                        return self._get_fallback_result()
                else:
                    logger.error(f"BE-5 ASR service HTTP error: {response.status_code} - {response.text}")
                    return self._get_fallback_result()
                    
        except httpx.TimeoutException:
            logger.error(f"BE-5 ASR service timeout after {self.asr_timeout} seconds")
            return self._get_fallback_result()
        except httpx.ConnectError:
            logger.error(f"Cannot connect to BE-5 ASR service at {self.asr_service_url}")
            return self._get_fallback_result()
        except Exception as e:
            logger.error(f"BE-5 ASR service error: {e}")
            return self._get_fallback_result()
    
    def _get_fallback_result(self) -> Dict:
        """
        Get fallback result when transcription fails
        
        Returns:
            Fallback transcription result
        """
        return {
            "text": "Sorry, transcription failed. Please try again.",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Sorry, transcription failed. Please try again."
                }
            ],
            "confidence": 0.0
        }
    
    async def check_service_health(self) -> bool:
        """
        Check if BE-5's ASR service is healthy
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            logger.info(f"Checking BE-5 ASR service health: {self.asr_service_url}")
            
            # 尝试连接到BE-5的ASR服务
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 可以尝试访问根路径或健康检查端点
                response = await client.get(f"{self.asr_service_url}/")
                
                if response.status_code in [200, 404]:  # 404也表示服务在运行
                    logger.info("BE-5 ASR service is healthy")
                    return True
                else:
                    logger.warning(f"BE-5 ASR service returned status: {response.status_code}")
                    return False
                    
        except httpx.ConnectError:
            logger.error(f"Cannot connect to BE-5 ASR service at {self.asr_service_url}")
            return False
        except Exception as e:
            logger.error(f"BE-5 ASR service health check failed: {e}")
            return False


