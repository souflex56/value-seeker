# 文档分块架构说明

## 🎯 当前推荐方案：父子分块RAG处理器

**文件位置：** `parent_child_rag_processor.py`

### 📋 方案概述

这是一个专门为RAG系统设计的完整父子分块处理方案，实现了你要求的完整流程：

1. **高保真表格提取** - 使用pdfplumber提取表格，转为Markdown子分块
2. **高保真文本提取** - 使用unstructured跳过表格区域，提取文本元素  
3. **文本二次分块** - 递归分块生成细粒度子分块
4. **构建父子关系** - 按页面分组创建父分块，关联所有子分块
5. **RAG存储准备** - 生成向量数据库和文档存储格式

### 🚀 使用方式

```python
from parent_child_rag_processor import ParentChildRAGProcessor

# 创建处理器
processor = ParentChildRAGProcessor({
    'child_chunk_size': 800,
    'child_chunk_overlap': 100,
    'parent_strategy': 'page_group',
    'pages_per_parent': 3
})

# 处理PDF
result = processor.process_pdf('your_report.pdf')

# 获取RAG存储格式
child_chunks = result['child_chunks']  # 用于向量数据库
parent_chunks = result['parent_chunks']  # 用于文档存储

# 保存结果
files = processor.save_results(result)
```

### 📊 输出格式

**子分块（向量数据库）：**
```json
{
  "chunk_id": "table_9_0_20102f6f",
  "content": "| 营业收入 | 16,247,040,360.90 | ...",
  "chunk_type": "table",
  "parent_id": "parent_pages_9_11_xxx",
  "metadata": {
    "page_number": 9,
    "table_type": "financial",
    "row_count": 7,
    "col_count": 5,
    "bbox": {...}
  }
}
```

**父分块（文档存储）：**
```json
{
  "parent_id": "parent_pages_9_11_xxx",
  "title": "页面 9-11",
  "content": "[表格 - 页面9]\n营业收入数据...\n[表格 - 页面10]\n季度数据...",
  "page_range": [9, 11],
  "child_ids": ["table_9_0_...", "table_10_0_..."],
  "chunk_type": "page_group"
}
```

### 🔍 RAG检索流程

```python
def query_rag(question):
    # 1. 检索相关子分块
    child_chunks = vector_db.search(question, top_k=5)
    
    # 2. 获取父分块ID
    parent_ids = [chunk['metadata']['parent_id'] for chunk in child_chunks]
    
    # 3. 获取父分块完整内容
    parent_contents = [doc_store[pid] for pid in set(parent_ids)]
    
    # 4. 生成答案
    return llm.generate(question, parent_contents)
```

### ✅ 核心优势

- **高保真提取** - 表格和文本都保持原始结构
- **避免重复** - unstructured跳过表格区域，避免重复处理
- **细粒度检索** - 子分块提供精确的向量检索
- **丰富上下文** - 父分块提供完整的上下文信息
- **RAG优化** - 专门为RAG系统设计的存储架构

### 📁 结果存储

处理结果保存在 `parent_child_rag_results/` 目录：
- `child_chunks_*.json` - 子分块数据（用于向量数据库）
- `parent_chunks_*.json` - 父分块数据（用于文档存储）
- `parent_child_report_*.md` - 处理报告
- `parent_child_rag_*.json` - 完整结果数据

---

## 📚 项目中的其他组件

以下是项目中的核心组件，用于支持各种文档处理需求：

### 核心组件 (src/data/)
- `table_extractor.py` - 表格提取器
- `models.py` - 数据模型定义
- `document_processor.py` - 基础文档处理器
- `enhanced_document_processor.py` - 增强文档处理器
- `financial_report_chunker.py` - 财务报告分块器
- `parent_child_document_processor.py` - 父子分块处理器

### 使用建议
- **RAG系统** → 使用 `parent_child_rag_processor.py` ✅
- **财务报告专业处理** → 可考虑 `financial_report_chunker.py`
- **复杂文档架构** → 可考虑 `parent_child_document_processor.py`

---

**推荐：直接使用 `parent_child_rag_processor.py`，这是经过验证的最佳方案！**