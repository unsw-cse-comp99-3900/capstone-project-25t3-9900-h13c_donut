"""
TTS客户端抽象接口

定义了TTS客户端的标准接口，遵循依赖倒置原则（DIP）。
业务层依赖这些抽象接口，而不是具体实现。

设计理念：
1. 接口隔离原则（ISP）：分离同步和流式接口
2. 开闭原则（OCP）：对扩展开放，对修改封闭
3. Liskov替换原则（LSP）：所有实现必须可互换
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
from domain.models import TTSRequest, TTSResponse, VoiceInfo


class TTSClientInterface(ABC):
    """
    TTS客户端基础接口
    
    所有TTS适配器必须实现此接口，确保可以无缝切换不同的provider。
    """
    
    @abstractmethod
    async def synthesize(self, request: TTSRequest) -> TTSResponse:
        """
        合成完整音频（非流式）
        
        Args:
            request: TTS合成请求
            
        Returns:
            TTSResponse: 包含完整音频数据的响应
            
        Raises:
            TTSError: 合成失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_voices(self) -> List[VoiceInfo]:
        """
        获取可用语音列表
        
        Returns:
            List[VoiceInfo]: 可用的语音信息列表
            
        Raises:
            TTSError: 获取失败时抛出
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: True表示服务可用，False表示不可用
        """
        pass


class StreamingTTSClientInterface(TTSClientInterface):
    """
    流式TTS客户端接口
    
    扩展了基础接口，增加流式合成能力。
    注意：不是所有provider都支持真正的流式合成（如REST API通常不支持）。
    """
    
    @abstractmethod
    async def synthesize_stream(
        self, request: TTSRequest
    ) -> AsyncIterator[bytes]:
        """
        流式合成音频
        
        实时生成音频片段，适用于WebSocket或SSE场景。
        
        Args:
            request: TTS合成请求
            
        Yields:
            bytes: 音频数据片段（可能是完整的音频帧或部分数据）
            
        Raises:
            TTSError: 合成失败时抛出
            
        注意：
        - 对于支持真正流式的provider（如ElevenLabs WebSocket），
          会实时yield生成的音频片段
        - 对于仅支持REST的provider，会先合成完整音频，再分块yield
        """
        pass


class TTSClientFactory(ABC):
    """
    TTS客户端工厂接口
    
    用于创建不同provider的TTS客户端实例。
    未来可扩展为支持配置驱动的客户端创建。
    """
    
    @staticmethod
    @abstractmethod
    def create_client(provider: str, **config) -> TTSClientInterface:
        """
        根据provider类型创建客户端
        
        Args:
            provider: provider名称（如"elevenlabs"、"coqui"）
            **config: provider特定的配置参数
            
        Returns:
            TTSClientInterface: 客户端实例
            
        Raises:
            ValueError: 不支持的provider类型
        """
        pass

