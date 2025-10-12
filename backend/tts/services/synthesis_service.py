"""
TTS合成服务

业务逻辑层，负责：
1. 封装TTS客户端调用
2. 提供统一的合成接口（整段/流式）
3. 实现缓存策略（可选）
4. 记录监控指标（可选）

遵循SOLID原则：
- 单一职责：只负责合成业务逻辑
- 依赖倒置：依赖TTSClientInterface抽象，而非具体实现
- 开闭原则：通过依赖注入支持扩展新的provider
"""
from __future__ import annotations
from typing import AsyncIterator, Optional, List
import hashlib
import time
import base64

from domain.interfaces import TTSClientInterface, StreamingTTSClientInterface
from domain.models import (
    TTSRequest,
    TTSResponse,
    VoiceInfo,
    VoiceSettings,
)
from utils.exceptions import TTSError, ValidationError


class SynthesisService:
    """
    TTS合成服务
    
    提供高层次的TTS合成能力，隔离底层客户端实现细节。
    
    特性：
    - 支持任意TTSClientInterface实现（ElevenLabs、Coqui等）
    - 可选的缓存策略（避免重复合成相同内容）
    - 监控和日志（可选）
    - 优雅降级（可选，如主provider失败时切换到备用）
    
    使用示例：
    >>> from adapters.elevenlabs_client import ElevenLabsClient
    >>> from config.settings import settings
    >>> 
    >>> # 创建客户端
    >>> client = ElevenLabsClient(api_key=settings.ELEVENLABS_API_KEY)
    >>> 
    >>> # 创建服务（依赖注入）
    >>> service = SynthesisService(tts_client=client)
    >>> 
    >>> # 合成音频
    >>> request = TTSRequest(text="Hello", voice_id="Rachel")
    >>> response = await service.synthesize_whole(request)
    """
    
    def __init__(
        self,
        tts_client: TTSClientInterface,
        enable_cache: bool = False,
        cache_ttl_seconds: int = 3600,
        chunk_size: int = 32_000,
    ):
        """
        初始化合成服务
        
        Args:
            tts_client: TTS客户端实例（依赖注入）
            enable_cache: 是否启用缓存（需要Redis支持，当前仅为内存缓存）
            cache_ttl_seconds: 缓存过期时间（秒）
            chunk_size: 流式分块大小（字节）
        """
        self.client = tts_client
        self.enable_cache = enable_cache
        self.cache_ttl_seconds = cache_ttl_seconds
        self.chunk_size = chunk_size
        
        # 简单的内存缓存（生产环境应使用Redis）
        self._cache: dict[str, tuple[TTSResponse, float]] = {}
    
    async def synthesize_whole(
        self,
        text: str,
        voice_id: str,
        model_id: str = "eleven_multilingual_v2",
        voice_settings: Optional[VoiceSettings] = None,
    ) -> TTSResponse:
        """
        合成完整音频
        
        这是高层次API，接受简单参数并返回完整音频。
        
        Args:
            text: 要合成的文本
            voice_id: 语音ID
            model_id: 模型ID
            voice_settings: 语音参数（可选）
            
        Returns:
            TTSResponse: 包含完整音频数据的响应
            
        Raises:
            ValidationError: 参数无效
            TTSError: 合成失败
        """
        # 验证输入
        if not text or not text.strip():
            raise ValidationError("文本内容不能为空")
        
        if not voice_id:
            raise ValidationError("voice_id不能为空")
        
        # 构建请求
        request = TTSRequest(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=voice_settings,
        )
        
        # 检查缓存
        if self.enable_cache:
            cache_key = self._generate_cache_key(request)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                return cached_response
        
        # 调用客户端合成
        start_time = time.time()
        response = await self.client.synthesize(request)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # 添加性能指标到metadata
        response.metadata["synthesis_time_ms"] = elapsed_ms
        response.metadata["cached"] = False
        
        # 写入缓存
        if self.enable_cache:
            self._put_to_cache(cache_key, response)
        
        return response
    
    async def synthesize_chunked(
        self,
        text: str,
        voice_id: str,
        model_id: str = "eleven_multilingual_v2",
        voice_settings: Optional[VoiceSettings] = None,
    ) -> AsyncIterator[bytes]:
        """
        流式合成音频（分块返回）
        
        适用于WebSocket场景，可以边生成边传输。
        
        注意：
        - 如果客户端实现了StreamingTTSClientInterface，会使用真正的流式
        - 否则会先合成完整音频再分块
        
        Args:
            text: 要合成的文本
            voice_id: 语音ID
            model_id: 模型ID
            voice_settings: 语音参数（可选）
            
        Yields:
            bytes: 音频数据片段
            
        Raises:
            ValidationError: 参数无效
            TTSError: 合成失败
        """
        # 验证输入
        if not text or not text.strip():
            raise ValidationError("文本内容不能为空")
        
        # 构建请求
        request = TTSRequest(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=voice_settings,
        )
        
        # 使用流式客户端（如果支持）
        if isinstance(self.client, StreamingTTSClientInterface):
            async for chunk in self.client.synthesize_stream(request):
                yield chunk
        else:
            # 降级：先合成完整音频再分块
            response = await self.client.synthesize(request)
            audio_data = response.audio_data
            
            for i in range(0, len(audio_data), self.chunk_size):
                yield audio_data[i : i + self.chunk_size]
    
    async def synthesize_chunked_base64(
        self,
        text: str,
        voice_id: Optional[str] = None,
        chunk_bytes: int = 4096,
        mime: str = "audio/mpeg",
        **voice_params
    ) -> AsyncIterator[dict]:
        """
        整段合成 -> 固定字节切片 -> 产出 base64 JSON
        最后一块加 isLast:true。**不**再 yield final_tts。
        """
        mp3 = await self.synthesize_whole(text=text, voice_id=voice_id, **voice_params)
        data = mp3.audio_data  # bytes
        total = len(data)
        seq = 1
        for i in range(0, total, chunk_bytes):
            raw = memoryview(data)[i:i+chunk_bytes]
            is_last = (i + chunk_bytes) >= total
            yield {
                "type": "tts_chunk",
                "seq": seq,
                "mime": mime,             # "audio/mpeg"
                "bytes_b64": base64.b64encode(raw).decode("ascii"),
                "size": len(raw),
                "isLast": is_last,        # <--- 关键
                "provider": "elevenlabs"  # 或根据当前实际provider填写
            }
            seq += 1

    async def get_available_voices(self) -> List[VoiceInfo]:
        """
        获取可用语音列表
        
        委托给底层客户端实现。
        
        Returns:
            List[VoiceInfo]: 可用的语音信息列表
        """
        return await self.client.get_voices()
    
    async def health_check(self) -> bool:
        """
        服务健康检查
        
        Returns:
            bool: True表示服务可用
        """
        return await self.client.health_check()
    
    # ========== 缓存相关（内部方法） ==========
    
    def _generate_cache_key(self, request: TTSRequest) -> str:
        """
        生成缓存键
        
        基于请求内容生成唯一标识，用于缓存查询。
        
        策略：
        - 包含文本、语音ID、模型ID、语音参数
        - 使用SHA256哈希（避免键过长）
        """
        # 构建缓存键内容
        key_parts = [
            request.text,
            request.voice_id,
            request.model_id,
            request.output_format.value,
        ]
        
        # 添加语音参数
        if request.voice_settings:
            vs = request.voice_settings
            key_parts.extend([
                str(vs.stability),
                str(vs.similarity_boost),
                str(vs.style),
                str(vs.use_speaker_boost),
            ])
        
        # 生成哈希
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[TTSResponse]:
        """
        从缓存读取
        
        TODO: 生产环境应使用Redis
        """
        if cache_key not in self._cache:
            return None
        
        response, cached_at = self._cache[cache_key]
        
        # 检查是否过期
        if time.time() - cached_at > self.cache_ttl_seconds:
            del self._cache[cache_key]
            return None
        
        # 标记为缓存命中
        response.metadata["cached"] = True
        return response
    
    def _put_to_cache(self, cache_key: str, response: TTSResponse):
        """
        写入缓存
        
        TODO: 生产环境应使用Redis
        """
        self._cache[cache_key] = (response, time.time())
        
        # 简单的缓存清理（防止内存泄漏）
        if len(self._cache) > 1000:
            # 清理最老的一半缓存
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1][1]  # 按缓存时间排序
            )
            for key, _ in sorted_items[:500]:
                del self._cache[key]


