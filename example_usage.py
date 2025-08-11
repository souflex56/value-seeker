#!/usr/bin/env python3
"""
中文PDF分块功能使用示例
展示如何使用新的增强文档处理器
"""

import sys
sys.path.append('.')

def main():
    """主函数 - 展示增强文档处理器的使用"""
    
    # 方式1: 使用工厂函数创建（推荐）
    from src.data import create_enhanced_processor
    
    config = {
        'chunk_size': 1000,
        'chunk_overlap': 200,
        'min_chunk_size': 100,
        'enable_chinese_optimization': True,
        'chinese_detection_threshold': 0.3,
        'preserve_sentences': True,
        'preserve_financial_terms': True,
        'use_semantic_split': True
    }
    
    processor = create_enhanced_processor(config)
    
    # 方式2: 直接创建类实例
    # from src.data import EnhancedDocumentProcessor
    # processor = EnhancedDocumentProcessor(config)
    
    # 处理PDF文档
    pdf_path = "data/reports/600580_卧龙电驱2025-04-26_卧龙电驱2024年年度报告_2105.pdf"
    
    try:
        print("🚀 开始处理PDF文档...")
        
        # 解析PDF
        documents = processor.parse_pdf(pdf_path)
        print(f"✅ 解析完成，共 {len(documents)} 页")
        
        # 智能分块
        chunks = processor.chunk_documents(documents[:5])  # 只处理前5页作为示例
        print(f"✅ 分块完成，共 {len(chunks)} 个块")
        
        # 获取处理统计
        stats = processor.get_processing_stats(chunks)
        print(f"\n📊 处理统计:")
        print(f"  平均块长度: {stats['avg_chunk_length']:.0f} 字符")
        print(f"  财务相关块: {stats['financial_chunks']}")
        print(f"  分块方法: {stats['chunking_methods']}")
        print(f"  语言分布: {stats['languages']}")
        
        # 显示示例块
        print(f"\n📝 示例块:")
        for i, chunk in enumerate(chunks[:2]):
            print(f"  块 {i+1}:")
            print(f"    ID: {chunk.chunk_id}")
            print(f"    长度: {len(chunk.content)} 字符")
            print(f"    方法: {chunk.metadata.get('chunking_method', 'N/A')}")
            print(f"    语言: {chunk.metadata.get('language', 'N/A')}")
            print(f"    财务术语: {chunk.metadata.get('financial_terms_count', 0)}")
            print(f"    内容: {chunk.content[:100]}...")
            print()
        
        print("🎉 处理完成！")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()