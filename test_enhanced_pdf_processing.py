#!/usr/bin/env python3
"""
测试增强的PDF处理功能
对比原有系统和中文优化系统的效果
"""

import sys
import os
from pathlib import Path
sys.path.append('.')

def test_enhanced_pdf_processing():
    """测试增强的PDF处理功能"""
    try:
        from src.data.enhanced_document_processor import EnhancedDocumentProcessor
        
        print("🇨🇳 测试增强的PDF处理系统（中文优化）")
        print("="*60)
        
        # 配置
        config = {
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'min_chunk_size': 100,
            'pdf_strategy': 'fast',
            'use_high_res': False,
            'enable_chinese_optimization': True,
            'chinese_detection_threshold': 0.3,
            'preserve_sentences': True,
            'preserve_financial_terms': True,
            'use_semantic_split': True
        }
        
        # 初始化增强处理器
        processor = EnhancedDocumentProcessor(config)
        
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
        
        # 显示前几个文档的语言检测结果
        print("\n🔍 语言检测结果:")
        for i, doc in enumerate(documents[:5]):
            language = processor._detect_language(doc.content)
            print(f"  页面 {doc.page_number}: {language} (内容长度: {len(doc.content)} 字符)")
        
        # 文档分块（使用增强功能）
        print("\n✂️  步骤2: 增强文档分块...")
        chunks = processor.chunk_documents(documents)
        print(f"✅ 分块完成，共生成 {len(chunks)} 个文档块")
        
        # 获取处理统计
        stats = processor.get_processing_stats(chunks)
        print("\n📊 处理统计:")
        print(f"  总块数: {stats['total_chunks']}")
        print(f"  平均块长度: {stats['avg_chunk_length']:.0f} 字符")
        print(f"  财务相关块: {stats['financial_chunks']}")
        print(f"  分块方法分布: {stats['chunking_methods']}")
        print(f"  语言分布: {stats['languages']}")
        
        # 显示前几个块的详细信息
        print("\n📝 块信息预览:")
        for i, chunk in enumerate(chunks[:5]):
            print(f"  块 {i+1} (ID: {chunk.chunk_id}):")
            print(f"    页码: {chunk.metadata.get('page_number', 'N/A')}")
            print(f"    长度: {len(chunk.content)} 字符")
            print(f"    分块方法: {chunk.metadata.get('chunking_method', 'N/A')}")
            print(f"    语言: {chunk.metadata.get('language', 'N/A')}")
            print(f"    财务术语数: {chunk.metadata.get('financial_terms_count', 0)}")
            print(f"    数字数量: {chunk.metadata.get('numbers_count', 0)}")
            print(f"    内容预览: {chunk.content[:80].replace(chr(10), ' ')}...")
            print()
        
        # 分块方法对比（选择一个有代表性的文档）
        if documents:
            print("🔄 步骤3: 分块方法对比...")
            comparison = processor.compare_chunking_methods(documents[10])  # 选择第11页
            
            print("📈 分块方法对比结果:")
            for method, result in comparison.items():
                print(f"  {method}:")
                print(f"    块数量: {result['chunk_count']}")
                print(f"    平均长度: {result['avg_length']:.0f} 字符")
                if 'financial_chunks' in result:
                    print(f"    财务相关块: {result['financial_chunks']}")
                print()
        
        print("🎉 增强PDF处理测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 增强PDF处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chinese_text_splitter():
    """单独测试中文文本分割器"""
    try:
        from src.data.chinese_text_splitter import create_chinese_text_splitter
        
        print("\n" + "="*60)
        print("🔤 测试中文文本分割器")
        print("="*60)
        
        # 测试文本（模拟财务报告内容）
        test_text = """
        卧龙电气驱动集团股份有限公司2024年年度报告显示，公司营业收入达到150.5亿元，同比增长12.3%。
        净利润为8.2亿元，较上年同期增长15.7%。毛利率保持在23.4%的较高水平。
        
        公司资产负债率为45.2%，流动比率为1.85，速动比率为1.42，财务状况良好。
        每股收益为1.23元，每股净资产为8.95元，净资产收益率达到13.7%。
        
        在现金流方面，经营活动现金流净额为12.8亿元，投资活动现金流净额为-5.6亿元，
        筹资活动现金流净额为-3.2亿元，自由现金流为7.2亿元。
        
        展望未来，公司将继续专注于电机驱动技术的创新发展，提升产品竞争力，
        扩大市场份额，为股东创造更大价值。
        """
        
        # 创建中文分割器
        config = {
            'chunk_size': 200,  # 较小的块用于测试
            'chunk_overlap': 50,
            'min_chunk_size': 50,
            'preserve_sentences': True,
            'preserve_financial_terms': True,
            'use_semantic_split': True
        }
        
        splitter = create_chinese_text_splitter(config)
        
        # 分割文本
        chunks = splitter.split_text(test_text)
        
        print(f"✅ 分割完成，共生成 {len(chunks)} 个块")
        
        # 显示分割结果
        print("\n📝 分割结果:")
        for i, chunk in enumerate(chunks):
            metadata = splitter.get_chunk_metadata(chunk, i)
            print(f"  块 {i+1}:")
            print(f"    长度: {len(chunk)} 字符")
            print(f"    财务术语: {metadata['financial_terms_count']}")
            print(f"    数字: {metadata['numbers_count']}")
            print(f"    内容: {chunk.strip()}")
            print()
        
        print("🎉 中文文本分割器测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 中文文本分割器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_original():
    """与原有系统对比"""
    try:
        from src.data.document_processor import DocumentProcessor
        from src.data.enhanced_document_processor import EnhancedDocumentProcessor
        
        print("\n" + "="*60)
        print("⚖️  原有系统 vs 增强系统对比")
        print("="*60)
        
        pdf_path = "data/reports/600580_卧龙电驱2025-04-26_卧龙电驱2024年年度报告_2105.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF文件不存在: {pdf_path}")
            return False
        
        # 配置
        config = {
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'min_chunk_size': 100,
            'pdf_strategy': 'fast',
        }
        
        # 原有系统
        print("📄 测试原有系统...")
        original_processor = DocumentProcessor(config)
        original_docs = original_processor.parse_pdf(pdf_path)
        original_chunks = original_processor.chunk_documents(original_docs[:10])  # 只测试前10页
        
        # 增强系统
        print("🚀 测试增强系统...")
        enhanced_config = {**config, 'enable_chinese_optimization': True}
        enhanced_processor = EnhancedDocumentProcessor(enhanced_config)
        enhanced_docs = enhanced_processor.parse_pdf(pdf_path)
        enhanced_chunks = enhanced_processor.chunk_documents(enhanced_docs[:10])  # 只测试前10页
        
        # 对比结果
        print("\n📊 对比结果:")
        print(f"原有系统:")
        print(f"  块数量: {len(original_chunks)}")
        print(f"  平均长度: {sum(len(c.content) for c in original_chunks) / len(original_chunks):.0f} 字符")
        print(f"  分块方法: {set(c.metadata.get('chunking_method', 'unknown') for c in original_chunks)}")
        
        print(f"\n增强系统:")
        print(f"  块数量: {len(enhanced_chunks)}")
        print(f"  平均长度: {sum(len(c.content) for c in enhanced_chunks) / len(enhanced_chunks):.0f} 字符")
        print(f"  分块方法: {set(c.metadata.get('chunking_method', 'unknown') for c in enhanced_chunks)}")
        
        # 获取增强系统的统计
        stats = enhanced_processor.get_processing_stats(enhanced_chunks)
        print(f"  财务相关块: {stats['financial_chunks']}")
        print(f"  语言分布: {stats['languages']}")
        
        print("\n🎉 系统对比完成!")
        return True
        
    except Exception as e:
        print(f"❌ 系统对比失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始增强PDF处理功能测试")
    print("="*60)
    
    # 测试中文文本分割器
    chinese_splitter_success = test_chinese_text_splitter()
    
    # 测试增强系统
    enhanced_success = test_enhanced_pdf_processing()
    
    # 与原有系统对比
    comparison_success = compare_with_original()
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    print(f"中文文本分割器: {'✅ 成功' if chinese_splitter_success else '❌ 失败'}")
    print(f"增强PDF处理系统: {'✅ 成功' if enhanced_success else '❌ 失败'}")
    print(f"系统对比: {'✅ 成功' if comparison_success else '❌ 失败'}")
    
    if all([chinese_splitter_success, enhanced_success, comparison_success]):
        print("\n🎉 所有测试通过！增强系统可以投入使用。")
        print("\n💡 集成建议:")
        print("1. 将 EnhancedDocumentProcessor 替换现有的 DocumentProcessor")
        print("2. 在配置中启用 enable_chinese_optimization")
        print("3. 根据需要调整中文检测阈值和分块参数")
        print("4. 监控分块效果，必要时进一步优化")
    else:
        print("\n⚠️  部分测试失败，需要进一步调试")

if __name__ == "__main__":
    main()