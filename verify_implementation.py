#!/usr/bin/env python3
"""
验证任务1实现的脚本
测试项目基础架构搭建的各个组件
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, 'src')

def test_config_system():
    """测试配置管理系统"""
    print("🔧 测试配置管理系统...")
    
    try:
        from core.config import ConfigManager
        
        # 测试配置加载
        config_manager = ConfigManager()
        
        # 测试各种配置获取
        model_config = config_manager.get_model_config()
        print(f"  ✅ 模型配置: {model_config.base_model}")
        print(f"  ✅ 设备配置: {model_config.device}")
        
        data_config = config_manager.get_data_config()
        print(f"  ✅ 数据配置: chunk_size={data_config.chunk_size}")
        
        system_config = config_manager.get_system_config()
        print(f"  ✅ 系统配置: log_level={system_config.log_level}")
        
        print("  ✅ 配置管理系统测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 配置管理系统测试失败: {e}")
        return False

def test_logging_system():
    """测试日志系统"""
    print("📝 测试日志系统...")
    
    try:
        from core.logger import ValueSeekerLogger, get_logger
        
        # 创建临时目录用于测试
        with tempfile.TemporaryDirectory() as temp_dir:
            # 测试日志器创建
            logger = ValueSeekerLogger("test_logger", "INFO", temp_dir)
            
            # 测试基础日志记录
            logger.info("测试信息日志")
            logger.warning("测试警告日志")
            logger.error("测试错误日志")
            
            # 测试带上下文的日志
            logger.info("测试上下文日志", {"user_id": "test", "action": "verify"})
            
            # 测试性能日志
            logger.log_retrieval("测试查询", 5, 1.23)
            logger.log_generation("测试查询", 100, 2.45)
            
            # 检查日志文件是否创建
            log_files = list(Path(temp_dir).glob("*.log"))
            if len(log_files) >= 2:  # 至少有主日志和性能日志
                print(f"  ✅ 日志文件创建成功: {len(log_files)}个文件")
            else:
                print(f"  ⚠️  日志文件数量不足: {len(log_files)}个文件")
            
            # 测试全局日志器
            global_logger = get_logger()
            global_logger.info("全局日志器测试")
            
        print("  ✅ 日志系统测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 日志系统测试失败: {e}")
        return False

def test_exception_handling():
    """测试异常处理框架"""
    print("⚠️  测试异常处理框架...")
    
    try:
        from core.exceptions import (
            ValueSeekerException, ConfigurationError, 
            handle_exceptions, retry_on_exception
        )
        
        # 测试基础异常
        exc = ValueSeekerException("测试异常", "TEST_ERROR", {"key": "value"})
        assert str(exc) == "[TEST_ERROR] 测试异常"
        assert exc.error_code == "TEST_ERROR"
        print("  ✅ 基础异常类测试通过")
        
        # 测试特定异常
        config_exc = ConfigurationError("配置错误", config_key="test_key")
        assert config_exc.error_code == "CONFIG_ERROR"
        print("  ✅ 特定异常类测试通过")
        
        # 测试异常处理装饰器
        @handle_exceptions(ValueError, default_return="error", log_error=False, reraise=False)
        def test_function(should_raise=False):
            if should_raise:
                raise ValueError("测试错误")
            return "success"
        
        assert test_function(False) == "success"
        assert test_function(True) == "error"
        print("  ✅ 异常处理装饰器测试通过")
        
        print("  ✅ 异常处理框架测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 异常处理框架测试失败: {e}")
        return False

def test_device_utils():
    """测试设备检测工具"""
    print("🖥️  测试设备检测工具...")
    
    try:
        from core.device_utils import DeviceManager, detect_device, get_device_info
        
        # 测试设备管理器
        device_manager = DeviceManager()
        
        # 测试设备检测
        device = device_manager.detect_optimal_device()
        print(f"  ✅ 检测到设备: {device}")
        
        # 测试设备信息获取
        device_info = device_manager.get_device_info()
        print(f"  ✅ 设备信息: {device_info.device_type} - {device_info.device_name}")
        
        # 测试内存信息
        memory_info = device_manager.get_memory_info()
        if memory_info:
            print(f"  ✅ 内存信息: {memory_info.get('total', 'N/A'):.1f}GB 总计")
        
        # 测试优化设置
        optimization = device_manager.optimize_memory_settings()
        print(f"  ✅ 优化设置: batch_size={optimization.get('batch_size', 'N/A')}")
        
        # 测试快速接口
        quick_device = detect_device()
        quick_info = get_device_info()
        print(f"  ✅ 快速接口: {quick_device} - {quick_info.device_type}")
        
        print("  ✅ 设备检测工具测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 设备检测工具测试失败: {e}")
        return False

def test_directory_structure():
    """测试项目目录结构"""
    print("📁 测试项目目录结构...")
    
    required_dirs = [
        "src/core",
        "src/rag", 
        "config",
        "tests",
        "logs"
    ]
    
    required_files = [
        "config/config.yaml",
        "src/core/__init__.py",
        "src/core/config.py",
        "src/core/logger.py",
        "src/core/exceptions.py",
        "src/core/device_utils.py",
        "environment.yml",
        "environment-cuda.yml",
        "setup_env.sh"
    ]
    
    missing_dirs = []
    missing_files = []
    
    # 检查目录
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    # 检查文件
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"  ❌ 缺少目录: {missing_dirs}")
        return False
    
    if missing_files:
        print(f"  ❌ 缺少文件: {missing_files}")
        return False
    
    print("  ✅ 项目目录结构完整")
    return True

def main():
    """主测试函数"""
    print("🚀 开始验证任务1：项目基础架构搭建")
    print("=" * 50)
    
    tests = [
        ("目录结构", test_directory_structure),
        ("配置管理系统", test_config_system),
        ("日志系统", test_logging_system),
        ("异常处理框架", test_exception_handling),
        ("设备检测工具", test_device_utils),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 任务1：项目基础架构搭建 - 全部测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)