# AI投资分析师 Value-Seeker

基于大语言模型的智能投资分析系统，专注于价值投资策略分析和投资建议生成。

## 🎯 项目概述

Value-Seeker是一个集成了检索增强生成(RAG)技术的AI投资分析师，能够：

- 📊 分析上市公司财务报告和研究报告
- 💡 提供基于价值投资理念的投资建议
- 💬 支持多轮对话式投资咨询
- 📈 集成实时市场数据分析

## 🏗️ 技术架构

- **核心模型**: Qwen2.5-7B-Instruct
- **检索系统**: BGE-M3 + BGE-Reranker-Large
- **向量数据库**: FAISS
- **Web界面**: Gradio
- **部署方式**: Docker + GPU加速

## 🚀 快速开始

### 环境要求

- Python 3.10+
- CUDA 11.8+ (GPU版本) 或 Apple Silicon (MPS版本)
- 16GB+ RAM
- 50GB+ 存储空间

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd value-seeker
```

2. **创建环境**
```bash
# macOS (Apple Silicon)
./setup_env.sh mps

# Linux (NVIDIA GPU)
./setup_env.sh cuda
```

3. **激活环境**
```bash
conda activate value-seeker
```

4. **验证安装**
```bash
python verify_implementation.py
```

5. **启动应用**
```bash
python app.py
```

## 📁 项目结构

```
value-seeker/
├── .kiro/                 # Kiro IDE配置
│   └── specs/             # 功能规格文档
├── src/                   # 源代码
│   ├── core/              # 核心模块
│   │   ├── config.py      # 配置管理
│   │   ├── logger.py      # 日志系统
│   │   ├── exceptions.py  # 异常处理
│   │   └── device_utils.py # 设备检测
│   ├── models/            # 模型相关
│   ├── data/              # 数据处理
│   ├── retrieval/         # 检索系统
│   └── rag/               # RAG实现
├── config/                # 配置文件
│   └── config.yaml        # 主配置文件
├── tests/                 # 测试代码
├── environment.yml        # Conda环境(macOS MPS)
├── environment-cuda.yml   # Conda环境(CUDA)
├── setup_env.sh          # 环境设置脚本
├── verify_implementation.py # 验证脚本
└── pyproject.toml        # 项目配置
```

## ✨ 功能特性

### 已完成 ✅
- **项目基础架构**: 配置管理、日志系统、异常处理
- **设备检测**: 自动检测CUDA/MPS/CPU并优化配置
- **环境管理**: 支持Apple Silicon MPS和NVIDIA CUDA
- **测试框架**: 完整的单元测试和集成测试

### 开发中 🚧
- 智能文档解析和向量化
- 高效的语义检索系统
- 多轮对话式交互
- 实时投资建议生成
- 可视化分析报告
- 模型微调和优化

## 🛠️ 开发指南

### 代码规范

项目使用以下工具确保代码质量：

- **格式化**: Black
- **代码检查**: Flake8
- **类型检查**: MyPy
- **测试**: Pytest

运行代码检查：
```bash
black src/ tests/
flake8 src/ tests/
mypy src/
pytest tests/ -v
```

### 配置管理

配置文件位于 `config/config.yaml`，支持：

- 模型参数配置 (自动设备检测)
- 数据处理配置
- 检索系统配置
- Web界面配置
- 训练参数配置

### 设备支持

- **Apple Silicon**: 自动启用MPS加速
- **NVIDIA GPU**: 自动启用CUDA加速
- **CPU**: 自动优化CPU性能

### 测试

运行测试套件：
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_config.py -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

## 📊 项目状态

### 任务进度

- [x] **任务1**: 项目基础架构搭建 (100%)
  - [x] 配置管理系统
  - [x] 日志系统
  - [x] 异常处理框架
  - [x] 设备检测工具
- [ ] **任务2**: 数据处理模块实现 (0%)
- [ ] **任务3**: 检索系统实现 (0%)
- [ ] **任务4**: RAG系统集成 (0%)
- [ ] **任务5**: Web界面开发 (0%)

### 测试覆盖率

- **总体覆盖率**: 53%
- **核心模块**: 90%+
- **测试通过率**: 100% (14/14)

## 🐳 部署

### Docker部署

```bash
# 构建镜像
docker build -t value-seeker .

# 运行容器
docker run -p 7860:7860 --gpus all value-seeker
```

### 生产部署

详见 `deploy/` 目录下的部署文档。

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📞 联系方式

- 项目维护者: Value-Seeker Team
- 项目主页: [GitHub Repository URL]
- 文档: [Documentation URL]

---

**注意**: 本项目正在积极开发中，功能和API可能会发生变化。