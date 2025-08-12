#!/usr/bin/env python3
"""
父子分块RAG处理器

完整的父子分块RAG流程实现：
1. 【解析】高保真表格提取 - pdfplumber提取表格，转为Markdown子分块
2. 【解析】高保真文本提取 - unstructured跳过表格区域，提取文本元素
3. 【分块】文本的二次分块 - 递归字符分块，形成细粒度子分块
4. 【富化与索引】构建父子关系 - 定义父分块，关联子分块，存储元数据
5. 【检索】执行父子文档检索 - 检索子分块，返回父分块完整内容
"""

import sys
import os
import uuid
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

try:
    import pdfplumber
    from unstructured.partition.pdf import partition_pdf
    from unstructured.documents.elements import Table as UnstructuredTable, Text, Title
    import pandas as pd
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

@dataclass
class TableChunk:
    """表格子分块"""
    chunk_id: str
    content: str  # Markdown格式
    page_number: int
    bbox: Dict[str, float]  # 边界框
    table_type: str
    row_count: int
    col_count: int
    parent_id: str

@dataclass
class TextChunk:
    """文本子分块"""
    chunk_id: str
    content: str
    page_number: Optional[int]
    element_type: str  # Title, Text, etc.
    parent_id: str
    char_count: int

@dataclass
class ParentChunk:
    """父分块"""
    parent_id: str
    title: str
    content: str  # 完整内容
    page_range: Tuple[int, int]
    child_ids: List[str]
    chunk_type: str  # chapter, section, page_group

