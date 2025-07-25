"""
日志系统测试
"""

import pytest
import tempfile
import os
from pathlib import Path
import json

from src.core.logger import ValueSeekerLogger, get_logger, setup_logging
from src.core.exceptions import ValueSeekerException


class TestValueSeekerLogger:
    """日志系统测试"""
    
    def test_logger_creation(self):
        """测试日志器创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ValueSeekerLogger("test_logger", "INFO", temp_dir)
            
            assert logger.name == "test_logger"
            assert logger.log_level == "INFO"
            assert logger.log_dir == Path(temp_dir)
    
    def test_basic_logging(self):
        """测试基础日志记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ValueSeekerLogger("test_logger", "DEBUG", temp_dir)
            
            # 测试不同级别的日志
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # 强制刷新日志缓冲区
            for handler in logger.logger.handlers:
                handler.flush()
            
            # 检查日志文件是否创建
            log_file = Path(temp_dir) / "test_logger.log"
            assert log_file.exists()
    
    def test_context_logging(self):
        """测试带上下文的日志记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ValueSeekerLogger("test_logger", "INFO", temp_dir)
            
            context = {"user_id": "test_user", "query_id": "123"}
            logger.info("Test message with context", context)
            
            # 强制刷新日志缓冲区
            for handler in logger.logger.handlers:
                handler.flush()
            
            # 检查日志内容
            log_file = Path(temp_dir) / "test_logger.log"
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Test message with context" in content
                assert "user_id" in content
    
    def test_performance_logging(self):
        """测试性能日志记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ValueSeekerLogger("test_logger", "INFO", temp_dir)
            
            # 测试检索性能日志
            logger.log_retrieval("test query", 5, 1.23)
            
            # 测试生成性能日志
            logger.log_generation("test query", 100, 2.45)
            
            # 检查性能日志文件
            perf_log_file = Path(temp_dir) / "test_logger_performance.log"
            assert perf_log_file.exists()
    
    def test_error_logging(self):
        """测试错误日志记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ValueSeekerLogger("test_logger", "INFO", temp_dir)
            
            try:
                raise ValueError("Test error")
            except Exception as e:
                logger.log_error(e, {"context": "test"})
            
            # 强制刷新日志缓冲区
            for handler in logger.logger.handlers:
                handler.flush()
            
            # 检查错误日志文件
            error_log_file = Path(temp_dir) / "test_logger_error.log"
            assert error_log_file.exists()
    
    def test_global_logger(self):
        """测试全局日志器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger1 = get_logger("global_test", "INFO", temp_dir)
            logger2 = get_logger("global_test", "INFO", temp_dir)
            
            # 应该返回同一个实例
            assert logger1 is logger2