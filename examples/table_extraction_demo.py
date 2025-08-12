#!/usr/bin/env python3
"""
高保真表格提取功能演示

展示任务 3.1 实现的核心功能：
- 使用pdfplumber提取PDF表格
- 将表格序列化为Markdown格式
- 记录页码和边界框信息
- 集成到父子分块架构中
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.data.table_extractor import create_table_extractor
from src.data.parent_child_document_processor import create_parent_child_processor
from src.data.models import TableChunk


def demo_table_extractor():
    """演示表格提取器功能"""
    print("=" * 60)
    print("表格提取器功能演示")
    print("=" * 60)
    
    # 创建表格提取器
    extractor = create_table_extractor({
        'min_table_rows': 2,
        'min_table_cols': 2
    })
    
    print("✓ 表格提取器创建成功")
    print(f"  - 最小行数要求: {extractor.min_table_rows}")
    print(f"  - 最小列数要求: {extractor.min_table_cols}")
    print()
    
    # 模拟表格数据验证
    print("1. 表格数据验证功能:")
    
    valid_table = [
        ['公司名称', '营业收入(万元)', '净利润(万元)', '总资产(万元)'],
        ['公司A', '10000', '1000', '50000'],
        ['公司B', '12000', '1200', '55000'],
        ['公司C', '8000', '800', '40000']
    ]
    
    is_valid = extractor._is_valid_table(valid_table)
    print(f"  - 有效表格验证: {'✓ 通过' if is_valid else '✗ 失败'}")
    
    invalid_table = [['单列数据']]
    is_invalid = not extractor._is_valid_table(invalid_table)
    print(f"  - 无效表格过滤: {'✓ 通过' if is_invalid else '✗ 失败'}")
    print()
    
    # DataFrame转换
    print("2. DataFrame转换功能:")
    df = extractor._convert_to_dataframe(valid_table)
    print(f"  - 转换后形状: {df.shape}")
    print(f"  - 列名: {list(df.columns)}")
    print(f"  - 示例数据: {df.iloc[0, 0]} -> {df.iloc[0, 1]}")
    print()
    
    # Markdown序列化
    print("3. Markdown序列化功能:")
    markdown = extractor._serialize_to_markdown(df)
    print("  - Markdown输出预览:")
    print("    " + "\n    ".join(markdown.split('\n')[:4]))
    print("    ...")
    print()
    
    # 表格类型分类
    print("4. 表格类型分类功能:")
    table_type = extractor._classify_table_type(df, "财务数据汇总表")
    print(f"  - 分类结果: {table_type}")
    print(f"  - 分类说明: {'财务相关表格' if table_type == 'financial' else '其他类型表格'}")
    print()


def demo_table_chunk_model():
    """演示表格分块数据模型"""
    print("=" * 60)
    print("表格分块数据模型演示")
    print("=" * 60)
    
    # 创建表格分块示例
    table_chunk = TableChunk(
        table_id="demo_table_001",
        markdown_content="""| 财务指标 | 2023年 | 2024年 | 增长率 |
