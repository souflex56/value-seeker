#!/usr/bin/env python3
"""
AI投资分析师 Value-Seeker 主程序入口
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import ConfigManager
from src.core.logger import setup_logging
from src.core.exceptions import ValueSeekerException, handle_exceptions


@handle_exceptions(Exception, log_error=True, reraise=True)
def initialize_system():
    """初始化系统"""
    print("🚀 正在启动 AI投资分析师 Value-Seeker...")
    
    # 加载配置
    try:
        config_manager = ConfigManager("config/config.yaml")
        print("✅ 配置文件加载成功")
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        raise
    
    # 设置日志系统
    try:
        system_config = config_manager.get_system_config()
        logger = setup_logging(
            log_level=system_config.log_level,
            log_dir="logs"
        )
        print(f"✅ 日志系统初始化成功 (级别: {system_config.log_level})")
        
        # 记录系统启动
        logger.log_system_startup(config_manager.get_raw_config())
        
    except Exception as e:
        print(f"❌ 日志系统初始化失败: {e}")
        raise
    
    # 显示配置信息
    print("\n📋 系统配置信息:")
    model_config = config_manager.get_model_config()
    data_config = config_manager.get_data_config()
    
    print(f"  • 基础模型: {model_config.base_model}")
    print(f"  • 设备: {model_config.device}")
    print(f"  • 最大内存: {model_config.max_memory}")
    print(f"  • 量化: {model_config.quantization}")
    print(f"  • 文档目录: {data_config.reports_dir}")
    print(f"  • 向量存储: {data_config.vector_store_path}")
    print(f"  • 分块大小: {data_config.chunk_size}")
    
    return config_manager, logger


def main():
    """主函数"""
    try:
        config_manager, logger = initialize_system()
        
        print("\n🎉 系统初始化完成!")
        print("📝 日志文件位置: ./logs/")
        print("⚙️  配置文件位置: ./config/config.yaml")
        print("\n💡 提示: 这是基础架构搭建阶段，后续功能模块将逐步实现")
        
        # 测试日志功能
        logger.info("系统启动测试", {"component": "main", "status": "success"})
        logger.log_query("这是一个测试查询", "test_user")
        
        print("\n✨ 基础架构搭建完成，系统已就绪!")
        
    except ValueSeekerException as e:
        print(f"\n❌ 系统错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()