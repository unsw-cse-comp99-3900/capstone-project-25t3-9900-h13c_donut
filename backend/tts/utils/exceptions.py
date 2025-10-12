"""
自定义异常类

定义了TTS系统中所有可能的异常类型，遵循"异常即文档"原则。
每个异常都携带详细的上下文信息，便于调试和监控。

异常层次结构：
TTSError (基类)
├── ValidationError (验证错误)
├── NetworkError (网络错误)
│   ├── ConnectionError (连接失败)
│   ├── TimeoutError (超时)
│   └── RateLimitError (限流)
├── ProviderError (Provider错误)
│   ├── AuthenticationError (认证失败)
│   ├── QuotaExceededError (配额超限)
│   └── ServiceUnavailableError (服务不可用)
└── AudioProcessingError (音频处理错误)
"""
from __future__ import annotations
from typing import Optional, Dict, Any


class TTSError(Exception):
    """
    TTS系统基础异常类
    
    所有自定义异常的基类，携带错误码和详细信息。
    
    Attributes:
        message: 错误消息
        error_code: 错误码，便于日志分析和告警
        details: 详细的错误上下文信息
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def __str__(self) -> str:
        base = f"[{self.error_code}] {self.message}"
        if self.details:
            base += f" | 详情: {self.details}"
        return base


# ========== 验证错误 ==========

class ValidationError(TTSError):
    """
    输入验证错误
    
    当请求参数不符合要求时抛出（如文本为空、参数超出范围等）。
    """
    pass


# ========== 网络错误 ==========

class NetworkError(TTSError):
    """网络通信错误基类"""
    pass


class ConnectionError(NetworkError):
    """连接失败（如DNS解析失败、无法建立TCP连接）"""
    pass


class TimeoutError(NetworkError):
    """请求超时（连接超时或读取超时）"""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds


class RateLimitError(NetworkError):
    """
    API限流错误
    
    当请求频率超过provider限制时抛出。
    
    Attributes:
        retry_after: 建议的重试等待时间（秒）
    """
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code=error_code, details=details)
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


# ========== Provider错误 ==========

class ProviderError(TTSError):
    """TTS Provider错误基类"""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        http_status: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        if provider:
            self.details["provider"] = provider
        if http_status:
            self.details["http_status"] = http_status


class AuthenticationError(ProviderError):
    """
    认证失败
    
    API密钥无效、过期或缺失时抛出。
    """
    pass


class QuotaExceededError(ProviderError):
    """
    配额超限
    
    当账户余额不足或使用量超过套餐限制时抛出。
    """
    pass


class ServiceUnavailableError(ProviderError):
    """
    服务不可用
    
    Provider服务异常（如5xx错误、维护中等）时抛出。
    """
    pass


class VoiceNotFoundError(ProviderError):
    """
    语音不存在
    
    请求的voice_id在provider中不存在时抛出。
    """
    pass


# ========== 音频处理错误 ==========

class AudioProcessingError(TTSError):
    """
    音频处理错误
    
    音频数据损坏、格式不支持、解码失败等情况时抛出。
    """
    pass


# ========== 错误工厂函数 ==========

def create_http_error(
    status_code: int,
    response_body: str,
    provider: str = "unknown"
) -> TTSError:
    """
    根据HTTP状态码创建对应的异常
    
    这是一个工厂函数，将HTTP错误映射为语义化的异常类型。
    
    Args:
        status_code: HTTP状态码
        response_body: 响应体内容
        provider: Provider名称
        
    Returns:
        TTSError: 对应的异常实例
    """
    message = f"HTTP {status_code}: {response_body[:200]}"
    
    # 4xx 客户端错误
    if status_code == 401 or status_code == 403:
        return AuthenticationError(
            message, provider=provider, http_status=status_code
        )
    elif status_code == 404:
        return VoiceNotFoundError(
            message, provider=provider, http_status=status_code
        )
    elif status_code == 429:
        return RateLimitError(
            message,
            details={"provider": provider, "http_status": status_code}
        )
    elif 400 <= status_code < 500:
        return ValidationError(
            message, error_code=f"HTTP_{status_code}", details={"provider": provider}
        )
    
    # 5xx 服务端错误
    elif 500 <= status_code < 600:
        return ServiceUnavailableError(
            message, provider=provider, http_status=status_code
        )
    
    # 其他错误
    else:
        return ProviderError(
            message, provider=provider, http_status=status_code
        )