|----------|--------|--------|--------|
| 营业收入(万元) | 10000 | 12000 | 20% |
| 净利润(万元) | 1000 | 1500 | 50% |
| 总资产(万元) | 50000 | 60000 | 20% |""",
        page_number=1,
        boundary_box={
            'x0': 50.0,
            'y0': 100.0,
            'x1': 400.0,
            'y1': 250.0
        },
        table_type='financial'
    )
    
    print("✓ 表格分块创建成功")
    print(f"  - 表格ID: {table_chunk.table_id}")
    print(f"  - 页码: {table_chunk.page_number}")
    print(f"  - 类型: {table_chunk.table_type}")
    print(f"  - 边界框: x0={table_chunk.boundary_box['x0']}, y0={table_chunk.boundary_box['y0']}")
    print(f"            x1={table_chunk.boundary_box['x1']}, y1={table_chunk.boundary_box['y1']}")
    print()
    
    print("Markdown内容预览:")
    lines = table_chunk.markdown_content.split('\n')
    for i, line in enumerate(lines[:5]):
        print(f"  {i+1:2d}: {line}")
    print()


def demo_parent_child_integration():
    """演示父子分块集成"""
    print("=" * 60)
    print("父子分块架构集成演示")
    print("=" * 60)
    
    # 创建父子文档处理器
    processor = create_parent_child_processor({
        'parent_chunk_size': 2000,
        'child_chunk_size': 500,
        'child_chunk_overlap': 100,
        'table_extraction': {
            'min_table_rows': 2,
            'min_table_cols': 2
        }
    })
    
    print("✓ 父子文档处理器创建成功")
    print(f"  - 父分块大小: {processor.parent_chunk_size}")
    print(f"  - 子分块大小: {processor.child_chunk_size}")
    print(f"  - 重叠大小: {processor.child_chunk_overlap}")
    print()
    
    # 演示文本分割功能
    print("文本分割功能演示:")
    sample_text = """
    本公司是一家专业从事投资分析的金融服务公司。我们的主要业务包括股票分析、债券评级、投资组合管理等。
    
    根据最新的财务报表分析，公司在2024年第一季度实现了显著增长。营业收入达到1.2亿元，同比增长25%。
    净利润为2000万元，同比增长30%。这一业绩表现超出了市场预期。
    
    公司的核心竞争优势在于专业的分析团队和先进的数据处理技术。我们拥有超过50名资深分析师，
    平均从业经验超过10年。同时，公司投入大量资源开发人工智能分析系统，提高分析效率和准确性。
    """.strip()
    
    segments = processor._split_text_into_segments(sample_text, 200, 50)
    
    print(f"  - 原文长度: {len(sample_text)} 字符")
    print(f"  - 分割片段数: {len(segments)}")
    print("  - 片段预览:")
    
    for i, segment in enumerate(segments[:3]):
        preview = segment[:80] + "..." if len(segment) > 80 else segment
        print(f"    片段 {i+1}: {preview}")
    
    if len(segments) > 3:
        print(f"    ... (还有 {len(segments) - 3} 个片段)")
    print()


def demo_statistics():
    """演示统计功能"""
    print("=" * 60)
    print("统计功能演示")
    print("=" * 60)
    
    # 创建表格提取器
    extractor = create_table_extractor()
    
    # 模拟表格分块数据
    mock_table_chunks = [
        TableChunk(
            table_id="table_1",
            markdown_content="| 指标 | 值 |\n|---|---|\n| 营收 | 1000万 |",
            page_number=1,
            boundary_box={'x0': 0, 'y0': 0, 'x1': 100, 'y1': 50},
            table_type='financial'
        ),
        TableChunk(
            table_id="table_2",
            markdown_content="| 项目 | 描述 |\n|---|---|\n| 概述 | 重点内容 |",
            page_number=1,
            boundary_box={'x0': 0, 'y0': 60, 'x1': 100, 'y1': 110},
            table_type='summary'
        ),
        TableChunk(
            table_id="table_3",
            markdown_content="| 名称 | 部门 |\n|---|---|\n| 张三 | 技术部 |",
            page_number=2,
            boundary_box={'x0': 0, 'y0': 0, 'x1': 100, 'y1': 50},
            table_type='other'
        )
    ]
    
    # 获取统计信息
    stats = extractor.get_extraction_stats(mock_table_chunks)
    
    print("表格提取统计信息:")
    print(f"  - 总表格数: {stats['total_tables']}")
    print(f"  - 包含表格的页面数: {stats['pages_with_tables']}")
    print(f"  - 平均表格大小: {stats['avg_table_size']:.1f} 字符")
    print("  - 表格类型分布:")
    for table_type, count in stats['table_types'].items():
        print(f"    * {table_type}: {count} 个")
    print("  - 页面分布:")
    for page, count in stats['page_distribution'].items():
        print(f"    * 第{page}页: {count} 个表格")
    print()


def main():
    """主演示函数"""
    print("🎯 任务 3.1 - 高保真表格提取实现功能演示")
    print()
    
    try:
        demo_table_extractor()
        demo_table_chunk_model()
        demo_parent_child_integration()
        demo_statistics()
        
        print("=" * 60)
        print("🎉 演示完成！")
        print()
        print("核心功能总结:")
        print("✅ pdfplumber表格提取 - 支持多种表格格式识别")
        print("✅ Markdown序列化 - 高质量表格内容保存")
        print("✅ 边界框记录 - 精确的位置信息")
        print("✅ 表格分类 - 智能识别财务、摘要等类型")
        print("✅ 父子分块集成 - 无缝融入文档处理架构")
        print("✅ 单元测试覆盖 - 确保功能稳定性")
        print()
        print("满足需求:")
        print("📋 需求1.1 - 高保真PDF表格提取")
        print("📋 需求1.2 - 结构化数据处理")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)