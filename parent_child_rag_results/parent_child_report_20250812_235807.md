# 父子分块RAG处理报告

## 基本信息
- **文件**: data/reports/600580_卧龙电驱2025-04-26_卧龙电驱2024年年度报告_2105.pdf
- **处理时间**: 2025-08-12T23:58:07.829030
- **处理方法**: parent_child_rag

## 分块统计
- **子分块总数**: 313
  - 表格子分块: 313
  - 文本子分块: 0
- **父分块总数**: 64
- **跳过的表格区域**: 313

## 父子分块RAG架构

### 🎯 处理流程
1. **高保真表格提取** - pdfplumber提取313个表格，转为Markdown子分块
2. **高保真文本提取** - unstructured跳过313个表格区域，提取文本元素
3. **文本二次分块** - 递归分块生成0个文本子分块
4. **构建父子关系** - 创建64个父分块，关联所有子分块
5. **RAG存储准备** - 子分块用于向量化，父分块用于上下文检索

### 📊 存储架构
- **向量数据库**: 存储313个子分块的向量表示
- **文档存储**: 存储64个父分块的完整内容（键值对）

### 🔍 检索流程
1. 用户提问 → 向量数据库检索相关子分块
2. 从子分块元数据提取父分块ID
3. 从文档存储获取父分块完整内容
4. 将父分块内容提交给LLM生成答案

## 配置参数
- **子分块大小**: 800
- **子分块重叠**: 100
- **父分块策略**: page_group
- **每组页数**: 3

## RAG系统集成指南

### 1. 向量数据库存储
```python
# 存储子分块到向量数据库
for child_chunk in result['child_chunks']:
    vector = embed_text(child_chunk['content'])
    vector_db.store(
        id=child_chunk['chunk_id'],
        vector=vector,
        metadata=child_chunk['metadata']
    )
```

### 2. 文档存储
```python
# 存储父分块到文档存储
for parent_id, parent_data in result['parent_chunks'].items():
    doc_store[parent_id] = parent_data['content']
```

### 3. 检索查询
```python
# 检索流程
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

## 优势特点
- ✅ **高保真提取**: 表格和文本都保持原始结构
- ✅ **避免重复**: unstructured跳过表格区域，避免重复处理
- ✅ **细粒度检索**: 子分块提供精确的向量检索
- ✅ **丰富上下文**: 父分块提供完整的上下文信息
- ✅ **灵活配置**: 支持多种父分块策略
- ✅ **RAG优化**: 专门为RAG系统设计的存储架构

