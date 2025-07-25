#!/bin/bash

# AI投资分析师 Value-Seeker 环境设置脚本
# 支持一键创建不同硬件配置的conda环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助信息
show_help() {
    echo "AI投资分析师 Value-Seeker 环境设置脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  mps       创建macOS MPS环境 (Apple Silicon, 默认)"
    echo "  cuda      创建CUDA GPU环境 (Linux/Windows + NVIDIA)"
    echo "  list      列出所有可用环境"
    echo "  remove    删除指定环境"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 mps      # 创建macOS MPS环境"
    echo "  $0 cuda     # 创建CUDA环境"
    echo ""
}

# 检查conda是否安装
check_conda() {
    if ! command -v conda &> /dev/null; then
        print_error "conda未找到，请先安装Anaconda或Miniconda"
        exit 1
    fi
    print_success "conda已安装"
}

# 检查Python版本要求
check_python_version() {
    print_info "检查Python版本要求..."
    
    # 检查系统Python版本
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        print_info "系统Python版本: $python_version"
        
        # 使用Python自身进行版本比较（最可靠的方法）
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            print_success "系统Python版本符合要求 ($python_version >= 3.10)"
        else
            print_warning "系统Python版本过低 ($python_version < 3.10)"
            print_info "将在conda环境中安装Python 3.10+"
        fi
    else
        print_warning "未找到python3命令"
    fi
}

# 检测硬件环境
detect_hardware() {
    print_info "检测硬件环境..."
    
    # 检测操作系统
    local os_type=$(uname -s)
    case $os_type in
        "Darwin")
            print_info "操作系统: macOS"
            # 检测Apple Silicon
            if [[ $(uname -m) == "arm64" ]]; then
                print_success "检测到Apple Silicon (ARM64)"
                print_info "推荐使用MPS加速"
            else
                print_info "检测到Intel Mac (x86_64)"
                print_warning "建议使用MPS环境，但性能可能有限"
            fi
            ;;
        "Linux")
            print_info "操作系统: Linux"
            # 检测NVIDIA GPU
            if command -v nvidia-smi &> /dev/null; then
                print_success "检测到NVIDIA GPU"
                nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1 | while read gpu_name; do
                    print_info "GPU: $gpu_name"
                done
                print_info "推荐使用CUDA环境"
            else
                print_warning "未检测到NVIDIA GPU"
                print_info "将使用CPU环境"
            fi
            ;;
        *)
            print_warning "未知操作系统: $os_type"
            ;;
    esac
}

# 创建环境
create_env() {
    local env_type=$1
    local env_file=""
    local env_name=""
    
    # 检查前置条件
    check_python_version
    detect_hardware
    
    case $env_type in
        "mps")
            env_file="environment.yml"
            env_name="value-seeker"
            print_info "创建macOS MPS环境 (Apple Silicon优化)"
            ;;
        "cuda")
            env_file="environment-cuda.yml"
            env_name="value-seeker-cuda"
            print_info "创建CUDA GPU环境 (NVIDIA GPU优化)"
            ;;
        *)
            print_error "未知的环境类型: $env_type"
            show_help
            exit 1
            ;;
    esac
    
    if [ ! -f "$env_file" ]; then
        print_error "环境文件不存在: $env_file"
        exit 1
    fi
    
    print_info "正在创建 $env_type 环境..."
    print_info "环境文件: $env_file"
    print_info "环境名称: $env_name"
    
    # 检查环境是否已存在
    if conda env list | grep -q "^$env_name "; then
        print_warning "环境 $env_name 已存在"
        read -p "是否要删除并重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "删除现有环境..."
            conda env remove -n "$env_name" -y
        else
            print_info "取消操作"
            exit 0
        fi
    fi
    
    # 创建环境
    print_info "创建conda环境..."
    conda env create -f "$env_file"
    
    # 激活环境进行验证
    print_info "激活环境进行验证..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate "$env_name"
    
    # 验证Python版本
    print_info "验证Python版本..."
    python -c "
