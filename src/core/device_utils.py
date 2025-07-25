"""
设备检测和配置工具
支持自动检测和配置CUDA、MPS、CPU设备
"""

import torch
import platform
import subprocess
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .logger import get_logger
from .exceptions import ResourceError

# 尝试导入psutil，如果不可用则使用替代方案
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class DeviceInfo:
    """设备信息"""
    device_type: str  # 'cuda', 'mps', 'cpu'
    device_name: str
    memory_total: Optional[float] = None  # GB
    memory_available: Optional[float] = None  # GB
    compute_capability: Optional[str] = None
    driver_version: Optional[str] = None


class DeviceManager:
    """设备管理器"""
    
    def __init__(self):
        self.logger = get_logger()
        self._device_info: Optional[DeviceInfo] = None
        self._optimal_device: Optional[torch.device] = None
    
    def detect_optimal_device(self) -> torch.device:
        """检测最优设备"""
        if self._optimal_device is not None:
            return self._optimal_device
        
        device_priority = ['cuda', 'mps', 'cpu']
        
        for device_type in device_priority:
            if self._is_device_available(device_type):
                self._optimal_device = torch.device(device_type)
                self._device_info = self._get_device_info(device_type)
                
                self.logger.info(
                    f"检测到最优设备: {device_type}",
                    {"device_info": self._device_info.__dict__}
                )
                return self._optimal_device
        
        # 默认使用CPU
        self._optimal_device = torch.device('cpu')
        self._device_info = self._get_device_info('cpu')
        
        self.logger.warning("未检测到GPU设备，使用CPU")
        return self._optimal_device
    
    def _is_device_available(self, device_type: str) -> bool:
        """检查设备是否可用"""
        try:
            if device_type == 'cuda':
                return torch.cuda.is_available()
            elif device_type == 'mps':
                return (hasattr(torch.backends, 'mps') and 
                       torch.backends.mps.is_available())
            elif device_type == 'cpu':
                return True
            return False
        except Exception as e:
            self.logger.warning(f"检查设备 {device_type} 时出错: {e}")
            return False
    
    def _get_device_info(self, device_type: str) -> DeviceInfo:
        """获取设备详细信息"""
        try:
            if device_type == 'cuda':
                return self._get_cuda_info()
            elif device_type == 'mps':
                return self._get_mps_info()
            else:
                return self._get_cpu_info()
        except Exception as e:
            self.logger.error(f"获取设备信息失败: {e}")
            return DeviceInfo(
                device_type=device_type,
                device_name="Unknown"
            )
    
    def _get_cuda_info(self) -> DeviceInfo:
        """获取CUDA设备信息"""
        if not torch.cuda.is_available():
            raise ResourceError("CUDA不可用")
        
        device_id = torch.cuda.current_device()
        device_name = torch.cuda.get_device_name(device_id)
        
        # 获取内存信息
        memory_total = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
        memory_allocated = torch.cuda.memory_allocated(device_id) / (1024**3)
        memory_available = memory_total - memory_allocated
        
        # 获取计算能力
        props = torch.cuda.get_device_properties(device_id)
        compute_capability = f"{props.major}.{props.minor}"
        
        # 获取驱动版本
        driver_version = torch.version.cuda
        
        return DeviceInfo(
            device_type='cuda',
            device_name=device_name,
            memory_total=memory_total,
            memory_available=memory_available,
            compute_capability=compute_capability,
            driver_version=driver_version
        )
    
    def _get_mps_info(self) -> DeviceInfo:
        """获取MPS设备信息"""
        if not (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()):
            raise ResourceError("MPS不可用")
        
        # 获取系统信息
        system_info = self._get_system_info()
        
        # MPS内存信息较难获取，使用系统内存作为参考
        if HAS_PSUTIL:
            memory_info = psutil.virtual_memory()
            memory_total = memory_info.total / (1024**3)
            memory_available = memory_info.available / (1024**3)
        else:
            # 使用默认值或通过其他方式获取
            memory_total = 16.0  # 默认16GB
            memory_available = 8.0  # 默认8GB可用
        
        return DeviceInfo(
            device_type='mps',
            device_name=f"Apple {system_info.get('chip', 'Silicon')}",
            memory_total=memory_total,
            memory_available=memory_available,
            compute_capability="MPS",
            driver_version=system_info.get('macos_version')
        )
    
    def _get_cpu_info(self) -> DeviceInfo:
        """获取CPU设备信息"""
        # 获取CPU信息
        cpu_info = platform.processor() or platform.machine()
        
        if HAS_PSUTIL:
            cpu_count = psutil.cpu_count(logical=False)
            # 获取内存信息
            memory_info = psutil.virtual_memory()
            memory_total = memory_info.total / (1024**3)
            memory_available = memory_info.available / (1024**3)
        else:
            # 使用默认值
            cpu_count = 4  # 默认4核
            memory_total = 8.0  # 默认8GB
            memory_available = 4.0  # 默认4GB可用
        
        device_name = f"{cpu_info} ({cpu_count} cores)"
        
        return DeviceInfo(
            device_type='cpu',
            device_name=device_name,
            memory_total=memory_total,
            memory_available=memory_available
        )
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
        
        # macOS特定信息
        if platform.system() == 'Darwin':
            try:
                # 获取macOS版本
                result = subprocess.run(['sw_vers', '-productVersion'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    info['macos_version'] = result.stdout.strip()
                
                # 获取芯片信息
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    brand = result.stdout.strip()
                    if 'Apple' in brand:
                        info['chip'] = brand.split()[1]  # 如 "M1", "M2"
                    else:
                        info['chip'] = 'Intel'
            except Exception as e:
                self.logger.debug(f"获取macOS系统信息失败: {e}")
        
        return info
    
    def get_device_info(self) -> DeviceInfo:
        """获取当前设备信息"""
        if self._device_info is None:
            self.detect_optimal_device()
        return self._device_info
    
    def get_memory_info(self) -> Dict[str, float]:
        """获取内存使用信息"""
        device_info = self.get_device_info()
        
        if device_info.device_type == 'cuda':
            return self._get_cuda_memory_info()
        else:
            return self._get_system_memory_info()
    
    def _get_cuda_memory_info(self) -> Dict[str, float]:
        """获取CUDA内存信息"""
        if not torch.cuda.is_available():
            return {}
        
        device_id = torch.cuda.current_device()
        memory_allocated = torch.cuda.memory_allocated(device_id) / (1024**3)
        memory_reserved = torch.cuda.memory_reserved(device_id) / (1024**3)
        memory_total = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
        memory_free = memory_total - memory_reserved
        
        return {
            'total': memory_total,
            'allocated': memory_allocated,
            'reserved': memory_reserved,
            'free': memory_free,
            'utilization': (memory_reserved / memory_total) * 100
        }
    
    def _get_system_memory_info(self) -> Dict[str, float]:
        """获取系统内存信息"""
        if HAS_PSUTIL:
            memory_info = psutil.virtual_memory()
            return {
                'total': memory_info.total / (1024**3),
                'available': memory_info.available / (1024**3),
                'used': memory_info.used / (1024**3),
                'utilization': memory_info.percent
            }
        else:
            # 使用默认值
            return {
                'total': 16.0,
                'available': 8.0,
                'used': 8.0,
                'utilization': 50.0
            }
    
    def optimize_memory_settings(self) -> Dict[str, Any]:
        """优化内存设置"""
        device_info = self.get_device_info()
        memory_info = self.get_memory_info()
        
        settings = {}
        
        if device_info.device_type == 'cuda':
            # CUDA内存优化
            available_memory = memory_info.get('free', 0)
            
            if available_memory > 16:  # 16GB+
                settings.update({
                    'max_memory': '12GB',
                    'batch_size': 8,
                    'gradient_accumulation_steps': 1
                })
            elif available_memory > 8:  # 8-16GB
                settings.update({
                    'max_memory': '6GB',
                    'batch_size': 4,
                    'gradient_accumulation_steps': 2
                })
            else:  # <8GB
                settings.update({
                    'max_memory': '4GB',
                    'batch_size': 2,
                    'gradient_accumulation_steps': 4
                })
        
        elif device_info.device_type == 'mps':
            # MPS内存优化
            available_memory = memory_info.get('available', 0)
            
            if available_memory > 32:  # 32GB+ (M1 Pro/Max/Ultra)
                settings.update({
                    'max_memory': '16GB',
                    'batch_size': 6,
                    'gradient_accumulation_steps': 1
                })
            elif available_memory > 16:  # 16-32GB (M1 Pro)
                settings.update({
                    'max_memory': '8GB',
                    'batch_size': 4,
                    'gradient_accumulation_steps': 2
                })
            else:  # <16GB (M1 base)
                settings.update({
                    'max_memory': '6GB',
                    'batch_size': 2,
                    'gradient_accumulation_steps': 4
                })
        
        else:  # CPU
            # CPU内存优化
            available_memory = memory_info.get('available', 0)
            
            settings.update({
                'max_memory': f"{min(available_memory * 0.7, 8):.0f}GB",
                'batch_size': 1,
                'gradient_accumulation_steps': 8
            })
        
        self.logger.info(
            f"内存优化设置: {settings}",
            {"device": device_info.device_type, "memory_info": memory_info}
        )
        
        return settings
    
    def clear_cache(self) -> None:
        """清理设备缓存"""
        device_info = self.get_device_info()
        
        if device_info.device_type == 'cuda':
            torch.cuda.empty_cache()
            self.logger.info("已清理CUDA缓存")
        elif device_info.device_type == 'mps':
            torch.mps.empty_cache()
            self.logger.info("已清理MPS缓存")
    
    def validate_device_compatibility(self, model_name: str) -> Tuple[bool, str]:
        """验证设备兼容性"""
        device_info = self.get_device_info()
        
        # 检查Qwen2.5兼容性
        if 'qwen2.5' in model_name.lower():
            if device_info.device_type == 'cuda':
                # 检查CUDA版本
                if device_info.compute_capability:
                    major, minor = map(int, device_info.compute_capability.split('.'))
                    if major < 6:  # 需要6.0+
                        return False, f"Qwen2.5需要CUDA计算能力6.0+，当前: {device_info.compute_capability}"
            
            elif device_info.device_type == 'mps':
                # MPS通常兼容
                return True, "MPS设备兼容Qwen2.5"
            
            elif device_info.device_type == 'cpu':
                return True, "CPU设备兼容Qwen2.5（性能较低）"
        
        return True, f"设备 {device_info.device_type} 兼容模型 {model_name}"


# 全局设备管理器实例
_global_device_manager: Optional[DeviceManager] = None


def get_device_manager() -> DeviceManager:
    """获取全局设备管理器实例"""
    global _global_device_manager
    
    if _global_device_manager is None:
        _global_device_manager = DeviceManager()
    
    return _global_device_manager


def detect_device() -> torch.device:
    """快速检测最优设备"""
    return get_device_manager().detect_optimal_device()


def get_device_info() -> DeviceInfo:
    """快速获取设备信息"""
    return get_device_manager().get_device_info()


def optimize_for_device() -> Dict[str, Any]:
    """快速获取设备优化设置"""
    return get_device_manager().optimize_memory_settings()