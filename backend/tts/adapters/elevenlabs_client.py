"""
ElevenLabs REST API 适配器

实现了ElevenLabs TTS服务的REST API调用，支持：
- 文本转语音（多种模型和语音）
- 语音列表查询
- 健康检查
- 自动重试（指数退避）
- 详细的错误处理和映射

API文档: https://elevenlabs.io/docs/api-reference
"""
from __future__ import annotations
import httpx
import asyncio
from typing import List, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from domain.interfaces import StreamingTTSClientInterface
from domain.models import (
    TTSRequest,
    TTSResponse,
    VoiceInfo,
    AudioFormat,
)
from utils.exceptions import (
    NetworkError,
    TimeoutError,
    create_http_error,
    TTSError,
)


class ElevenLabsClient(StreamingTTSClientInterface):
    """
    ElevenLabs REST API客户端
    
    遵循依赖倒置原则，实现StreamingTTSClientInterface接口。
    
    注意：
    - ElevenLabs的REST API并非真正的流式，synthesize_stream会先获取完整音频再分块
    - 如需真正的流式，应使用ElevenLabsWebSocketClient（需要协议文档后实现）
    
    重试策略：
    - 网络错误：最多重试3次，指数退避（2^n秒）
    - 5xx错误：重试
    - 4xx错误：不重试（客户端错误）
    """
    
    # API端点
    SYNTH_PATH = "/v1/text-to-speech/{voice_id}"
    VOICES_PATH = "/v1/voices"
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.elevenlabs.io",
        timeout_seconds: float = 20.0,
        max_retries: int = 3,
        chunk_size: int = 32_000,
    ):
        """
        初始化ElevenLabs客户端
        
        Args:
            api_key: ElevenLabs API密钥
            base_url: API基础URL（可用于自托管或代理）
            timeout_seconds: 请求超时时间（秒）
            max_retries: 最大重试次数
            chunk_size: 流式分块大小（字节）
        """
        if not api_key or api_key == "change-me":
            raise ValueError("必须提供有效的ElevenLabs API密钥")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.chunk_size = chunk_size
        
        self._headers = {
            "xi-api-key": self.api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((NetworkError, httpx.RequestError)),
        reraise=True,
    )
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """
        合成完整音频（REST API）
        
        Args:
            request: TTS合成请求
            
        Returns:
            TTSResponse: 包含完整音频数据的响应
            
        Raises:
            ValidationError: 请求参数无效
            AuthenticationError: API密钥无效
            RateLimitError: 超出速率限制
            ServiceUnavailableError: ElevenLabs服务不可用
            NetworkError: 网络通信失败
        """
        # 构建请求payload
        payload = {
            "text": request.text,
            "model_id": request.model_id,
        }
        
        # 添加语音设置（过滤None值）
        if request.voice_settings:
            voice_settings = {}
            if request.voice_settings.stability is not None:
                voice_settings["stability"] = request.voice_settings.stability
            if request.voice_settings.similarity_boost is not None:
                voice_settings["similarity_boost"] = request.voice_settings.similarity_boost
            if request.voice_settings.style is not None:
                voice_settings["style"] = request.voice_settings.style
            if request.voice_settings.use_speaker_boost is not None:
                voice_settings["use_speaker_boost"] = request.voice_settings.use_speaker_boost
            
            if voice_settings:
                payload["voice_settings"] = voice_settings
        
        # 添加输出格式参数（如果API支持）
        if request.output_format != AudioFormat.MP3_44100_128:
            payload["output_format"] = request.output_format.value
        
        # 发送请求
        url = f"{self.base_url}{self.SYNTH_PATH.format(voice_id=request.voice_id)}"
        timeout = httpx.Timeout(self.timeout_seconds)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers)
                
                # 错误处理
                if response.status_code >= 400:
                    raise create_http_error(
                        status_code=response.status_code,
                        response_body=response.text,
                        provider="elevenlabs",
                    )
                
                # 成功响应
                return TTSResponse(
                    audio_data=response.content,
                    format=request.output_format,
                    metadata={
                        "provider": "elevenlabs",
                        "model_id": request.model_id,
                        "voice_id": request.voice_id,
                        "content_length": len(response.content),
                    }
                )
        
        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"ElevenLabs API请求超时（{self.timeout_seconds}秒）",
                timeout_seconds=self.timeout_seconds,
                details={"url": url},
            ) from e
        
        except httpx.ConnectError as e:
            raise NetworkError(
                f"无法连接到ElevenLabs API: {str(e)}",
                error_code="CONNECTION_FAILED",
                details={"url": url},
            ) from e
        
        except httpx.RequestError as e:
            raise NetworkError(
                f"网络请求失败: {str(e)}",
                error_code="REQUEST_FAILED",
                details={"url": url},
            ) from e
    
    async def synthesize_stream(self, request: TTSRequest):
        """
        伪流式合成（分块返回）
        
        注意：ElevenLabs的REST API不支持真正的流式，此方法会：
        1. 先调用synthesize获取完整音频
        2. 将音频按chunk_size分块yield
        
        如需真正的流式（实时生成），请使用ElevenLabsWebSocketClient。
        
        Args:
            request: TTS合成请求
            
        Yields:
            bytes: 音频数据片段
        """
        # 获取完整音频
        response = await self.synthesize(request)
        audio_data = response.audio_data
        
        # 分块yield
        for i in range(0, len(audio_data), self.chunk_size):
            chunk = audio_data[i : i + self.chunk_size]
            yield chunk
            
            # 模拟流式间隔（可选，避免过快下发）
            await asyncio.sleep(0.01)
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((NetworkError,)),
        reraise=True,
    )
    async def get_voices(self) -> List[VoiceInfo]:
        """
        获取可用语音列表
        
        Returns:
            List[VoiceInfo]: 可用的语音信息列表
            
        Raises:
            AuthenticationError: API密钥无效
            NetworkError: 网络通信失败
        """
        url = f"{self.base_url}{self.VOICES_PATH}"
        timeout = httpx.Timeout(10.0)  # 列表查询使用较短超时
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=self._headers)
                
                if response.status_code >= 400:
                    raise create_http_error(
                        status_code=response.status_code,
                        response_body=response.text,
                        provider="elevenlabs",
                    )
                
                # 解析响应
                data = response.json()
                voices = []
                
                for voice_data in data.get("voices", []):
                    voices.append(VoiceInfo(
                        voice_id=voice_data["voice_id"],
                        name=voice_data["name"],
                        accent=voice_data.get("labels", {}).get("accent"),
                        gender=voice_data.get("labels", {}).get("gender"),
                        age=voice_data.get("labels", {}).get("age"),
                        description=voice_data.get("description"),
                        preview_url=voice_data.get("preview_url"),
                        labels=voice_data.get("labels", {}),
                    ))
                
                return voices
        
        except httpx.RequestError as e:
            raise NetworkError(
                f"获取语音列表失败: {str(e)}",
                error_code="GET_VOICES_FAILED",
                details={"url": url},
            ) from e
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        通过尝试获取语音列表来验证服务可用性。
        
        Returns:
            bool: True表示服务可用，False表示不可用
        """
        try:
            await self.get_voices()
            return True
        except Exception:
            return False

