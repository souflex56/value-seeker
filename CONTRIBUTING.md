# 贡献指南

感谢你对 Value-Seeker 项目的关注！本文档将帮助你了解如何为项目做出贡献。

## 🚀 快速开始

### 1. Fork 和克隆项目

```bash
# Fork 项目到你的GitHub账户，然后克隆
git clone https://github.com/YOUR_USERNAME/value-seeker.git
cd value-seeker

# 添加上游仓库
git remote add upstream https://github.com/souflex56/value-seeker.git
```

### 2. 设置开发环境

```bash
# 创建开发环境
./setup_env.sh mps  # macOS
# 或
./setup_env.sh cuda # Linux with NVIDIA GPU

# 激活环境
conda activate value-seeker

# 验证安装
python verify_implementation.py
```

### 3. 创建功能分支

```bash
# 从main分支创建新的功能分支
git checkout -b feature/your-feature-name

# 或者修复bug
git checkout -b fix/bug-description
```

## 📝 开发流程

### 代码规范

项目使用以下工具确保代码质量：

```bash
# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/

# 运行测试
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```bash
# 功能添加
git commit -m "feat: add new data processing module"

# Bug修复
git commit -m "fix: resolve memory leak in device detection"

# 文档更新
git commit -m "docs: update installation guide"

# 测试添加
git commit -m "test: add unit tests for config manager"

# 重构
git commit -m "refactor: optimize logging performance"

# 样式修改
git commit -m "style: format code with black"
```

### 提交类型

- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_config.py -v

# 运行带覆盖率的测试
pytest tests/ --cov=src --cov-report=term-missing

# 生成HTML覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 编写测试

- 为新功能编写单元测试
- 确保测试覆盖率不低于80%
- 使用描述性的测试名称
- 遵循AAA模式（Arrange, Act, Assert）

示例：
```python
def test_config_manager_loads_default_config():
    """测试配置管理器加载默认配置"""
    # Arrange
    config_manager = ConfigManager()
    
    # Act
    model_config = config_manager.get_model_config()
    
    # Assert
    assert model_config.base_model == "Qwen/Qwen2.5-7B-Instruct"
    assert model_config.device in ["mps", "cuda", "cpu"]
```

## 📋 Pull Request 流程

### 1. 准备提交

```bash
# 确保代码符合规范
black src/ tests/
flake8 src/ tests/
mypy src/

# 运行所有测试
pytest tests/ -v

# 更新文档（如需要）
```

### 2. 推送分支

```bash
# 推送功能分支到你的fork
git push origin feature/your-feature-name
```

### 3. 创建 Pull Request

1. 在GitHub上打开你的fork
2. 点击 "Compare & pull request"
3. 填写PR模板：

```markdown
## 📝 变更描述

简要描述你的变更内容。

## 🎯 变更类型

- [ ] Bug修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 🧪 测试

- [ ] 添加了新的测试
- [ ] 所有测试通过
- [ ] 手动测试通过

## 📋 检查清单

- [ ] 代码符合项目规范
- [ ] 添加了必要的文档
- [ ] 更新了CHANGELOG（如适用）
- [ ] 测试覆盖率满足要求

## 📸 截图（如适用）

如果有UI变更，请添加截图。

## 🔗 相关Issue

Closes #issue_number
```

### 4. 代码审查

- 响应审查意见
- 根据反馈修改代码
- 保持提交历史清晰

## 🏗️ 项目架构

### 目录结构

```
src/
├── core/           # 核心模块
│   ├── config.py   # 配置管理
│   ├── logger.py   # 日志系统
│   ├── exceptions.py # 异常处理
│   └── device_utils.py # 设备检测
├── data/           # 数据处理
├── models/         # 模型管理
├── retrieval/      # 检索系统
├── rag/            # RAG核心
└── prompts/        # Prompt管理
```

### 设计原则

1. **模块化**: 每个模块职责单一
2. **可测试**: 代码易于测试
3. **可配置**: 通过配置文件控制行为
4. **错误处理**: 完善的异常处理机制
5. **日志记录**: 详细的日志记录

## 🐛 报告Bug

### Bug报告模板

```markdown
## 🐛 Bug描述

简要描述bug的现象。

## 🔄 复现步骤

1. 执行步骤1
2. 执行步骤2
3. 看到错误

## 🎯 期望行为

描述你期望的正确行为。

## 🖥️ 环境信息

- OS: [e.g. macOS 13.0]
- Python版本: [e.g. 3.11]
- 项目版本: [e.g. v1.0.0]
- 设备: [e.g. Apple M2, NVIDIA RTX 4090]

## 📋 额外信息

添加任何其他有助于解决问题的信息。
```

## 💡 功能请求

### 功能请求模板

```markdown
## 🚀 功能描述

简要描述你想要的功能。

## 🎯 问题背景

描述这个功能要解决的问题。

## 💡 解决方案

描述你期望的解决方案。

## 🔄 替代方案

描述你考虑过的其他解决方案。

## 📋 额外信息

添加任何其他相关信息。
```

## 📞 联系方式

- 项目维护者: [@souflex56](https://github.com/souflex56)
- 项目主页: https://github.com/souflex56/value-seeker
- Issues: https://github.com/souflex56/value-seeker/issues

感谢你的贡献！🎉