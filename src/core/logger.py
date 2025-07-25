"""
日志系统
提供结构化日志记录和性能监控
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
import json


class ValueSeekerLogger:
    """Value-Seeker专用日志器"""
    
    def __init__(self, 
                 name: str = "value_seeker",
                 log_level: str = "INFO",
                 log_dir: str = "logs",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        
        self.name = name
        self.log_level = log_level.upper()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.log_level))
        
        # 设置handlers（总是调用以确保perf_logger被初始化）
        self._setup_handlers(max_file_size, backup_count)
    
    def _setup_handlers(self, max_file_size: int, backup_count: int) -> None:
        """设置日志处理器"""
        
        # 避免重复添加handler到主logger
        if self.logger.handlers:
            # 清除现有handlers以避免重复
            self.logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器 - 一般日志
        file_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.log_level))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 错误日志处理器
        error_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}_error.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        # 性能日志处理器
        perf_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}_performance.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_formatter = logging.Formatter('%(asctime)s - %(message)s')
        perf_handler.setFormatter(perf_formatter)
        
        # 创建性能专用logger
        self.perf_logger = logging.getLogger(f"{self.name}_performance")
        self.perf_logger.setLevel(logging.INFO)
        if not self.perf_logger.handlers:  # 避免重复添加handler
            self.perf_logger.addHandler(perf_handler)
        self.perf_logger.propagate = False
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录信息日志"""
        self._log_with_context(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录警告日志"""
        self._log_with_context(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录错误日志"""
        self._log_with_context(logging.ERROR, message, extra)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录调试日志"""
        self._log_with_context(logging.DEBUG, message, extra)
    
    def _log_with_context(self, level: int, message: str, extra: Optional[Dict[str, Any]]) -> None:
        """带上下文的日志记录"""
        if extra:
            context_str = json.dumps(extra, ensure_ascii=False, separators=(',', ':'))
            full_message = f"{message} | Context: {context_str}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)
    
    def log_query(self, query: str, user_id: Optional[str] = None) -> None:
        """记录用户查询"""
        context = {
            "event_type": "user_query",
            "query_length": len(query),
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        self.info(f"用户查询: {query[:100]}...", context)
    
    def log_retrieval(self, query: str, results_count: int, processing_time: float) -> None:
        """记录检索性能"""
        context = {
            "event_type": "retrieval",
            "query": query[:50] + "..." if len(query) > 50 else query,
            "results_count": results_count,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        perf_data = {
            "type": "retrieval_performance",
            "processing_time": processing_time,
            "results_count": results_count,
            "timestamp": datetime.now().isoformat()
        }
        
        self.info(f"检索完成: {results_count}个结果, 耗时{processing_time:.2f}秒", context)
        self.perf_logger.info(json.dumps(perf_data, ensure_ascii=False))
    
    def log_generation(self, query: str, answer_length: int, processing_time: float) -> None:
        """记录生成性能"""
        context = {
            "event_type": "generation",
            "query": query[:50] + "..." if len(query) > 50 else query,
            "answer_length": answer_length,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
        perf_data = {
            "type": "generation_performance",
            "processing_time": processing_time,
            "answer_length": answer_length,
            "timestamp": datetime.now().isoformat()
        }
        
        self.info(f"生成完成: {answer_length}字符, 耗时{processing_time:.2f}秒", context)
        self.perf_logger.info(json.dumps(perf_data, ensure_ascii=False))
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """记录错误信息"""
        error_context = {
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        if context:
            error_context.update(context)
        
        self.error(f"系统错误: {error}", error_context)
    
    def log_system_startup(self, config: Dict[str, Any]) -> None:
        """记录系统启动"""
        startup_context = {
            "event_type": "system_startup",
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
        self.info("系统启动", startup_context)
    
    def log_model_loading(self, model_name: str, loading_time: float, memory_usage: Optional[float] = None) -> None:
        """记录模型加载"""
        context = {
            "event_type": "model_loading",
            "model_name": model_name,
            "loading_time": loading_time,
            "memory_usage": memory_usage,
            "timestamp": datetime.now().isoformat()
        }
        
        perf_data = {
            "type": "model_loading_performance",
            "model_name": model_name,
            "loading_time": loading_time,
            "memory_usage": memory_usage,
            "timestamp": datetime.now().isoformat()
        }
        
        self.info(f"模型加载完成: {model_name}, 耗时{loading_time:.2f}秒", context)
        self.perf_logger.info(json.dumps(perf_data, ensure_ascii=False))


# 全局日志器实例
_global_logger: Optional[ValueSeekerLogger] = None


def get_logger(name: str = "value_seeker", 
               log_level: str = "INFO",
               log_dir: str = "logs") -> ValueSeekerLogger:
    """获取全局日志器实例"""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = ValueSeekerLogger(name, log_level, log_dir)
    
    return _global_logger


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> ValueSeekerLogger:
    """设置全局日志系统"""
    global _global_logger
    _global_logger = ValueSeekerLogger("value_seeker", log_level, log_dir)
    return _global_logger