# ========== 工厂函数（便利方法） ==========

def create_synthesis_service(
    provider: str = "elevenlabs",
    api_key: Optional[str] = None,
    **kwargs
) -> SynthesisService:
    """
    工厂函数：根据provider创建SynthesisService
    
    这是一个便利函数，简化服务创建流程。
    
    Args:
        provider: provider名称（"elevenlabs"或"coqui"）
        api_key: API密钥（如果需要）
        **kwargs: 其他配置参数
        
    Returns:
        SynthesisService: 配置好的服务实例
        
    Raises:
        ValueError: 不支持的provider
    
    使用示例：
    >>> service = create_synthesis_service(
    >>>     provider="elevenlabs",
    >>>     api_key="your_api_key",
    >>>     enable_cache=True
    >>> )
    """
    if provider == "elevenlabs":
        from adapters.elevenlabs_client import ElevenLabsClient
        
        if not api_key:
            raise ValueError("ElevenLabs provider需要提供api_key")
        
        client = ElevenLabsClient(api_key=api_key)
        return SynthesisService(tts_client=client, **kwargs)
    
    elif provider == "coqui":
        # TODO: 实现Coqui适配器后取消注释
        # from adapters.coqui_client import CoquiClient
        # client = CoquiClient(**kwargs)
        # return SynthesisService(tts_client=client, **kwargs)
        raise NotImplementedError("Coqui provider尚未实现")
    
    else:
        raise ValueError(f"不支持的provider: {provider}")

