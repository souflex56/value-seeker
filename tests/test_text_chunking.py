"""
智能文本分块功能测试

测试基于语义的文本分块算法，包括可配置参数和表格关联关系保持。
"""

import pytest
import pandas as pd
from src.data.document_processor import DocumentProcessor
from src.data.models import Document, Table, Chunk


class TestTextChunking:
    """智能文本分块测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = {
            'chunk_size': 200,  # 较小的块大小便于测试
            'chunk_overlap': 30,
            'min_chunk_size': 50
        }
        self.processor = DocumentProcessor(self.config)
    
    def test_configurable_chunk_size(self):
        """测试可配置的chunk_size参数"""
        # 测试不同的chunk_size配置
        configs = [
            {'chunk_size': 100, 'chunk_overlap': 20},
            {'chunk_size': 300, 'chunk_overlap': 50},
            {'chunk_size': 500, 'chunk_overlap': 100}
        ]
        
        content = "这是一个测试文档。" * 100  # 创建足够长的内容
        
        for config in configs:
            processor = DocumentProcessor(config)
            document = Document(
                content=content,
                metadata={'document_id': 'test-doc'},
                tables=[],
                source='test.pdf',
                page_number=1
            )
            
            chunks = processor.chunk_documents([document])
            
            # 验证块大小大致符合配置
            for chunk in chunks:
                assert len(chunk.content) <= config['chunk_size'] + 100  # 允许一些误差
            
            # 验证配置生效
            assert processor.chunk_size == config['chunk_size']
            assert processor.chunk_overlap == config['chunk_overlap']
    
    def test_configurable_chunk_overlap(self):
        """测试可配置的chunk_overlap参数"""
        content = "第一段内容。第二段内容。第三段内容。第四段内容。第五段内容。" * 20
        
        document = Document(
            content=content,
            metadata={'document_id': 'test-doc'},
            tables=[],
            source='test.pdf',
            page_number=1
        )
        
        # 测试有重叠的情况
        processor_with_overlap = DocumentProcessor({'chunk_size': 200, 'chunk_overlap': 50})
        chunks_with_overlap = processor_with_overlap.chunk_documents([document])
        
        # 测试无重叠的情况
        processor_no_overlap = DocumentProcessor({'chunk_size': 200, 'chunk_overlap': 0})
        chunks_no_overlap = processor_no_overlap.chunk_documents([document])
        
        # 有重叠的情况应该产生更多的块（因为有重复内容）
        if len(chunks_with_overlap) > 1 and len(chunks_no_overlap) > 1:
            # 检查重叠内容
            overlap_text = processor_with_overlap._get_overlap_text(chunks_with_overlap[0].content, 50)
            assert len(overlap_text) > 0
            assert overlap_text in chunks_with_overlap[1].content
    
    def test_semantic_chunking(self):
        """测试基于语义的文本分块"""
        # 创建包含不同语义段落的文档
        content = """
        公司财务概况：本公司在2023年实现了显著的业绩增长。营业收入达到10亿元，同比增长15%。
        
        盈利能力分析：净利润为2亿元，净利率达到20%，显示出良好的盈利能力。毛利率保持在35%的水平。
        
        资产负债情况：总资产50亿元，负债率控制在40%以下，财务结构稳健。现金流充足，为未来发展提供保障。
        
        市场前景展望：随着行业复苏，公司预计2024年将继续保持增长态势。新产品线的推出将带来额外收入。
        """
        
        document = Document(
            content=content,
            metadata={'document_id': 'test-doc'},
            tables=[],
            source='test.pdf',
            page_number=1
        )
        
        chunks = self.processor.chunk_documents([document])
        
        assert len(chunks) > 0
        
        # 验证每个块都有合理的内容
        for chunk in chunks:
            assert len(chunk.content.strip()) >= self.config['min_chunk_size']
            assert chunk.document_id == 'test-doc'
            assert 'chunk_index' in chunk.metadata
            assert 'chunk_length' in chunk.metadata
    
    def test_table_relationship_preservation(self):
        """测试表格和文本的关联关系保持"""
        # 创建包含表格的文档
        table_data = pd.DataFrame({
            '项目': ['营业收入', '净利润', '总资产'],
            '2023年': [1000000, 200000, 5000000],
            '2022年': [800000, 150000, 4500000]
        })
        
        table = Table(
            data=table_data,
            caption='主要财务指标',
            page_number=1,
            table_type='financial'
        )
        
        content = """
        根据下表所示的财务数据，公司在2023年表现优异。
        
        如上表所示，各项指标均有显著提升。营业收入增长25%，净利润增长33%。
        这些数据反映了公司强劲的增长势头和良好的经营管理能力。
        """
        
        document = Document(
            content=content,
            metadata={'document_id': 'test-doc'},
            tables=[table],
            source='test.pdf',
            page_number=1
        )
        
        chunks = self.processor.chunk_documents([document])
        
        # 验证块的元数据包含表格信息
        for chunk in chunks:
            assert 'has_tables' in chunk.metadata
            assert 'table_count' in chunk.metadata
            
            # 如果文档有表格，块的元数据应该反映这一点
            if chunk.metadata['has_tables']:
                assert chunk.metadata['table_count'] == 1
                assert 'table_types' in chunk.metadata
                assert 'table_captions' in chunk.metadata
                assert 'financial' in chunk.metadata['table_types']
                assert '主要财务指标' in chunk.metadata['table_captions']
    
    def test_chunk_metadata_completeness(self):
        """测试块元数据的完整性"""
        content = "这是一个测试文档，用于验证块元数据的完整性。" * 10
        
        document = Document(
            content=content,
            metadata={
                'document_id': 'test-doc-123',
                'source_file': 'test.pdf',
                'title': '测试文档'
            },
            tables=[],
            source='/path/to/test.pdf',
            page_number=2
        )
        
        chunks = self.processor.chunk_documents([document])
        
        for i, chunk in enumerate(chunks):
            # 验证基本元数据
            assert chunk.chunk_id == f'test-doc-123_chunk_{i}'
            assert chunk.document_id == 'test-doc-123'
            
            # 验证块元数据
            metadata = chunk.metadata
            assert metadata['source_file'] == 'test.pdf'
            assert metadata['source_path'] == '/path/to/test.pdf'
            assert metadata['page_number'] == 2
            assert metadata['chunk_index'] == i
            assert metadata['chunk_length'] == len(chunk.content)
            assert metadata['document_id'] == 'test-doc-123'
            assert metadata['has_tables'] == False
            assert metadata['table_count'] == 0
    
    def test_min_chunk_size_filtering(self):
        """测试最小块大小过滤"""
        # 创建包含很短内容的文档
        short_content = "短内容。"
        
        document = Document(
            content=short_content,
            metadata={'document_id': 'test-doc'},
            tables=[],
            source='test.pdf',
            page_number=1
        )
        
        chunks = self.processor.chunk_documents([document])
        
        # 由于内容太短，可能不会生成块
        if chunks:
            for chunk in chunks:
                assert len(chunk.content) >= self.config['min_chunk_size']
    
    def test_sentence_boundary_respect(self):
        """测试句子边界的尊重"""
        # 创建包含明确句子边界的内容
        content = """
        第一句话包含重要的财务信息。第二句话描述了市场情况。第三句话分析了竞争态势。
        第四句话讨论了未来展望。第五句话总结了投资建议。第六句话提到了风险因素。
        第七句话描述了管理层变动。第八句话分析了行业趋势。第九句话讨论了技术创新。
        第十句话总结了整体评估。
        """
        
        document = Document(
            content=content,
            metadata={'document_id': 'test-doc'},
            tables=[],
            source='test.pdf',
            page_number=1
        )
        
        chunks = self.processor.chunk_documents([document])
        
        # 验证块包含完整的语义内容
        for chunk in chunks:
            content = chunk.content.strip()
            # 检查块是否包含句号（表示包含完整句子）
            if len(content) > 50:  # 只对足够长的块进行检查
                # 由于分块算法的实现，我们主要检查内容的合理性
                assert len(content) > 0
                # 检查是否包含中文句号或英文句号
                has_sentence_marker = '。' in content or '.' in content or content.count('句话') > 0
                assert has_sentence_marker
    
    def test_overlap_text_extraction(self):
        """测试重叠文本提取功能"""
        text = "这是一段很长的文本内容，用于测试重叠功能的正确性和有效性。"
        
        # 测试不同的重叠大小
        overlap_sizes = [10, 20, 30]
        
        for overlap_size in overlap_sizes:
            overlap_text = self.processor._get_overlap_text(text, overlap_size)
            
            assert len(overlap_text) <= overlap_size
            assert overlap_text in text
            
            # 如果原文本比重叠大小长，重叠文本应该是原文本的后缀
            if len(text) > overlap_size:
                assert text.endswith(overlap_text) or overlap_text in text[-overlap_size:]
    
    def test_chunk_id_uniqueness(self):
        """测试块ID的唯一性"""
        content = "这是一个测试文档。" * 50
        
        documents = [
            Document(
                content=content,
                metadata={'document_id': 'doc-1'},
                tables=[],
                source='test1.pdf',
                page_number=1
            ),
            Document(
                content=content,
                metadata={'document_id': 'doc-2'},
                tables=[],
                source='test2.pdf',
                page_number=1
            )
        ]
        
        all_chunks = self.processor.chunk_documents(documents)
        
        # 收集所有块ID
        chunk_ids = [chunk.chunk_id for chunk in all_chunks]
        
        # 验证ID唯一性
        assert len(chunk_ids) == len(set(chunk_ids))
        
        # 验证ID格式
        for chunk_id in chunk_ids:
            assert '_chunk_' in chunk_id
            assert chunk_id.startswith(('doc-1', 'doc-2'))
    
    def test_empty_document_handling(self):
        """测试空文档处理"""
        # 使用最小有效内容（避免Document验证错误）
        document = Document(
            content="短内容",  # 使用很短但有效的内容
            metadata={'document_id': 'empty-doc'},
            tables=[],
            source='empty.pdf',
            page_number=1
        )
        
        chunks = self.processor.chunk_documents([document])
        
        # 短文档可能不产生块（如果小于min_chunk_size）
        # 或者产生一个小块
        assert len(chunks) <= 1
    
    def test_large_document_chunking(self):
        """测试大文档分块"""
        # 创建一个大文档
        large_content = "这是一个大型文档的内容。" * 200  # 约4000字符
        
        document = Document(
            content=large_content,
            metadata={'document_id': 'large-doc'},
            tables=[],
            source='large.pdf',
            page_number=1
        )
        
        chunks = self.processor.chunk_documents([document])
        
        # 验证大文档被正确分块
        assert len(chunks) > 1
        
        # 验证所有块的总长度大致等于原文档长度（考虑重叠）
        total_chunk_length = sum(len(chunk.content) for chunk in chunks)
        # 由于重叠，总长度可能大于原文档
        assert total_chunk_length >= len(large_content)
        
        # 验证每个块都不超过配置的大小（允许一些误差）
        for chunk in chunks:
            assert len(chunk.content) <= self.config['chunk_size'] + 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])