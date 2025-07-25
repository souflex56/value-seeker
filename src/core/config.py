"""
配置管理系统
支持YAML配置加载和环境切换
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import torch


@dataclass
class ModelConfig:
    """模型配置"""
    base_model: str
    device: str
    max_memory: str
    quantization: str
    embedding_model: str
    reranker_model: str


@dataclass
class DataConfig:
    """数据配置"""
    reports_dir: str
    corpus_dir: str
    chunk_size: int
    chunk_overlap: int
    vector_store_path: str


@dataclass
class RetrievalConfig:
    """检索配置"""
    top_k: int
    rerank_top_k: int
    similarity_threshold: float


@dataclass
class PromptConfig:
    """Prompt配置"""
    query_rewrite_version: str
    generation_version: str
    style_version: str
    judge_version: str


@dataclass
class TrainingConfig:
    """训练配置"""
    learning_rate: float
    batch_size: int
    num_epochs: int
    warmup_steps: int
    save_steps: int


@dataclass
class SystemConfig:
    """系统配置"""
    max_concurrent_users: int
    response_timeout: int
    log_level: str
    debug_mode: bool


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            
            # 环境变量覆盖
            self._apply_env_overrides()
            
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {e}")
    
    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        env_mappings = {
            'CUDA_VISIBLE_DEVICES': ['model_config', 'device'],
            'MAX_MEMORY': ['model_config', 'max_memory'],
            'LOG_LEVEL': ['system_config', 'log_level'],
            'DEBUG_MODE': ['system_config', 'debug_mode'],
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # 设置嵌套配置值
                current = self._config
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})
                current[config_path[-1]] = env_value
    
    def get_model_config(self) -> ModelConfig:
        """获取模型配置"""
        config = self._config.get('model_config', {})
        device = config.get('device', 'auto')
        
        # 自动检测设备
        if device == 'auto':
            device = self._detect_device()
        
        return ModelConfig(
            base_model=config.get('base_model', 'Qwen/Qwen2.5-7B-Instruct'),
            device=device,
            max_memory=config.get('max_memory', '20GB'),
            quantization=config.get('quantization', '4bit'),
            embedding_model=config.get('embedding_model', 'BAAI/bge-m3'),
            reranker_model=config.get('reranker_model', 'BAAI/bge-reranker-large')
        )
    
    def _detect_device(self) -> str:
        """自动检测可用设备"""
        if torch.cuda.is_available():
            return 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'
        else:
            return 'cpu'
    
    def get_data_config(self) -> DataConfig:
        """获取数据配置"""
        config = self._config.get('data_config', {})
        return DataConfig(
            reports_dir=config.get('reports_dir', './data/reports/'),
            corpus_dir=config.get('corpus_dir', './data/dyp_corpus/'),
            chunk_size=config.get('chunk_size', 512),
            chunk_overlap=config.get('chunk_overlap', 50),
            vector_store_path=config.get('vector_store_path', './deploy/vector_store/')
        )
    
    def get_retrieval_config(self) -> RetrievalConfig:
        """获取检索配置"""
        config = self._config.get('retrieval_config', {})
        return RetrievalConfig(
            top_k=config.get('top_k', 10),
            rerank_top_k=config.get('rerank_top_k', 3),
            similarity_threshold=config.get('similarity_threshold', 0.7)
        )
    
    def get_prompt_config(self) -> PromptConfig:
        """获取Prompt配置"""
        config = self._config.get('prompt_config', {})
        return PromptConfig(
            query_rewrite_version=config.get('query_rewrite_version', 'v1'),
            generation_version=config.get('generation_version', 'v1'),
            style_version=config.get('style_version', 'v1'),
            judge_version=config.get('judge_version', 'v2')
        )
    
    def get_training_config(self) -> TrainingConfig:
        """获取训练配置"""
        config = self._config.get('training_config', {})
        return TrainingConfig(
            learning_rate=config.get('learning_rate', 2e-5),
            batch_size=config.get('batch_size', 4),
            num_epochs=config.get('num_epochs', 3),
            warmup_steps=config.get('warmup_steps', 100),
            save_steps=config.get('save_steps', 500)
        )
    
    def get_system_config(self) -> SystemConfig:
        """获取系统配置"""
        config = self._config.get('system_config', {})
        return SystemConfig(
            max_concurrent_users=config.get('max_concurrent_users', 5),
            response_timeout=config.get('response_timeout', 10),
            log_level=config.get('log_level', 'INFO'),
            debug_mode=config.get('debug_mode', False)
        )
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._load_config()
    
    def get_raw_config(self) -> Dict[str, Any]:
        """获取原始配置字典"""
        return self._config.copy() if self._config else {}