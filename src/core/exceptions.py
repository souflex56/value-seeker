"""
异常处理基础框架
定义系统中使用的所有自定义异常类
"""

from typing import Optional, Dict, Any


class ValueSeekerException(Exception):
    """Value-Seeker基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context
        }


class ConfigurationError(ValueSeekerException):
    """配置相关异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_key = config_key


class DocumentProcessingError(ValueSeekerException):
    """文档处理异常"""
    
    def __init__(self, message: str, document_path: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="DOC_PROCESSING_ERROR", **kwargs)
        self.document_path = document_path


class RetrievalError(ValueSeekerException):
    """检索异常"""
    
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="RETRIEVAL_ERROR", **kwargs)
        self.query = query


class GenerationError(ValueSeekerException):
    """生成异常"""
    
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="GENERATION_ERROR", **kwargs)
        self.query = query


class ModelLoadError(ValueSeekerException):
    """模型加载异常"""
    
    def __init__(self, message: str, model_name: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="MODEL_LOAD_ERROR", **kwargs)
        self.model_name = model_name


class VectorStoreError(ValueSeekerException):
    """向量存储异常"""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="VECTOR_STORE_ERROR", **kwargs)
        self.operation = operation


class PromptError(ValueSeekerException):
    """Prompt相关异常"""
    
    def __init__(self, message: str, prompt_type: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="PROMPT_ERROR", **kwargs)
        self.prompt_type = prompt_type


class ValidationError(ValueSeekerException):
    """数据验证异常"""
    
    def __init__(self, message: str, field_name: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field_name = field_name


class ResourceError(ValueSeekerException):
    """资源相关异常（内存、GPU等）"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="RESOURCE_ERROR", **kwargs)
        self.resource_type = resource_type


class TimeoutError(ValueSeekerException):
    """超时异常"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, **kwargs):
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)
        self.timeout_seconds = timeout_seconds


class NetworkError(ValueSeekerException):
    """网络相关异常"""
    
    def __init__(self, message: str, url: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)
        self.url = url


# 异常处理装饰器
from functools import wraps
from typing import Callable, Type, Union, List
import traceback


def handle_exceptions(
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    default_return=None,
    log_error: bool = True,
    reraise: bool = False
):
    """
    异常处理装饰器
    
    Args:
        exceptions: 要捕获的异常类型
        default_return: 异常时的默认返回值
        log_error: 是否记录错误日志
        reraise: 是否重新抛出异常
    """
    
    if not isinstance(exceptions, (list, tuple)):
        exceptions = [exceptions]
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(exceptions) as e:
                if log_error:
                    from .logger import get_logger
                    logger = get_logger()
                    logger.log_error(e, {
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200],
                        "traceback": traceback.format_exc()
                    })
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def retry_on_exception(
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """
    异常重试装饰器
    
    Args:
        exceptions: 要重试的异常类型
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟时间递增因子
    """
    
    if not isinstance(exceptions, (list, tuple)):
        exceptions = [exceptions]
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # 最后一次尝试失败，抛出异常
                        break
                    
                    # 记录重试日志
                    from .logger import get_logger
                    logger = get_logger()
                    logger.warning(
                        f"函数 {func.__name__} 第{attempt + 1}次尝试失败，{current_delay}秒后重试",
                        {"exception": str(e), "attempt": attempt + 1}
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # 所有重试都失败，抛出最后一个异常
            raise last_exception
        
        return wrapper
    return decorator