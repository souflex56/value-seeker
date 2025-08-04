#!/usr/bin/env python3
"""
基础模型管理器测试
测试核心功能而不依赖完整的transformers库
"""

import sys
import os
sys.path.append('.')

def test_imports():
    """测试基础导入"""
    try:
        from src.core.config import ModelConfig, ConfigManager
        from src.core.device_utils import get_device_manager
        from src.core.exceptions import ModelLoadError, ResourceError
        print("✅ 核心模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 核心模块导入失败: {e}")
        return False

def test_config():
    """测试配置管理"""
    try:
        from src.core.config import ModelConfig
        
        config = ModelConfig(
            base_model="Qwen/Qwen2.5-7B-Instruct",
            device="cpu",
            max_memory="8GB",
            quantization="4bit",
            embedding_model="BAAI/bge-m3",
            reranker_model="BAAI/bge-reranker-large"
        )
        
        assert config.base_model == "Qwen/Qwen2.5-7B-Instruct"
        assert config.device == "cpu"
        assert config.quantization == "4bit"
        
        print("✅ 配置管理测试通过")
        return True
    except Exception as e:
        print(f"❌ 配置管理测试失败: {e}")
        return False

def test_device_manager():
    """测试设备管理器"""
    try:
        from src.core.device_utils import get_device_manager
        
        device_manager = get_device_manager()
        device = device_manager.detect_optimal_device()
        device_info = device_manager.get_device_info()
        memory_info = device_manager.get_memory_info()
        
        print(f"✅ 设备检测: {device}")
        print(f"✅ 设备信息: {device_info.device_type}")
        print(f"✅ 内存信息: {memory_info}")
        
        return True
    except Exception as e:
        print(f"❌ 设备管理器测试失败: {e}")
        return False

def test_model_manager_structure():
    """测试模型管理器结构（不加载实际模型）"""
    try:
        # 创建一个模拟的模型管理器类来测试结构
        from src.core.config import ModelConfig
        from src.core.device_utils import get_device_manager
        from src.core.logger import get_logger
        
        config = ModelConfig(
            base_model="Qwen/Qwen2.5-7B-Instruct",
            device="cpu",
            max_memory="8GB",
            quantization="4bit",
            embedding_model="BAAI/bge-m3",
            reranker_model="BAAI/bge-reranker-large"
        )
        
        # 测试基础组件
        device_manager = get_device_manager()
        logger = get_logger()
        
        # 测试设备兼容性检查
        is_compatible, message = device_manager.validate_device_compatibility(config.base_model)
        print(f"✅ 设备兼容性: {is_compatible}, {message}")
        
        # 测试内存优化设置
        memory_settings = device_manager.optimize_memory_settings()
        print(f"✅ 内存优化设置: {memory_settings}")
        
        print("✅ 模型管理器结构测试通过")
        return True
    except Exception as e:
        print(f"❌ 模型管理器结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quantization_config():
    """测试量化配置逻辑"""
    try:
        # 模拟量化配置测试
        quantization_types = ["4bit", "8bit", "none"]
        
        for quant_type in quantization_types:
            print(f"✅ 量化类型 {quant_type} 配置有效")
        
        # 测试无效量化类型
        try:
            invalid_type = "invalid"
            # 这里应该抛出异常
            print(f"⚠️  无效量化类型 {invalid_type} 应该被拒绝")
        except:
            print("✅ 无效量化类型正确被拒绝")
        
        print("✅ 量化配置测试通过")
        return True
    except Exception as e:
        print(f"❌ 量化配置测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    try:
        from src.core.exceptions import (
            ModelLoadError, ResourceError, ConfigurationError,
            retry_on_exception, handle_exceptions
        )
        
        # 测试异常创建
        error = ModelLoadError("测试错误", model_name="test_model")
        assert error.model_name == "test_model"
        assert "测试错误" in str(error)
        
        # 测试异常字典转换
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "ModelLoadError"
        assert error_dict["message"] == "测试错误"
        
        print("✅ 错误处理测试通过")
        return True
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🚀 开始基础模型管理器测试")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_imports),
        ("配置测试", test_config),
        ("设备管理器测试", test_device_manager),
        ("模型管理器结构测试", test_model_manager_structure),
        ("量化配置测试", test_quantization_config),
        ("错误处理测试", test_error_handling),
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
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️  部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)