class ParentChildRAGProcessor:
    """父子分块RAG处理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 表格提取配置
        self.table_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3
        }
        
        # 文本分块配置
        self.child_chunk_size = self.config.get('child_chunk_size', 800)
        self.child_chunk_overlap = self.config.get('child_chunk_overlap', 100)
        
        # 父分块配置
        self.parent_strategy = self.config.get('parent_strategy', 'page_group')  # chapter, section, page_group
        self.pages_per_parent = self.config.get('pages_per_parent', 3)
        
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("需要安装: pip install pdfplumber unstructured pandas")
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        完整的父子分块RAG流程
        
        Returns:
            {
                'child_chunks': List[Dict],  # 所有子分块（用于向量化）
                'parent_chunks': Dict[str, Dict],  # 父分块存储（键值对）
                'metadata': Dict,
                'stats': Dict
            }
        """
        print("🚀 开始父子分块RAG处理...")
        
        # Step 1: 高保真表格提取
        print("📊 Step 1: 高保真表格提取...")
        table_chunks, table_bboxes = self._extract_table_chunks(pdf_path)
        print(f"   ✓ 提取到 {len(table_chunks)} 个表格子分块")
        
        # Step 2: 高保真文本提取（跳过表格区域）
        print("📝 Step 2: 高保真文本提取...")
        text_elements = self._extract_text_elements(pdf_path, table_bboxes)
        print(f"   ✓ 提取到 {len(text_elements)} 个文本元素")
        
        # Step 3: 文本的二次分块
        print("✂️  Step 3: 文本的二次分块...")
        text_chunks = self._chunk_text_elements(text_elements)
        print(f"   ✓ 生成 {len(text_chunks)} 个文本子分块")
        
        # Step 4: 构建父子关系
        print("🔗 Step 4: 构建父子关系...")
        parent_chunks = self._build_parent_child_relationships(table_chunks, text_chunks)
        print(f"   ✓ 构建 {len(parent_chunks)} 个父分块")
        
        # Step 5: 准备RAG存储格式
        print("💾 Step 5: 准备RAG存储格式...")
        child_chunks_for_vector_db = self._prepare_child_chunks_for_vector_db(table_chunks, text_chunks)
        parent_chunks_for_doc_store = self._prepare_parent_chunks_for_doc_store(parent_chunks)
        
        result = {
            'child_chunks': child_chunks_for_vector_db,  # 用于向量数据库
            'parent_chunks': parent_chunks_for_doc_store,  # 用于文档存储
            'metadata': {
                'source_file': pdf_path,
                'processing_method': 'parent_child_rag',
                'config': self.config,
                'processed_at': datetime.now().isoformat()
            },
            'stats': {
                'total_child_chunks': len(child_chunks_for_vector_db),
                'table_child_chunks': len(table_chunks),
                'text_child_chunks': len(text_chunks),
                'parent_chunks': len(parent_chunks),
                'table_bboxes_excluded': len(table_bboxes)
            }
        }
        
        print("✅ 父子分块RAG处理完成！")
        return result
    
    def _extract_table_chunks(self, pdf_path: str) -> Tuple[List[TableChunk], List[Dict]]:
        """Step 1: 使用pdfplumber提取表格，转为Markdown子分块"""
        table_chunks = []
        table_bboxes = []  # 用于告诉unstructured跳过这些区域
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.find_tables(table_settings=self.table_settings)
                
                for table_idx, table in enumerate(tables):
                    try:
                        # 提取表格数据
                        raw_data = table.extract()
                        if not raw_data or len(raw_data) < 2:
                            continue
                        
                        # 转换为DataFrame
                        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                        df = df.dropna(how='all').dropna(axis=1, how='all')
                        
                        if df.empty:
                            continue
                        
                        # 转换为Markdown
                        markdown_content = self._dataframe_to_markdown(df)
                        
                        # 记录边界框（用于unstructured跳过）
                        bbox = {
                            'page': page_num,
                            'x0': float(table.bbox[0]),
                            'y0': float(table.bbox[1]),
                            'x1': float(table.bbox[2]),
                            'y1': float(table.bbox[3])
                        }
                        table_bboxes.append(bbox)
                        
                        # 创建表格子分块（暂时没有parent_id，后续分配）
                        table_chunk = TableChunk(
                            chunk_id=f"table_{page_num}_{table_idx}_{str(uuid.uuid4())[:8]}",
                            content=markdown_content,
                            page_number=page_num,
                            bbox=bbox,
                            table_type=self._classify_table_type(df),
                            row_count=len(df),
                            col_count=len(df.columns),
                            parent_id=""  # 后续分配
                        )
                        
                        table_chunks.append(table_chunk)
                        
                    except Exception as e:
                        print(f"   ⚠️  页面{page_num}表格{table_idx}处理失败: {e}")
                        continue
        
        return table_chunks, table_bboxes
    
    def _extract_text_elements(self, pdf_path: str, table_bboxes: List[Dict]) -> List[Dict]:
        """Step 2: 使用unstructured提取文本，跳过表格区域"""
        try:
            # 使用unstructured解析PDF
            elements = partition_pdf(
                filename=pdf_path,
                strategy="fast",
                infer_table_structure=False,  # 关键：不解析表格
                extract_images_in_pdf=False,
                include_page_breaks=True
            )
            
            # 过滤掉表格区域的文本
            text_elements = []
            for element in elements:
                if not hasattr(element, 'text') or not element.text.strip():
                    continue
                
                text = element.text.strip()
                
                # 跳过可能的表格内容
                if self._is_likely_table_content(text, table_bboxes):
                    continue
                
                # 获取元素类型
                element_type = type(element).__name__
                
                # 尝试获取页码（如果有的话）
                page_number = getattr(element, 'metadata', {}).get('page_number', None)
                
                text_elements.append({
                    'content': text,
                    'element_type': element_type,
                    'page_number': page_number,
                    'char_count': len(text)
                })
            
            return text_elements
            
        except Exception as e:
            print(f"   ⚠️  文本提取失败: {e}")
            return []
    
    def _chunk_text_elements(self, text_elements: List[Dict]) -> List[TextChunk]:
        """Step 3: 对文本元素进行二次分块"""
        text_chunks = []
        
        for element in text_elements:
            content = element['content']
            
            # 如果文本较短，直接作为一个子分块
            if len(content) <= self.child_chunk_size:
                chunk = TextChunk(
                    chunk_id=f"text_{str(uuid.uuid4())[:8]}",
                    content=content,
                    page_number=element['page_number'],
                    element_type=element['element_type'],
                    parent_id="",  # 后续分配
                    char_count=len(content)
                )
                text_chunks.append(chunk)
            else:
                # 对长文本进行递归分块
                sub_chunks = self._recursive_text_split(content, element)
                text_chunks.extend(sub_chunks)
        
        return text_chunks
    
    def _recursive_text_split(self, text: str, element: Dict) -> List[TextChunk]:
        """递归分割长文本"""
        chunks = []
        
        # 智能分割点
        separators = ['\n\n', '\n', '。', '！', '？', '.', '!', '?', ' ']
        
        start = 0
        while start < len(text):
            end = start + self.child_chunk_size
            
            if end >= len(text):
                # 最后一块
                chunk_text = text[start:].strip()
                if chunk_text:
                    chunk = TextChunk(
                        chunk_id=f"text_{str(uuid.uuid4())[:8]}",
                        content=chunk_text,
                        page_number=element['page_number'],
                        element_type=element['element_type'],
                        parent_id="",  # 后续分配
                        char_count=len(chunk_text)
                    )
                    chunks.append(chunk)
                break
            
            # 寻找最佳分割点
            segment = text[start:end]
            best_split = -1
            
            for separator in separators:
                split_pos = segment.rfind(separator)
                if split_pos > self.child_chunk_size * 0.7:  # 至少70%的目标长度
                    best_split = start + split_pos + len(separator)
                    break
            
            if best_split == -1:
                best_split = end
            
            chunk_text = text[start:best_split].strip()
            if chunk_text:
                chunk = TextChunk(
                    chunk_id=f"text_{str(uuid.uuid4())[:8]}",
                    content=chunk_text,
                    page_number=element['page_number'],
                    element_type=element['element_type'],
                    parent_id="",  # 后续分配
                    char_count=len(chunk_text)
                )
                chunks.append(chunk)
            
            # 下一个起点（考虑重叠）
            start = max(best_split - self.child_chunk_overlap, start + 1)
        
        return chunks
    
    def _build_parent_child_relationships(self, table_chunks: List[TableChunk], text_chunks: List[TextChunk]) -> List[ParentChunk]:
        """Step 4: 构建父子关系"""
        parent_chunks = []
        
        if self.parent_strategy == 'page_group':
            parent_chunks = self._build_page_group_parents(table_chunks, text_chunks)
        elif self.parent_strategy == 'chapter':
            parent_chunks = self._build_chapter_parents(table_chunks, text_chunks)
        else:
            # 默认使用页面分组
            parent_chunks = self._build_page_group_parents(table_chunks, text_chunks)
        
        return parent_chunks
    
    def _build_page_group_parents(self, table_chunks: List[TableChunk], text_chunks: List[TextChunk]) -> List[ParentChunk]:
        """按页面分组构建父分块"""
        parent_chunks = []
        
        # 收集所有页码
        all_pages = set()
        for chunk in table_chunks:
            all_pages.add(chunk.page_number)
        for chunk in text_chunks:
            if chunk.page_number:
                all_pages.add(chunk.page_number)
        
        if not all_pages:
            return parent_chunks
        
        # 按页面分组
        sorted_pages = sorted(all_pages)
        
        for i in range(0, len(sorted_pages), self.pages_per_parent):
            page_group = sorted_pages[i:i + self.pages_per_parent]
            start_page = page_group[0]
            end_page = page_group[-1]
            
            parent_id = f"parent_pages_{start_page}_{end_page}_{str(uuid.uuid4())[:8]}"
            
            # 收集这个页面组的所有子分块
            child_ids = []
            parent_content_parts = []
            
            # 添加表格子分块
            for chunk in table_chunks:
                if chunk.page_number in page_group:
                    chunk.parent_id = parent_id
                    child_ids.append(chunk.chunk_id)
                    parent_content_parts.append(f"[表格 - 页面{chunk.page_number}]\n{chunk.content}\n")
            
            # 添加文本子分块
            for chunk in text_chunks:
                if chunk.page_number in page_group:
                    chunk.parent_id = parent_id
                    child_ids.append(chunk.chunk_id)
                    parent_content_parts.append(chunk.content)
            
            # 创建父分块
            if child_ids:
                parent_chunk = ParentChunk(
                    parent_id=parent_id,
                    title=f"页面 {start_page}-{end_page}",
                    content="\n\n".join(parent_content_parts),
                    page_range=(start_page, end_page),
                    child_ids=child_ids,
                    chunk_type="page_group"
                )
                parent_chunks.append(parent_chunk)
        
        return parent_chunks
    
    def _build_chapter_parents(self, table_chunks: List[TableChunk], text_chunks: List[TextChunk]) -> List[ParentChunk]:
        """按章节构建父分块（简化版本）"""
        # 这里可以实现更复杂的章节识别逻辑
        # 目前先用页面分组作为替代
        return self._build_page_group_parents(table_chunks, text_chunks)
    
    def _prepare_child_chunks_for_vector_db(self, table_chunks: List[TableChunk], text_chunks: List[TextChunk]) -> List[Dict]:
        """准备子分块用于向量数据库存储"""
        child_chunks = []
        
        # 表格子分块
        for chunk in table_chunks:
            child_chunks.append({
                'chunk_id': chunk.chunk_id,
                'content': chunk.content,
                'chunk_type': 'table',
                'parent_id': chunk.parent_id,
                'metadata': {
                    'page_number': chunk.page_number,
                    'table_type': chunk.table_type,
                    'row_count': chunk.row_count,
                    'col_count': chunk.col_count,
                    'bbox': chunk.bbox
                }
            })
        
        # 文本子分块
        for chunk in text_chunks:
            child_chunks.append({
                'chunk_id': chunk.chunk_id,
                'content': chunk.content,
                'chunk_type': 'text',
                'parent_id': chunk.parent_id,
                'metadata': {
                    'page_number': chunk.page_number,
                    'element_type': chunk.element_type,
                    'char_count': chunk.char_count
                }
            })
        
        return child_chunks
    
    def _prepare_parent_chunks_for_doc_store(self, parent_chunks: List[ParentChunk]) -> Dict[str, Dict]:
        """准备父分块用于文档存储（键值对）"""
        parent_store = {}
        
        for chunk in parent_chunks:
            parent_store[chunk.parent_id] = {
                'parent_id': chunk.parent_id,
                'title': chunk.title,
                'content': chunk.content,
                'page_range': chunk.page_range,
                'child_ids': chunk.child_ids,
                'chunk_type': chunk.chunk_type
            }
        
        return parent_store
    
    def _dataframe_to_markdown(self, df: pd.DataFrame) -> str:
        """DataFrame转Markdown"""
        if df.empty:
            return ""
        
        try:
            return df.to_markdown(index=False, tablefmt='pipe')
        except:
            # 手动构建Markdown表格
            lines = []
            headers = [str(col) for col in df.columns]
            header_line = "| " + " | ".join(headers) + " |"
            lines.append(header_line)
            
            separator_line = "|" + "|".join([" --- " for _ in headers]) + "|"
            lines.append(separator_line)
            
            for _, row in df.iterrows():
                row_values = [str(val) if pd.notna(val) else "" for val in row]
                row_line = "| " + " | ".join(row_values) + " |"
                lines.append(row_line)
            
            return "\n".join(lines)
    
    def _classify_table_type(self, df: pd.DataFrame) -> str:
        """表格类型分类"""
        financial_keywords = [
            '营收', '收入', '利润', '资产', '负债', '现金流', '毛利率',
            'revenue', 'income', 'profit', 'asset', 'liability'
        ]
        
        table_text = df.to_string().lower()
        for keyword in financial_keywords:
            if keyword.lower() in table_text:
                return 'financial'
        
        return 'other'
    
    def _is_likely_table_content(self, text: str, table_bboxes: List[Dict]) -> bool:
        """判断是否是表格内容（简化版本）"""
        # 数字密度检查
        numbers = re.findall(r'\d+', text)
        words = text.split()
        if len(words) > 0 and len(numbers) > len(words) * 0.6:
            return True
        
        # 表格关键词检查
        table_keywords = ['营业收入', '净利润', '资产', '负债', '现金流', '毛利率', '万元', '千元']
        keyword_count = sum(1 for keyword in table_keywords if keyword in text)
        if keyword_count >= 2:
            return True
        
        return False
    
    def save_results(self, result: Dict[str, Any], output_dir: str = "parent_child_rag_results"):
        """保存父子分块RAG结果"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存完整结果
        result_file = output_path / f"parent_child_rag_{timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 保存子分块（用于向量数据库）
        child_chunks_file = output_path / f"child_chunks_{timestamp}.json"
        with open(child_chunks_file, 'w', encoding='utf-8') as f:
            json.dump(result['child_chunks'], f, ensure_ascii=False, indent=2)
        
        # 保存父分块（用于文档存储）
        parent_chunks_file = output_path / f"parent_chunks_{timestamp}.json"
        with open(parent_chunks_file, 'w', encoding='utf-8') as f:
            json.dump(result['parent_chunks'], f, ensure_ascii=False, indent=2)
        
        # 生成报告
        report_file = output_path / f"parent_child_report_{timestamp}.md"
        self._generate_report(result, report_file)
        
        print(f"💾 父子分块RAG结果已保存到:")
        print(f"   📋 报告: {report_file}")
        print(f"   👶 子分块: {child_chunks_file}")
        print(f"   👨 父分块: {parent_chunks_file}")
        print(f"   💾 完整数据: {result_file}")
        
        return {
            'report_file': report_file,
            'child_chunks_file': child_chunks_file,
            'parent_chunks_file': parent_chunks_file,
            'result_file': result_file
        }
    
    def _generate_report(self, result: Dict[str, Any], report_file: Path):
        """生成父子分块RAG报告"""
        stats = result['stats']
        
        report_content = f"""# 父子分块RAG处理报告