import sys
print(f'Python版本: {sys.version}')
if sys.version_info >= (3, 10):
    print('✅ Python版本符合要求 (3.10+)')
else:
    print('❌ Python版本过低，需要3.10+')
    exit(1)
"
    
    # 验证PyTorch和设备支持
    print_info "验证PyTorch和设备支持..."
    python -c "
import torch
print(f'PyTorch版本: {torch.__version__}')

# 检查CUDA
if torch.cuda.is_available():
    print(f'✅ CUDA可用: {torch.cuda.get_device_name(0)}')
    print(f'   CUDA版本: {torch.version.cuda}')
else:
    print('ℹ️  CUDA不可用')

# 检查MPS (Apple Silicon)
if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    print('✅ MPS可用 (Apple Silicon加速)')
else:
    print('ℹ️  MPS不可用')

# 推荐设备
if torch.cuda.is_available():
    device = 'cuda'
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    device = 'mps'
else:
    device = 'cpu'

print(f'🎯 推荐设备: {device}')
"
    
    # 验证关键依赖
    print_info "验证关键依赖包..."
    python -c "
packages = [
    ('transformers', 'Transformers'),
    ('torch', 'PyTorch'),
    ('langchain', 'LangChain'),
    ('sentence_transformers', 'SentenceTransformers'),
    ('gradio', 'Gradio')
]

for module, name in packages:
    try:
        exec(f'import {module}')
        version = eval(f'{module}.__version__')
        print(f'✅ {name}: {version}')
    except ImportError:
        print(f'❌ {name}: 未安装')
    except AttributeError:
        print(f'✅ {name}: 已安装 (版本未知)')
"
    
    print_success "环境创建和验证完成!"
    
    # 显示后续步骤
    echo ""
    print_info "🎯 后续步骤:"
    echo "1. 激活环境: conda activate $env_name"
    echo "2. 测试配置: python -c \"from src.core.device_utils import detect_device; print(detect_device())\""
    echo "3. 运行测试: python -m pytest tests/ -v"
    echo "4. 启动应用: python app.py"
    echo ""
    
    if [[ "$env_type" == "mps" ]]; then
        print_info "💡 Apple Silicon用户提示:"
        echo "   - 已启用MPS加速支持"
        echo "   - 模型将自动使用最佳设备"
        echo "   - 首次运行可能需要下载模型"
    elif [[ "$env_type" == "cuda" ]]; then
        print_info "🔥 CUDA用户提示:"
        echo "   - 已启用GPU加速支持"
        echo "   - 确保NVIDIA驱动版本兼容"
        echo "   - 可使用nvidia-smi监控GPU使用"
    fi
}

# 列出环境
list_envs() {
    print_info "当前conda环境:"
    conda env list | grep value-seeker || print_warning "未找到value-seeker相关环境"
}

# 删除环境
remove_env() {
    print_info "可删除的环境:"
    conda env list | grep value-seeker || {
        print_warning "未找到value-seeker相关环境"
        exit 0
    }
    
    echo ""
    read -p "请输入要删除的环境名称: " env_name
    
    if [ -z "$env_name" ]; then
        print_error "环境名称不能为空"
        exit 1
    fi
    
    if conda env list | grep -q "^$env_name "; then
        read -p "确认删除环境 $env_name? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            conda env remove -n "$env_name" -y
            print_success "环境 $env_name 已删除"
        else
            print_info "取消删除操作"
        fi
    else
        print_error "环境 $env_name 不存在"
    fi
}

# 主逻辑
main() {
    local command=${1:-"mps"}
    
    case $command in
        "help"|"-h"|"--help")
            show_help
            ;;
        "list")
            list_envs
            ;;
        "remove")
            remove_env
            ;;
        "mps"|"cuda")
            check_conda
            create_env "$command"
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"