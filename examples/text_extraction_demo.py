#!/usr/bin/env python3
"""
高保真文本提取演示脚本

演示如何使用unstructured解析PDF，跳过表格区域避免重复处理，
返回剩余的文本元素（标题、段落、列表等）。
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))

def demo_text_extraction():
    """演示高保真文本提取功能"""
    print("=" * 60)
    print("高保真文本提取演示")
    print("=" * 60)
    print()
    
    try:
        from src.data.parent_child_document_processor import ParentChildDocumentProcessor
        from src.data.models import TableChunk
        
        # 创建处理器
        config = {
            'parent_chunk_size': 2000,
            'child_chunk_size': 500,
            'child_chunk_overlap': 100
        }
        
        processor = ParentChildDocumentProcessor(config)
        print("✓ 父子文档处理器初始化成功")
        print()
        
        # 演示1: 表格边界框提取
        print("1. 表格边界框提取演示")
        print("-" * 30)
        
        mock_table_chunks = [
            TableChunk(
                table_id="demo_table_1",
                markdown_content="| 营业收入 | 净利润 | 总资产 |\n|---|---|---|\n| 1000万 | 100万 | 5000万 |",
                page_number=1,
                boundary_box={'x0': 100.0, 'y0': 200.0, 'x1': 400.0, 'y1': 300.0},
                table_type='financial'
            ),
            TableChunk(
                table_id="demo_table_2",
                markdown_content="| 项目 | 说明 |\n|---|---|\n| 主营业务 | 投资管理 |",
                page_number=2,
                boundary_box={'x0': 50.0, 'y0': 150.0, 'x1': 350.0, 'y1': 250.0},
                table_type='summary'
            )
        ]
        
        boundaries = processor._get_table_boundaries(mock_table_chunks)
        
        print(f"提取到 {len(boundaries)} 个表格边界框:")
        for i, boundary in enumerate(boundaries):
            print(f"  表格 {i+1}: 页面{boundary['page_number']}, "
                  f"坐标({boundary['x0']:.1f}, {boundary['y0']:.1f}, "
                  f"{boundary['x1']:.1f}, {boundary['y1']:.1f})")
        print()
        
        # 演示2: 文本内容表格判断
        print("2. 文本内容表格判断演示")
        print("-" * 30)
        
        test_texts = [
            ("营业收入 1000万 净利润 100万 资产总计 5000万", "财务数据文本"),
            ("公司简介：本公司成立于2020年，主要从事软件开发业务。", "普通描述文本"),
            ("revenue 1000万 profit 100万 equity 2000万", "英文财务文本"),
            ("会议纪要：董事会决定增加投资规模。", "会议记录文本")
        ]
        
        for text, description in test_texts:
            is_table = processor._is_text_likely_from_table(text)
            status = "✓ 表格文本" if is_table else "✗ 非表格文本"
            print(f"  {description}: {status}")
            print(f"    内容: {text[:30]}...")
        print()
        
        # 演示3: 文本元素过滤
        print("3. 文本元素过滤演示")
        print("-" * 30)
        
        # 模拟unstructured元素
        class MockElement:
            def __init__(self, text, category='Text', page_number=1):
                self.text = text
                self.category = category
                self.metadata = type('obj', (object,), {'page_number': page_number})()
        
        elements = [
            MockElement("第一章 公司概况", "Title", 1),
            MockElement("本公司是一家专业的投资管理公司，成立于2020年。", "Text", 1),
            MockElement("| 营收 | 利润 |\n| 1000 | 100 |", "Table", 1),
            MockElement("", "Text", 1),  # 空内容
            MockElement("第二章 业务分析", "Title", 2),
            MockElement("公司主要业务包括股权投资、债券投资等。", "Text", 2)
        ]
        
        print(f"原始元素数量: {len(elements)}")
        for i, elem in enumerate(elements):
            print(f"  元素 {i+1}: {elem.category} - {elem.text[:20]}...")
        
        # 过滤元素
        filtered = processor._filter_table_overlapping_elements(elements, boundaries)
        
        print(f"\n过滤后元素数量: {len(filtered)}")
        for i, elem in enumerate(filtered):
            print(f"  元素 {i+1}: {elem.category} - {elem.text[:30]}...")
        print()
        
        # 演示4: 父分块创建
        print("4. 父分块创建演示")
        print("-" * 30)
        
        # 使用过滤后的元素创建父分块
        parent_chunks = processor._create_parent_chunks_from_elements(filtered, "demo.pdf")
        
        print(f"创建了 {len(parent_chunks)} 个父分块:")
        for i, chunk in enumerate(parent_chunks):
            print(f"  父分块 {i+1}:")
            print(f"    ID: {chunk.parent_id}")
            print(f"    页面: {chunk.page_numbers}")
            print(f"    内容长度: {len(chunk.content)} 字符")
            print(f"    提取方法: {chunk.metadata.get('extraction_method', 'unknown')}")
            print(f"    内容预览: {chunk.content[:50]}...")
            print()
        
        # 演示5: 备用文本提取
        print("5. 备用文本提取演示")
        print("-" * 30)
        
        from unittest.mock import Mock, patch
        
        # 模拟文档处理器返回的文档
        mock_doc = Mock()
        mock_doc.content = "这是备用方法提取的文本内容，当unstructured不可用时使用。"
        mock_doc.page_number = 1
        
        with patch.object(processor.document_processor, 'parse_pdf', return_value=[mock_doc]):
            backup_elements = processor._fallback_text_extraction("demo.pdf")
        
        print(f"备用方法提取了 {len(backup_elements)} 个文本元素:")
        for i, elem in enumerate(backup_elements):
            print(f"  元素 {i+1}: {elem.category} - {elem.text}")
        print()
        
        print("=" * 60)
        print("演示完成！")
        print()
        print("高保真文本提取的主要特点:")
        print("- ✅ 使用unstructured解析PDF文档")
        print("- ✅ 获取pdfplumber提取的表格边界框")
        print("- ✅ 指示unstructured跳过表格区域")
        print("- ✅ 避免重复处理表格内容")
        print("- ✅ 返回纯文本元素（标题、段落、列表等）")
        print("- ✅ 提供备用文本提取方案")
        print("- ✅ 支持按页面组织父子分块")
        
        return True
        
    except Exception as e:
        print(f"演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = demo_text_extraction()
    if success:
        print("\n🎉 高保真文本提取演示成功完成！")
    else:
        print("\n❌ 演示过程中出现错误")
    
    sys.exit(0 if success else 1)