## 基本信息
- **文件**: {result['metadata']['source_file']}
- **处理时间**: {result['metadata']['processed_at']}
- **处理方法**: {result['metadata']['processing_method']}

## 分块统计
- **子分块总数**: {stats['total_child_chunks']}
  - 表格子分块: {stats['table_child_chunks']}
  - 文本子分块: {stats['text_child_chunks']}
- **父分块总数**: {stats['parent_chunks']}
- **跳过的表格区域**: {stats['table_bboxes_excluded']}

## 父子分块RAG架构

### 🎯 处理流程
1. **高保真表格提取** - pdfplumber提取{stats['table_child_chunks']}个表格，转为Markdown子分块
2. **高保真文本提取** - unstructured跳过{stats['table_bboxes_excluded']}个表格区域，提取文本元素
3. **文本二次分块** - 递归分块生成{stats['text_child_chunks']}个文本子分块
4. **构建父子关系** - 创建{stats['parent_chunks']}个父分块，关联所有子分块
5. **RAG存储准备** - 子分块用于向量化，父分块用于上下文检索

### 📊 存储架构
- **向量数据库**: 存储{stats['total_child_chunks']}个子分块的向量表示
- **文档存储**: 存储{stats['parent_chunks']}个父分块的完整内容（键值对）

### 🔍 检索流程
1. 用户提问 → 向量数据库检索相关子分块
2. 从子分块元数据提取父分块ID
3. 从文档存储获取父分块完整内容
4. 将父分块内容提交给LLM生成答案

