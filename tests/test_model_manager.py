"""
模型管理器测试
测试Qwen2.5-7B模型加载、量化和优化功能
"""

import pytest
import torch
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.models.model_manager import ModelManager, get_model_manager, load_qwen_model
from src.core.config import ModelConfig
from src.core.exceptions import ModelLoadError, ResourceError, ConfigurationError


class TestModelManager:
    """模型管理器测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return ModelConfig(
            base_model="Qwen/Qwen2.5-7B-Instruct",
            device="cpu",  # 使用CPU避免GPU依赖
            max_memory="8GB",
            quantization="4bit",
            embedding_model="BAAI/bge-m3",
            reranker_model="BAAI/bge-reranker-large"
        )
    
    @pytest.fixture
    def model_manager(self, mock_config):
        """创建模型管理器实例"""
        with patch('src.models.model_manager.get_device_manager') as mock_device_manager:
            mock_device_manager.return_value.detect_optimal_device.return_value = torch.device('cpu')
            mock_device_manager.return_value.optimize_memory_settings.return_value = {
                'max_memory': '8GB',
                'batch_size': 2
            }
            mock_device_manager.return_value.validate_device_compatibility.return_value = (True, "兼容")
            
            return ModelManager(mock_config)
    
    def test_init(self, mock_config):
        """测试初始化"""
        with patch('src.models.model_manager.get_device_manager'):
            manager = ModelManager(mock_config)
            
            assert manager.config == mock_config
            assert not manager._is_loaded
            assert manager.tokenizer is None
            assert manager.model is None
    
    def test_init_without_config(self):
        """测试无配置初始化"""
        with patch('src.models.model_manager.ConfigManager') as mock_config_manager:
            mock_config = Mock()
            mock_config_manager.return_value.get_model_config.return_value = mock_config
            
            with patch('src.models.model_manager.get_device_manager'):
                manager = ModelManager()
                assert manager.config == mock_config
    
    @patch('src.models.model_manager.AutoTokenizer')
    @patch('src.models.model_manager.AutoModelForCausalLM')
    def test_load_base_model_success(self, mock_model_class, mock_tokenizer_class, model_manager):
        """测试成功加载模型"""
        # 模拟分词器
        mock_tokenizer = Mock()
        mock_tokenizer.pad_token = None
        mock_tokenizer.eos_token = "<eos>"
        mock_tokenizer.pad_token_id = 0
        mock_tokenizer.eos_token_id = 1
        mock_tokenizer.__len__ = Mock(return_value=50000)
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        
        # 模拟模型
        mock_model = Mock()
        mock_model.device = torch.device('cpu')
        mock_model.parameters.return_value = [torch.randn(100), torch.randn(200)]
        mock_model_class.from_pretrained.return_value = mock_model
        
        # 执行加载
        tokenizer, model = model_manager.load_base_model()
        
        # 验证结果
        assert tokenizer == mock_tokenizer
        assert model == mock_model
        assert model_manager._is_loaded
        assert model_manager._load_time is not None
        
        # 验证分词器配置
        assert mock_tokenizer.pad_token == "<eos>"
        
        # 验证模型调用
        mock_model.eval.assert_called_once()
    
    def test_load_base_model_already_loaded(self, model_manager):
        """测试模型已加载时的行为"""
        # 设置为已加载状态
        model_manager._is_loaded = True
        model_manager.tokenizer = Mock()
        model_manager.model = Mock()
        
        tokenizer, model = model_manager.load_base_model()
        
        assert tokenizer == model_manager.tokenizer
        assert model == model_manager.model
    
    def test_validate_device_compatibility_fail(self, model_manager):
        """测试设备兼容性检查失败"""
        model_manager.device_manager.validate_device_compatibility.return_value = (
            False, "设备不兼容"
        )
        
        with pytest.raises(ConfigurationError, match="设备不兼容"):
            model_manager.load_base_model()
    
    def test_setup_quantization_4bit(self, model_manager):
        """测试4bit量化配置"""
        config = model_manager._setup_quantization()
        
        assert config is not None
        assert config.load_in_4bit is True
        assert config.bnb_4bit_compute_dtype == torch.float16
        assert config.bnb_4bit_use_double_quant is True
        assert config.bnb_4bit_quant_type == "nf4"
    
    def test_setup_quantization_8bit(self, model_manager):
        """测试8bit量化配置"""
        model_manager.config.quantization = "8bit"
        
        config = model_manager._setup_quantization()
        
        assert config is not None
        assert config.load_in_8bit is True
    
    def test_setup_quantization_none(self, model_manager):
        """测试无量化配置"""
        model_manager.config.quantization = "none"
        
        config = model_manager._setup_quantization()
        
        assert config is None
    
    def test_setup_quantization_invalid(self, model_manager):
        """测试无效量化配置"""
        model_manager.config.quantization = "invalid"
        
        with pytest.raises(ConfigurationError, match="不支持的量化类型"):
            model_manager._setup_quantization()
    
    @patch('src.models.model_manager.AutoTokenizer')
    def test_load_tokenizer_success(self, mock_tokenizer_class, model_manager):
        """测试成功加载分词器"""
        mock_tokenizer = Mock()
        mock_tokenizer.pad_token = None
        mock_tokenizer.eos_token = "<eos>"
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        
        tokenizer = model_manager._load_tokenizer()
        
        assert tokenizer == mock_tokenizer
        assert tokenizer.pad_token == "<eos>"
        
        mock_tokenizer_class.from_pretrained.assert_called_once_with(
            model_manager.config.base_model,
            trust_remote_code=True,
            padding_side="left"
        )
    
    @patch('src.models.model_manager.AutoTokenizer')
    def test_load_tokenizer_failure(self, mock_tokenizer_class, model_manager):
        """测试分词器加载失败"""
        mock_tokenizer_class.from_pretrained.side_effect = Exception("加载失败")
        
        with pytest.raises(ModelLoadError, match="加载分词器失败"):
            model_manager._load_tokenizer()
    
    @patch('src.models.model_manager.AutoModelForCausalLM')
    def test_load_model_success(self, mock_model_class, model_manager):
        """测试成功加载模型"""
        mock_model = Mock()
        mock_model.device = torch.device('cpu')
        mock_model_class.from_pretrained.return_value = mock_model
        
        device = torch.device('cpu')
        quantization_config = Mock()
        
        model = model_manager._load_model(quantization_config, device)
        
        assert model == mock_model
        mock_model.eval.assert_called_once()
        
        # 验证加载参数
        call_kwargs = mock_model_class.from_pretrained.call_args[1]
        assert call_kwargs["pretrained_model_name_or_path"] == model_manager.config.base_model
        assert call_kwargs["trust_remote_code"] is True
        assert call_kwargs["torch_dtype"] == torch.float16
        assert call_kwargs["quantization_config"] == quantization_config
    
    @patch('src.models.model_manager.AutoModelForCausalLM')
    def test_load_model_failure(self, mock_model_class, model_manager):
        """测试模型加载失败"""
        mock_model_class.from_pretrained.side_effect = Exception("加载失败")
        
        device = torch.device('cpu')
        
        with pytest.raises(ModelLoadError, match="加载模型失败"):
            model_manager._load_model(None, device)
    
    def test_setup_generation_config(self, model_manager):
        """测试生成配置设置"""
        model_manager.tokenizer = Mock()
        model_manager.tokenizer.pad_token_id = 0
        model_manager.tokenizer.eos_token_id = 1
        
        config = model_manager._setup_generation_config()
        
        assert config.max_new_tokens == 2048
        assert config.temperature == 0.7
        assert config.top_p == 0.8
        assert config.top_k == 50
        assert config.repetition_penalty == 1.05
        assert config.do_sample is True
        assert config.pad_token_id == 0
        assert config.eos_token_id == 1
    
    def test_collect_model_info(self, model_manager):
        """测试收集模型信息"""
        # 设置模拟对象
        model_manager.tokenizer = Mock()
        model_manager.tokenizer.__len__ = Mock(return_value=50000)
        
        model_manager.model = Mock()
        model_manager.model.device = torch.device('cpu')
        
        # 模拟参数
        param1 = Mock()
        param1.numel.return_value = 1000
        param1.requires_grad = True
        
        param2 = Mock()
        param2.numel.return_value = 2000
        param2.requires_grad = False
        
        model_manager.model.parameters.return_value = [param1, param2]
        
        model_manager._load_time = 10.5
        model_manager.device_manager.get_memory_info.return_value = {"total": 16.0}
        
        info = model_manager._collect_model_info()
        
        assert info["model_name"] == model_manager.config.base_model
        assert info["device"] == "cpu"
        assert info["quantization"] == "4bit"
        assert info["load_time"] == 10.5
        assert info["vocab_size"] == 50000
        assert info["total_parameters"] == 3000
        assert info["trainable_parameters"] == 1000
        assert "memory_info" in info
    
    def test_cleanup_failed_load(self, model_manager):
        """测试清理失败的加载"""
        model_manager.model = Mock()
        model_manager.tokenizer = Mock()
        model_manager._is_loaded = True
        
        model_manager._cleanup_failed_load()
        
        assert model_manager.model is None
        assert model_manager.tokenizer is None
        assert not model_manager._is_loaded
        model_manager.device_manager.clear_cache.assert_called_once()
    
    def test_generate_success(self, model_manager):
        """测试成功生成文本"""
        # 设置已加载状态
        model_manager._is_loaded = True
        
        # 模拟分词器
        mock_tokenizer = Mock()
        mock_inputs = {"input_ids": torch.tensor([[1, 2, 3]]), "attention_mask": torch.tensor([[1, 1, 1]])}
        mock_tokenizer.return_value = mock_inputs
        mock_tokenizer.decode.return_value = "生成的文本"
        model_manager.tokenizer = mock_tokenizer
        
        # 模拟模型
        mock_model = Mock()
        mock_model.device = torch.device('cpu')
        mock_outputs = torch.tensor([[1, 2, 3, 4, 5]])
        mock_model.generate.return_value = mock_outputs
        model_manager.model = mock_model
        
        # 模拟生成配置
        mock_generation_config = Mock()
        mock_generation_config.to_dict.return_value = {"max_new_tokens": 100}
        model_manager.generation_config = mock_generation_config
        
        result = model_manager.generate("测试输入", max_new_tokens=50)
        
        assert result == "生成的文本"
        mock_model.generate.assert_called_once()
    
    def test_generate_not_loaded(self, model_manager):
        """测试模型未加载时生成"""
        with pytest.raises(ModelLoadError, match="模型未加载"):
            model_manager.generate("测试输入")
    
    def test_get_model_info_loaded(self, model_manager):
        """测试获取已加载模型信息"""
        model_manager._is_loaded = True
        model_manager._model_info = {"test": "info"}
        
        info = model_manager.get_model_info()
        
        assert info["status"] == "loaded"
        assert info["test"] == "info"
    
    def test_get_model_info_not_loaded(self, model_manager):
        """测试获取未加载模型信息"""
        info = model_manager.get_model_info()
        
        assert info["status"] == "not_loaded"
    
    def test_optimize_memory_success(self, model_manager):
        """测试成功优化内存"""
        model_manager._is_loaded = True
        model_manager.device_manager.get_memory_info.return_value = {"free": 8.0}
        
        result = model_manager.optimize_memory()
        
        assert result["status"] == "optimized"
        assert "memory_info" in result
        model_manager.device_manager.clear_cache.assert_called_once()
    
    def test_optimize_memory_not_loaded(self, model_manager):
        """测试模型未加载时优化内存"""
        result = model_manager.optimize_memory()
        
        assert result["status"] == "model_not_loaded"
    
    def test_unload_model(self, model_manager):
        """测试卸载模型"""
        model_manager._is_loaded = True
        model_manager.model = Mock()
        model_manager.tokenizer = Mock()
        model_manager.generation_config = Mock()
        model_manager._load_time = 10.0
        model_manager._model_info = {"test": "info"}
        
        model_manager.unload_model()
        
        assert model_manager.model is None
        assert model_manager.tokenizer is None
        assert model_manager.generation_config is None
        assert not model_manager._is_loaded
        assert model_manager._load_time is None
        assert model_manager._model_info == {}
        model_manager.device_manager.clear_cache.assert_called_once()
    
    def test_reload_model(self, model_manager):
        """测试重新加载模型"""
        with patch.object(model_manager, 'unload_model') as mock_unload:
            with patch.object(model_manager, 'load_base_model') as mock_load:
                mock_load.return_value = ("tokenizer", "model")
                
                result = model_manager.reload_model()
                
                mock_unload.assert_called_once()
                mock_load.assert_called_once()
                assert result == ("tokenizer", "model")
    
    def test_is_loaded(self, model_manager):
        """测试检查加载状态"""
        assert not model_manager.is_loaded()
        
        model_manager._is_loaded = True
        assert model_manager.is_loaded()
    
    def test_get_device(self, model_manager):
        """测试获取设备"""
        assert model_manager.get_device() is None
        
        mock_model = Mock()
        mock_model.device = torch.device('cpu')
        model_manager.model = mock_model
        
        assert model_manager.get_device() == torch.device('cpu')


class TestGlobalFunctions:
    """测试全局函数"""
    
    def test_get_model_manager_singleton(self):
        """测试全局模型管理器单例"""
        with patch('src.models.model_manager.ModelManager') as mock_manager_class:
            mock_instance = Mock()
            mock_manager_class.return_value = mock_instance
            
            # 清理全局实例
            import src.models.model_manager
            src.models.model_manager._global_model_manager = None
            
            # 第一次调用
            manager1 = get_model_manager()
            assert manager1 == mock_instance
            
            # 第二次调用应该返回同一实例
            manager2 = get_model_manager()
            assert manager2 == mock_instance
            
            # 只应该创建一次
            mock_manager_class.assert_called_once()
    
    def test_load_qwen_model(self):
        """测试快速加载Qwen模型"""
        with patch('src.models.model_manager.get_model_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.load_base_model.return_value = ("tokenizer", "model")
            mock_get_manager.return_value = mock_manager
            
            result = load_qwen_model()
            
            assert result == ("tokenizer", "model")
            mock_manager.load_base_model.assert_called_once()


class TestRetryMechanism:
    """测试重试机制"""
    
    @pytest.fixture
    def model_manager_with_retry(self, mock_config):
        """创建带重试的模型管理器"""
        with patch('src.models.model_manager.get_device_manager') as mock_device_manager:
            mock_device_manager.return_value.detect_optimal_device.return_value = torch.device('cpu')
            mock_device_manager.return_value.optimize_memory_settings.return_value = {}
            mock_device_manager.return_value.validate_device_compatibility.return_value = (True, "兼容")
            
            return ModelManager(mock_config)
    
    @patch('src.models.model_manager.AutoTokenizer')
    @patch('src.models.model_manager.AutoModelForCausalLM')
    @patch('time.sleep')  # 避免实际等待
    def test_load_base_model_retry_success(self, mock_sleep, mock_model_class, mock_tokenizer_class, model_manager_with_retry):
        """测试重试成功"""
        # 前两次失败，第三次成功
        mock_tokenizer_class.from_pretrained.side_effect = [
            RuntimeError("第一次失败"),
            RuntimeError("第二次失败"),
            Mock()  # 第三次成功
        ]
        
        mock_model = Mock()
        mock_model.device = torch.device('cpu')
        mock_model.parameters.return_value = []
        mock_model_class.from_pretrained.return_value = mock_model
        
        # 应该成功加载
        tokenizer, model = model_manager_with_retry.load_base_model()
        
        assert tokenizer is not None
        assert model == mock_model
        
        # 验证重试了2次
        assert mock_sleep.call_count == 2
    
    @patch('src.models.model_manager.AutoTokenizer')
    @patch('time.sleep')
    def test_load_base_model_retry_exhausted(self, mock_sleep, mock_tokenizer_class, model_manager_with_retry):
        """测试重试次数用尽"""
        # 所有尝试都失败
        mock_tokenizer_class.from_pretrained.side_effect = RuntimeError("持续失败")
        
        with pytest.raises(ModelLoadError):
            model_manager_with_retry.load_base_model()
        
        # 验证重试了3次（总共4次尝试）
        assert mock_sleep.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__])