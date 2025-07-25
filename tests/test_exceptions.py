"""
异常处理测试
"""

import pytest
import time

from src.core.exceptions import (
    ValueSeekerException, ConfigurationError, DocumentProcessingError,
    RetrievalError, GenerationError, ModelLoadError,
    handle_exceptions, retry_on_exception
)


class TestValueSeekerExceptions:
    """异常类测试"""
    
    def test_base_exception(self):
        """测试基础异常类"""
        exc = ValueSeekerException("Test message", "TEST_ERROR", {"key": "value"})
        
        assert str(exc) == "[TEST_ERROR] Test message"
        assert exc.message == "Test message"
        assert exc.error_code == "TEST_ERROR"
        assert exc.context == {"key": "value"}
        
        # 测试转换为字典
        exc_dict = exc.to_dict()
        assert exc_dict["error_type"] == "ValueSeekerException"
        assert exc_dict["message"] == "Test message"
    
    def test_specific_exceptions(self):
        """测试特定异常类"""
        # 配置异常
        config_exc = ConfigurationError("Config error", config_key="test_key")
        assert config_exc.error_code == "CONFIG_ERROR"
        assert config_exc.config_key == "test_key"
        
        # 文档处理异常
        doc_exc = DocumentProcessingError("Doc error", document_path="/test/path")
        assert doc_exc.error_code == "DOC_PROCESSING_ERROR"
        assert doc_exc.document_path == "/test/path"
        
        # 检索异常
        retrieval_exc = RetrievalError("Retrieval error", query="test query")
        assert retrieval_exc.error_code == "RETRIEVAL_ERROR"
        assert retrieval_exc.query == "test query"


class TestExceptionDecorators:
    """异常装饰器测试"""
    
    def test_handle_exceptions_decorator(self):
        """测试异常处理装饰器"""
        
        @handle_exceptions(ValueError, default_return="error", log_error=False, reraise=False)
        def test_function(should_raise=False):
            if should_raise:
                raise ValueError("Test error")
            return "success"
        
        # 正常情况
        result = test_function(False)
        assert result == "success"
        
        # 异常情况
        result = test_function(True)
        assert result == "error"
    
    def test_retry_decorator(self):
        """测试重试装饰器"""
        call_count = 0
        
        @retry_on_exception(ValueError, max_retries=2, delay=0.1, backoff_factor=1.0)
        def test_function(fail_times=0):
            nonlocal call_count
            call_count += 1
            
            if call_count <= fail_times:
                raise ValueError(f"Attempt {call_count} failed")
            
            return f"Success on attempt {call_count}"
        
        # 重置计数器
        call_count = 0
        
        # 第一次就成功
        result = test_function(0)
        assert result == "Success on attempt 1"
        assert call_count == 1
        
        # 重置计数器
        call_count = 0
        
        # 第二次成功
        result = test_function(1)
        assert result == "Success on attempt 2"
        assert call_count == 2
        
        # 重置计数器
        call_count = 0
        
        # 超过最大重试次数
        with pytest.raises(ValueError):
            test_function(5)