## 配置参数
- **子分块大小**: {result['metadata']['config'].get('child_chunk_size', 800)}
- **子分块重叠**: {result['metadata']['config'].get('child_chunk_overlap', 100)}
- **父分块策略**: {result['metadata']['config'].get('parent_strategy', 'page_group')}
- **每组页数**: {result['metadata']['config'].get('pages_per_parent', 3)}

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

"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

def demo_parent_child_rag():
    """演示父子分块RAG处理"""
    print("🚀 父子分块RAG处理演示")
    print("=" * 80)
    
    pdf_path = "data/reports/600580_卧龙电驱2025-04-26_卧龙电驱2024年年度报告_2105.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return
    
    try:
        # 配置参数
        config = {
            'child_chunk_size': 800,
            'child_chunk_overlap': 100,
            'parent_strategy': 'page_group',
            'pages_per_parent': 3
        }
        
        processor = ParentChildRAGProcessor(config)
        
        # 处理PDF
        result = processor.process_pdf(pdf_path)
        
        # 显示结果
        print("\n📊 父子分块RAG结果:")
        stats = result['stats']
        print(f"  子分块总数: {stats['total_child_chunks']}")
        print(f"    - 表格子分块: {stats['table_child_chunks']}")
        print(f"    - 文本子分块: {stats['text_child_chunks']}")
        print(f"  父分块总数: {stats['parent_chunks']}")
        print(f"  跳过表格区域: {stats['table_bboxes_excluded']}")
        
        # 显示示例
        print("\n📋 子分块示例:")
        for i, chunk in enumerate(result['child_chunks'][:5]):
            print(f"  {i+1}. [{chunk['chunk_type']}] {chunk['chunk_id'][:20]}... (父分块: {chunk['parent_id'][:15]}...)")
        
        print("\n📋 父分块示例:")
        for i, (parent_id, parent_data) in enumerate(list(result['parent_chunks'].items())[:3]):
            print(f"  {i+1}. {parent_data['title']} - {len(parent_data['child_ids'])}个子分块")
        
        # 保存结果
        files = processor.save_results(result)
        
        print("\n✅ 父子分块RAG处理完成！")
        print("\n🎯 RAG系统集成:")
        print("  1. 将child_chunks.json中的子分块向量化存入向量数据库")
        print("  2. 将parent_chunks.json中的父分块存入文档存储")
        print("  3. 检索时：子分块检索 → 父分块上下文 → LLM生成答案")
        
        return result
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    demo_parent_child_rag()