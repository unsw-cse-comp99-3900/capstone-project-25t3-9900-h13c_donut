"""
异常类单元测试

测试内容：
1. 异常创建和属性
2. 异常继承关系
3. 错误工厂函数
"""
import pytest

from utils.exceptions import (
    TTSError,
    ValidationError,
    NetworkError,
    TimeoutError,
    RateLimitError,
    AuthenticationError,
    QuotaExceededError,
    ServiceUnavailableError,
    create_http_error,
)


class TestBaseException:
    """基础异常测试"""
    
    def test_create_basic(self):
        """测试：创建基础异常"""
        error = TTSError("Something went wrong")
        assert str(error) == "[TTSError] Something went wrong"
        assert error.error_code == "TTSError"
        assert error.details == {}
    
    def test_create_with_details(self):
        """测试：带详细信息创建"""
        error = TTSError(
            "Error occurred",
            error_code="CUSTOM_ERROR",
            details={"key": "value"},
        )
        assert error.error_code == "CUSTOM_ERROR"
        assert error.details["key"] == "value"


class TestSpecificExceptions:
    """具体异常测试"""
    
    def test_validation_error(self):
        """测试：验证错误"""
        error = ValidationError("Invalid input")
        assert isinstance(error, TTSError)
        assert "ValidationError" in str(error)
    
    def test_timeout_error(self):
        """测试：超时错误"""
        error = TimeoutError("Request timed out", timeout_seconds=10.0)
        assert error.details["timeout_seconds"] == 10.0
    
    def test_rate_limit_error(self):
        """测试：限流错误"""
        error = RateLimitError("Rate limited", retry_after=60)
        assert error.retry_after == 60
        assert error.details["retry_after"] == 60


class TestHttpErrorFactory:
    """HTTP错误工厂函数测试"""
    
    def test_401_authentication_error(self):
        """测试：401 -> AuthenticationError"""
        error = create_http_error(401, "Unauthorized", "elevenlabs")
        assert isinstance(error, AuthenticationError)
        assert error.details["http_status"] == 401
    
    def test_404_voice_not_found(self):
        """测试：404 -> VoiceNotFoundError"""
        error = create_http_error(404, "Voice not found", "elevenlabs")
        assert "VoiceNotFoundError" in error.__class__.__name__
    
    def test_429_rate_limit(self):
        """测试：429 -> RateLimitError"""
        error = create_http_error(429, "Too many requests", "elevenlabs")
        assert isinstance(error, RateLimitError)
    
    def test_500_service_unavailable(self):
        """测试：500 -> ServiceUnavailableError"""
        error = create_http_error(500, "Internal server error", "elevenlabs")
        assert isinstance(error, ServiceUnavailableError)
    
    def test_400_validation_error(self):
        """测试：400 -> ValidationError"""
        error = create_http_error(400, "Bad request", "elevenlabs")
        assert isinstance(error, ValidationError)

