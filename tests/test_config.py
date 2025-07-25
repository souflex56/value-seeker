"""
配置管理系统测试
"""

import pytest
import tempfile
import os
from pathlib import Path
import yaml

from src.core.config import ConfigManager, ModelConfig, DataConfig
from src.core.exceptions import ConfigurationError


class TestConfigManager:
    """配置管理器测试"""
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        config_manager = ConfigManager("config/config.yaml")
        
        # 测试模型配置
        model_config = config_manager.get_model_config()
        assert isinstance(model_config, ModelConfig)
        assert model_config.base_model == "Qwen/Qwen2.5-7B-Instruct"
        # 设备应该是自动检测的结果（mps, cuda, 或 cpu）
        assert model_config.device in ["mps", "cuda", "cpu"]
        
        # 测试数据配置
        data_config = config_manager.get_data_config()
        assert isinstance(data_config, DataConfig)
        assert data_config.chunk_size == 512
        assert data_config.chunk_overlap == 50
    
    def test_env_override(self):
        """测试环境变量覆盖"""
        # 设置环境变量
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["MAX_MEMORY"] = "16GB"
        
        try:
            config_manager = ConfigManager("config/config.yaml")
            system_config = config_manager.get_system_config()
            model_config = config_manager.get_model_config()
            
            assert system_config.log_level == "DEBUG"
            assert model_config.max_memory == "16GB"
        finally:
            # 清理环境变量
            os.environ.pop("LOG_LEVEL", None)
            os.environ.pop("MAX_MEMORY", None)
    
    def test_missing_config_file(self):
        """测试配置文件不存在的情况"""
        with pytest.raises(RuntimeError):
            ConfigManager("nonexistent_config.yaml")
    
    def test_config_reload(self):
        """测试配置重新加载"""
        config_manager = ConfigManager("config/config.yaml")
        
        # 第一次加载
        original_config = config_manager.get_raw_config()
        
        # 重新加载
        config_manager.reload_config()
        reloaded_config = config_manager.get_raw_config()
        
        assert original_config == reloaded_config