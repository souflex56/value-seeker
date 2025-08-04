#!/usr/bin/env python3
"""
模型管理器集成测试
测试模型管理器的完整功能（不实际加载大模型）
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock
sys.path.append('.')

def test_model_manager_initialization():
    """测试模型管理器初始化"""
    try:
        # 由于transformers版本兼容问题，我们使用mock来测试
        with patch('src.models.model_manager.AutoTokenizer'), \
             patch('src.models.model_manager.AutoModelForCausalLM'), \
             patch('src.models.model_manager.BitsAndBytesConfig'), \
             patch('src.models.model_manager.GenerationConfig'):
            
            from src.models.model_manager import ModelManager
            from src.core.config import ModelConfig
            
            config = ModelConfig(
                base_model="Qwen/Qwen2.5-7B-Instruct",
                device="cpu",
                max_memory="8GB",
                quantization="4bit",
                embedding_model="BAAI/bge-m3",
                reranker_model="BAAI/bge-reranker-large"
            )
            
            manager = ModelManager(config)
            
            # 测试基础属性
            assert manager.config == config
            assert not manager._is_loaded
            assert manager.tokenizer is None
            assert manager.model is None
            
            print("✅ 模型管理器初始化成功")
            return True
            
    except Exception as e:
        print(f"❌ 模型管理器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quantization_setup():
    """测试量化配置设置"""
    try:
        with patch('src.models.model_manager.BitsAndBytesConfig') as mock_config:
            from src.models.model_manager import ModelManager
            from src.core.config import ModelConfig
            
            # 测试4bit量化
            config = ModelConfig(
                base_model="Qwen/Qwen2.5-7B-Instruct",
                device="cpu",
                max_memory="8GB",
                quantization="4bit",
                embedding_model="BAAI/bge-m3",
                reranker_model="BAAI/bge-reranker-large"
            )
            
            manager = ModelManager(config)
            quant_config = manager._setup_quantization()
            
            # 验证4bit配置被调用
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs['load_in_4bit'] is True
            
            print("✅ 4bit量化配置测试通过")
            
            # 测试8bit量化
            mock_config.reset_mock()
            config.quantization = "8bit"
            manager.config = config
            
            quant_config = manager._setup_quantization()
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args[1]
            assert call_kwargs['load_in_8bit'] is True
            
            print("✅ 8bit量化配置测试通过")
            
            # 测试无量化
            config.quantization = "none"
            manager.config = config
            
            quant_config = manager._setup_quantization()
            assert quant_config is None
            
            print("✅ 无量化配置测试通过")
            
            return True
            
    except Exception as e:
        print(f"❌ 量化配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_device_compatibility():
    """测试设备兼容性检查"""
    try:
        with patch('src.models.model_manager.get_device_manager') as mock_device_manager:
            from src.models.model_manager import ModelManager
            from src.core.config import ModelConfig
            from src.core.exceptions import ConfigurationError
            
            config = ModelConfig(
                base_model="Qwen/Qwen2.5-7B-Instruct",
                device="cpu",
                max_memory="8GB",
                quantization="4bit",
                embedding_model="BAAI/bge-m3",
                reranker_model="BAAI/bge-reranker-large"
            )
            
            # 模拟设备管理器
            mock_dm = Mock()
            mock_dm.validate_device_compatibility.return_value = (True, "兼容")
            mock_device_manager.return_value = mock_dm
            
            manager = ModelManager(config)
            
            # 测试兼容性检查
            manager._validate_device_compatibility()
            mock_dm.validate_device_compatibility.assert_called_once_with(config.base_model)
            
            print("✅ 设备兼容性检查通过")
            
            # 测试不兼容情况
            mock_dm.validate_device_compatibility.return_value = (False, "不兼容")
            
            try:
                manager._validate_device_compatibility()
                assert False, "应该抛出ConfigurationError"
            except ConfigurationError as e:
                assert "设备不兼容" in str(e)
                print("✅ 设备不兼容检查通过")
            
            return True
            
    except Exception as e:
        print(f"❌ 设备兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_info_collection():
    """测试模型信息收集"""
    try:
        with patch('src.models.model_manager.get_device_manager') as mock_device_manager:
            from src.models.model_manager import ModelManager
            from src.core.config import ModelConfig
            
            config = ModelConfig(
                base_model="Qwen/Qwen2.5-7B-Instruct",
                device="cpu",
                max_memory="8GB",
                quantization="4bit",
                embedding_model="BAAI/bge-m3",
                reranker_model="BAAI/bge-reranker-large"
            )
            
            # 模拟设备管理器
            mock_dm = Mock()
            mock_dm.get_memory_info.return_value = {"total": 16.0, "available": 8.0}
            mock_device_manager.return_value = mock_dm
            
            manager = ModelManager(config)
            
            # 模拟模型和分词器
            mock_tokenizer = Mock()
            mock_tokenizer.__len__ = Mock(return_value=50000)
            manager.tokenizer = mock_tokenizer
            
            mock_model = Mock()
            mock_model.device = "cpu"
            
            # 模拟参数
            param1 = Mock()
            param1.numel.return_value = 1000
            param1.requires_grad = True
            
            param2 = Mock()
            param2.numel.return_value = 2000
            param2.requires_grad = False
            
            mock_model.parameters.return_value = [param1, param2]
            manager.model = mock_model
            
            manager._load_time = 10.5
            
            # 收集信息
            info = manager._collect_model_info()
            
            # 验证信息
            assert info["model_name"] == config.base_model
            assert info["device"] == "cpu"
            assert info["quantization"] == "4bit"
            assert info["load_time"] == 10.5
            assert info["vocab_size"] == 50000
            assert info["total_parameters"] == 3000
            assert info["trainable_parameters"] == 1000
            assert "memory_info" in info
            
            print("✅ 模型信息收集测试通过")
            return True
            
    except Exception as e:
        print(f"❌ 模型信息收集测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_optimization():
    """测试内存优化"""
    try:
        with patch('src.models.model_manager.get_device_manager') as mock_device_manager:
            from src.models.model_manager import ModelManager
            from src.core.config import ModelConfig
            
            config = ModelConfig(
                base_model="Qwen/Qwen2.5-7B-Instruct",
                device="cpu",
                max_memory="8GB",
                quantization="4bit",
                embedding_model="BAAI/bge-m3",
                reranker_model="BAAI/bge-reranker-large"
            )
            
            # 模拟设备管理器
            mock_dm = Mock()
            mock_dm.clear_cache = Mock()
            mock_dm.get_memory_info.return_value = {"total": 16.0, "free": 8.0}
            mock_device_manager.return_value = mock_dm
            
            manager = ModelManager(config)
            manager._is_loaded = True
            
            # 测试内存优化
            result = manager.optimize_memory()
            
            assert result["status"] == "optimized"
            assert "memory_info" in result
            mock_dm.clear_cache.assert_called_once()
            
            print("✅ 内存优化测试通过")
            
            # 测试未加载状态
            manager._is_loaded = False
            result = manager.optimize_memory()
            assert result["status"] == "model_not_loaded"
            
            print("✅ 未加载状态内存优化测试通过")
            return True
            
    except Exception as e:
        print(f"❌ 内存优化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_global_functions():
    """测试全局函数"""
    try:
        with patch('src.models.model_manager.ModelManager') as mock_manager_class:
            from src.models.model_manager import get_model_manager, load_qwen_model
            
            # 清理全局实例
            import src.models.model_manager
            src.models.model_manager._global_model_manager = None
            
            mock_instance = Mock()
            mock_manager_class.return_value = mock_instance
            
            # 测试get_model_manager
            manager1 = get_model_manager()
            assert manager1 == mock_instance
            
            # 第二次调用应该返回同一实例
            manager2 = get_model_manager()
            assert manager2 == mock_instance
            
            # 只应该创建一次
            mock_manager_class.assert_called_once()
            
            print("✅ get_model_manager测试通过")
            
            # 测试load_qwen_model
            mock_instance.load_base_model.return_value = ("tokenizer", "model")
            result = load_qwen_model()
            assert result == ("tokenizer", "model")
            mock_instance.load_base_model.assert_called_once()
            
            print("✅ load_qwen_model测试通过")
            return True
            
    except Exception as e:
        print(f"❌ 全局函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有集成测试"""
    print("🚀 开始模型管理器集成测试")
    print("=" * 50)
    
    tests = [
        ("模型管理器初始化", test_model_manager_initialization),
        ("量化配置设置", test_quantization_setup),
        ("设备兼容性检查", test_device_compatibility),
        ("模型信息收集", test_model_info_collection),
        ("内存优化", test_memory_optimization),
        ("全局函数", test_global_functions),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 运行 {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有集成测试通过！")
        return True
    else:
        print("⚠️  部分集成测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)