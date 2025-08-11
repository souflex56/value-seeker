#!/usr/bin/env python3
"""
测试当前PDF处理和分块功能
"""

import sys
import os
from pathlib import Path
sys.path.append('.')

def test_current_pdf_processing():
    """测试当前的PDF处理功能"""
    try:
        from src.data.document_processor import DocumentProcessor
        
        # 配置
        config = {
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'min_chunk_size': 100,
            'pdf_strategy': 'fast',
            'use_high_res': False
        }
        
        # 初始化处理器
        processor = DocumentProcessor(config)
        
        # PDF文件路径
        pdf_path = "data/reports/600580_卧龙电驱2025-04-26_卧龙电驱2024年年度报告_2105.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF文件不存在: {pdf_path}")
            return False
        
        print(f"🔍 开始处理PDF: {pdf_path}")
        print(f"📄 文件大小: {os.path.getsize(pdf_path) / 1024 / 1024:.2f} MB")
        
        # 解析PDF
        print("\n📖 步骤1: 解析PDF文档...")
        documents = processor.parse_pdf(pdf_path)
        print(f"✅ 解析完成，共生成 {len(documents)} 个文档页面")
        
        # 显示前几个文档的信息
        print("\n📋 文档信息预览:")
        for i, doc in enumerate(documents[:3]):
            print(f"  页面 {doc.page_number}:")
            print(f"    内容长度: {len(doc.content)} 字符")
            print(f"    表格数量: {len(doc.tables)}")
            print(f"    内容预览: {doc.content[:100].replace(chr(10), ' ')}...")
            if doc.tables:
                print(f"    表格类型: {[t.table_type for t in doc.tables]}")
            print()
        
        # 文档分块
        print("✂️  步骤2: 文档分块...")
        chunks = processor.chunk_documents(documents)
        print(f"✅ 分块完成，共生成 {len(chunks)} 个文档块")
        
        # 显示分块统计
        print("\n📊 分块统计:")
        chunk_lengths = [len(chunk.content) for chunk in chunks]
        print(f"  平均块长度: {sum(chunk_lengths) / len(chunk_lengths):.0f} 字符")
        print(f"  最短块长度: {min(chunk_lengths)} 字符")
        print(f"  最长块长度: {max(chunk_lengths)} 字符")
        
        # 显示前几个块的信息
        print("\n📝 块信息预览:")
        for i, chunk in enumerate(chunks[:5]):
            print(f"  块 {i+1} (ID: {chunk.chunk_id}):")
            print(f"    页码: {chunk.metadata.get('page_number', 'N/A')}")
            print(f"    长度: {len(chunk.content)} 字符")
            print(f"    分块方法: {chunk.metadata.get('chunking_method', 'N/A')}")
            print(f"    内容预览: {chunk.content[:80].replace(chr(10), ' ')}...")
            print()
        
        # 表格处理
        print("📊 步骤3: 表格处理...")
        all_tables = []
        for doc in documents:
            if doc.tables:
                tables = processor.process_tables(doc)
                all_tables.extend(tables)
        
        print(f"✅ 表格处理完成，共处理 {len(all_tables)} 个表格")
        
        if all_tables:
            print("\n📈 表格信息预览:")
            for i, table in enumerate(all_tables[:3]):
                print(f"  表格 {i+1}:")
                print(f"    页码: {table.page_number}")
                print(f"    类型: {table.table_type}")
                print(f"    标题: {table.caption[:50]}...")
                print(f"    形状: {table.data.shape}")
                print(f"    列名: {list(table.data.columns)[:5]}")
                print()
        
        # 财务数据提取
        if all_tables:
            print("💰 步骤4: 财务数据提取...")
            financial_data = processor.extract_financial_data(all_tables)
            print(f"✅ 财务数据提取完成")
            print(f"  提取的表格数量: {len(financial_data.get('extracted_tables', []))}")
            
            if financial_data.get('extracted_tables'):
                print("  财务表格信息:")
                for table_info in financial_data['extracted_tables'][:3]:
                    print(f"    页码 {table_info.get('page', 'N/A')}: {table_info.get('caption', 'N/A')[:50]}...")
        
        print("\n🎉 PDF处理测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ PDF处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chinese_document_processor():
    """测试中文文档处理器"""
    try:
        from src.data.chinese_document_processor import ChineseDocumentProcessor
        
        print("\n" + "="*60)
        print("🇨🇳 测试中文文档处理器")
        print("="*60)
        
        # 配置
        config = {
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'min_chunk_size': 100
        }
        
        # 初始化中文处理器
        processor = ChineseDocumentProcessor(config)
        
        # PDF文件路径
        pdf_path = "data/reports/600580_卧龙电驱2025-04-26_卧龙电驱2024年年度报告_2105.pdf"
        
        print(f"🔍 开始处理PDF: {pdf_path}")
        
        # 解析PDF
        print("\n📖 步骤1: 解析PDF文档...")
        documents = processor.parse_pdf(pdf_path)
        print(f"✅ 解析完成，共生成 {len(documents)} 个文档页面")
        
        # 显示前几个文档的信息
        print("\n📋 文档信息预览:")
        for i, doc in enumerate(documents[:3]):
            print(f"  页面 {doc.page_number}:")
            print(f"    内容长度: {len(doc.content)} 字符")
            print(f"    表格数量: {len(doc.tables)}")
            print(f"    内容预览: {doc.content[:100].replace(chr(10), ' ')}...")
            print()
        
        # 文档分块
        print("✂️  步骤2: 中文智能分块...")
        chunks = processor.chunk_documents(documents)
        print(f"✅ 分块完成，共生成 {len(chunks)} 个文档块")
        
        # 显示分块统计
        print("\n📊 分块统计:")
        chunk_lengths = [len(chunk.content) for chunk in chunks]
        print(f"  平均块长度: {sum(chunk_lengths) / len(chunk_lengths):.0f} 字符")
        print(f"  最短块长度: {min(chunk_lengths)} 字符")
        print(f"  最长块长度: {max(chunk_lengths)} 字符")
        
        # 显示前几个块的信息
        print("\n📝 块信息预览:")
        for i, chunk in enumerate(chunks[:5]):
            print(f"  块 {i+1} (ID: {chunk.chunk_id}):")
            print(f"    页码: {chunk.metadata.get('page_number', 'N/A')}")
            print(f"    长度: {len(chunk.content)} 字符")
            print(f"    分块方法: {chunk.metadata.get('chunking_method', 'N/A')}")
            print(f"    内容预览: {chunk.content[:80].replace(chr(10), ' ')}...")
            print()
        
        print("\n🎉 中文文档处理器测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 中文文档处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始PDF处理功能对比测试")
    print("="*60)
    
    # 测试当前系统
    print("📄 测试当前PDF处理系统")
    print("="*60)
    current_success = test_current_pdf_processing()
    
    # 测试中文处理器
    chinese_success = test_chinese_document_processor()
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    print(f"当前系统: {'✅ 成功' if current_success else '❌ 失败'}")
    print(f"中文处理器: {'✅ 成功' if chinese_success else '❌ 失败'}")
    
    if current_success and chinese_success:
        print("\n🎉 两个系统都运行成功，可以进行功能对比和集成!")
    elif current_success:
        print("\n⚠️  只有当前系统运行成功，中文处理器需要调试")
    elif chinese_success:
        print("\n⚠️  只有中文处理器运行成功，当前系统需要调试")
    else:
        print("\n❌ 两个系统都有问题，需要进一步调试")

if __name__ == "__main__":
    main()