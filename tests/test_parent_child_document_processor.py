"""
父子文档处理器单元测试

测试父子分块架构和高保真表格提取集成功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.data.parent_child_document_processor import (
    ParentChildDocumentProcessor, 
    create_parent_child_processor
)
from src.data.models import ParentChunk, ChildChunk, TableChunk, Document, Table
from src.core.exceptions import DocumentProcessingError


class TestParentChildDocumentProcessor:
    """父子文档处理器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = {
            'parent_chunk_size': 4000,
            'child_chunk_size': 1000,
            'child_chunk_overlap': 200,
            'table_extraction': {
                'min_table_rows': 2,
                'min_table_cols': 2
            }
        }
    
    @patch('src.data.parent_child_document_processor.DocumentProcessor')
    @patch('src.data.parent_child_document_processor.create_table_extractor')
    def test_init_success(self, mock_create_extractor, mock_doc_processor):
        """测试成功初始化"""
        processor = ParentChildDocumentProcessor(self.config)
        
        assert processor.parent_chunk_size == 4000
        assert processor.child_chunk_size == 1000
        assert processor.child_chunk_overlap == 200
        
        # 验证子组件初始化
        mock_doc_processor.assert_called_once()
        mock_create_extractor.assert_called_once_with({
            'min_table_rows': 2,
            'min_table_cols': 2
        })
    
    @patch('src.data.parent_child_document_processor.DocumentProcessor')
    @patch('src.data.parent_child_document_processor.create_table_extractor')
    def test_init_with_default_config(self, mock_create_extractor, mock_doc_processor):
        """测试使用默认配置初始化"""
        processor = ParentChildDocumentProcessor()
        
        assert processor.parent_chunk_size == 4000
        assert processor.child_chunk_size == 1000
        assert processor.child_chunk_overlap == 200
    
    @patch('src.data.parent_child_document_processor.Path')
    def test_process_pdf_file_not_exists(self, mock_path):
        """测试文件不存在时的处理"""
        mock_path.return_value.exists.return_value = False
        
        processor = ParentChildDocumentProcessor(self.config)
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            processor.process_pdf("nonexistent.pdf")
        
        assert "PDF文件不存在" in str(exc_info.value)
    
    @patch('src.data.parent_child_document_processor.Path')
    @patch('src.data.parent_child_document_processor.DocumentProcessor')
    @patch('src.data.parent_child_document_processor.create_table_extractor')
    def test_process_pdf_success(self, mock_create_extractor, mock_doc_processor_class, mock_path):
        """测试成功处理PDF"""
        # 模拟文件存在
        mock_path.return_value.exists.return_value = True
        
        # 模拟文档处理器
        mock_doc_processor = Mock()
        mock_doc_processor_class.return_value = mock_doc_processor
        
        # 模拟文档数据
        mock_document = Mock()
        mock_document.page_number = 1
        mock_document.content = "这是测试文档内容。" * 100
        mock_document.tables = []
        mock_document.metadata = {
            'document_id': 'test_doc_1',
            'total_pages': 1,
            'processed_at': '2024-01-01T00:00:00'
        }
        mock_doc_processor.parse_pdf.return_value = [mock_document]
        
        # 模拟表格提取器
        mock_table_extractor = Mock()
        mock_create_extractor.return_value = mock_table_extractor
        
        # 模拟表格数据
        mock_table_chunk = TableChunk(
            table_id="table_1_0",
            markdown_content="| 列1 | 列2 |\n|---|---|\n| 数据1 | 数据2 |",
            page_number=1,
            boundary_box={'x0': 0, 'y0': 0, 'x1': 100, 'y1': 100},
            table_type='financial'
        )
        mock_table_extractor.extract_tables_from_pdf.return_value = [mock_table_chunk]
        
        processor = ParentChildDocumentProcessor(self.config)
        parent_chunks, child_chunks = processor.process_pdf("test.pdf")
        
        # 验证结果
        assert len(parent_chunks) == 1
        assert len(child_chunks) >= 1  # 至少有文本分块
        
        # 验证父分块
        parent_chunk = parent_chunks[0]
        assert isinstance(parent_chunk, ParentChunk)
        assert parent_chunk.page_numbers == [1]
        assert parent_chunk.chunk_type == "page"
        
        # 验证子分块包含表格分块
        table_chunks = [c for c in child_chunks if c.chunk_type == "table"]
        assert len(table_chunks) == 1
        assert table_chunks[0].content == mock_table_chunk.markdown_content
    
    def test_create_parent_chunks(self):
        """测试创建父分块"""
        processor = ParentChildDocumentProcessor(self.config)
        
        # 创建模拟文档
        mock_document = Mock()
        mock_document.page_number = 1
        mock_document.content = "测试文档内容"
        mock_document.tables = []
        mock_document.metadata = {
            'document_id': 'test_doc_1',
            'total_pages': 2,
            'processed_at': '2024-01-01T00:00:00',
            'extraction_method': 'unstructured'
        }
        
        documents = [mock_document]
        pdf_path = "test.pdf"
        
        parent_chunks = processor._create_parent_chunks(documents, pdf_path)
        
        assert len(parent_chunks) == 1
        parent_chunk = parent_chunks[0]
        
        assert isinstance(parent_chunk, ParentChunk)
        assert parent_chunk.content == "测试文档内容"
        assert parent_chunk.page_numbers == [1]
        assert parent_chunk.chunk_type == "page"
        assert parent_chunk.metadata['source_file'] == "test.pdf"
        assert parent_chunk.metadata['total_pages'] == 2
    
    def test_create_text_child_chunks(self):
        """测试创建文本子分块"""
        processor = ParentChildDocumentProcessor(self.config)
        
        # 创建父分块
        parent_chunk = ParentChunk(
            parent_id="parent_1",
            content="这是一个很长的测试文档内容。" * 50,  # 足够长以产生多个子分块
            metadata={
                'source_file': 'test.pdf',
                'source_path': '/path/to/test.pdf',
                'document_id': 'doc_1'
            },
            page_numbers=[1],
            chunk_type="page"
        )
        
        child_chunks = processor._create_text_child_chunks(parent_chunk)
        
        assert len(child_chunks) > 0
        
        for child_chunk in child_chunks:
            assert isinstance(child_chunk, ChildChunk)
            assert child_chunk.parent_id == "parent_1"
            assert child_chunk.chunk_type == "text"
            assert child_chunk.page_number == 1
            assert len(child_chunk.content) >= 50  # 最小长度检查
    
    def test_create_text_child_chunks_empty_content(self):
        """测试空内容的文本子分块创建"""
        processor = ParentChildDocumentProcessor(self.config)
        
        parent_chunk = ParentChunk(
            parent_id="parent_1",
            content="",
            metadata={},
            page_numbers=[1],
            chunk_type="page"
        )
        
        child_chunks = processor._create_text_child_chunks(parent_chunk)
        
        assert len(child_chunks) == 0
    
    def test_create_table_child_chunks(self):
        """测试创建表格子分块"""
        processor = ParentChildDocumentProcessor(self.config)
        
        # 创建父分块
        parent_chunk = ParentChunk(
            parent_id="parent_1",
            content="页面内容",
            metadata={
                'source_file': 'test.pdf',
                'source_path': '/path/to/test.pdf',
                'document_id': 'doc_1'
            },
            page_numbers=[1],
            chunk_type="page"
        )
        
        # 创建表格分块
        table_chunks = [
            TableChunk(
                table_id="table_1_0",
                markdown_content="| 列1 | 列2 |\n|---|---|\n| 数据1 | 数据2 |",
                page_number=1,
                boundary_box={'x0': 0, 'y0': 0, 'x1': 100, 'y1': 100},
                table_type='financial'
            ),
            TableChunk(
                table_id="table_1_1",
                markdown_content="| 列A | 列B |\n|---|---|\n| 值A | 值B |",
                page_number=1,
                boundary_box={'x0': 0, 'y0': 100, 'x1': 100, 'y1': 200},
                table_type='other'
            )
        ]
        
        child_chunks = processor._create_table_child_chunks(parent_chunk, table_chunks)
        
        assert len(child_chunks) == 2
        
        for i, child_chunk in enumerate(child_chunks):
            assert isinstance(child_chunk, ChildChunk)
            assert child_chunk.parent_id == "parent_1"
            assert child_chunk.chunk_type == "table"
            assert child_chunk.page_number == 1
            assert child_chunk.metadata['table_id'] == table_chunks[i].table_id
            assert child_chunk.metadata['table_type'] == table_chunks[i].table_type
            assert child_chunk.content == table_chunks[i].markdown_content
    
    def test_split_text_into_segments_short_text(self):
        """测试短文本分割"""
        processor = ParentChildDocumentProcessor(self.config)
        
        text = "这是一个短文本。"
        segments = processor._split_text_into_segments(text, 1000, 200)
        
        assert len(segments) == 1
        assert segments[0] == text
    
    def test_split_text_into_segments_long_text(self):
        """测试长文本分割"""
        processor = ParentChildDocumentProcessor(self.config)
        
        # 创建足够长的文本
        text = "这是第一句话。这是第二句话。" * 100
        segments = processor._split_text_into_segments(text, 500, 100)
        
        assert len(segments) > 1
        
        # 检查重叠
        for i in range(len(segments) - 1):
            assert len(segments[i]) > 0
            assert len(segments[i+1]) > 0
    
    def test_split_text_into_segments_sentence_boundary(self):
        """测试在句子边界处分割"""
        processor = ParentChildDocumentProcessor(self.config)
        
        text = "第一句话很长很长很长。第二句话也很长很长很长。第三句话同样很长很长很长。"
        segments = processor._split_text_into_segments(text, 50, 10)
        
        # 应该在句号处分割
        for segment in segments:
            if len(segment) < len(text):  # 不是最后一个片段
                assert segment.endswith('。') or '。' in segment
    
    def test_get_processing_stats(self):
        """测试获取处理统计信息"""
        processor = ParentChildDocumentProcessor(self.config)
        
        # 创建测试数据
        parent_chunks = [
            ParentChunk(
                parent_id="parent_1",
                content="父分块内容1" * 100,
                metadata={},
                page_numbers=[1],
                chunk_type="page"
            ),
            ParentChunk(
                parent_id="parent_2",
                content="父分块内容2" * 150,
                metadata={},
                page_numbers=[2],
                chunk_type="page"
            )
        ]
        
        child_chunks = [
            ChildChunk(
                child_id="child_1",
                parent_id="parent_1",
                content="文本子分块内容",
                metadata={},
                chunk_type="text",
                page_number=1
            ),
            ChildChunk(
                child_id="child_2",
                parent_id="parent_1",
                content="| 列1 | 列2 |\n|---|---|\n| 数据1 | 数据2 |",
                metadata={'table_type': 'financial'},
                chunk_type="table",
                page_number=1
            ),
            ChildChunk(
                child_id="child_3",
                parent_id="parent_2",
                content="另一个文本子分块",
                metadata={},
                chunk_type="text",
                page_number=2
            )
        ]
        
        stats = processor.get_processing_stats(parent_chunks, child_chunks)
        
        assert stats['total_parent_chunks'] == 2
        assert stats['total_child_chunks'] == 3
        assert stats['child_chunk_types']['text'] == 2
        assert stats['child_chunk_types']['table'] == 1
        assert stats['table_types']['financial'] == 1
        assert stats['pages_processed'] == 2
        assert stats['compression_ratio'] == 1.5  # 3 child / 2 parent
        assert stats['avg_parent_length'] > 0
        assert stats['avg_child_length'] > 0
    
    def test_get_processing_stats_empty(self):
        """测试空数据的统计信息"""
        processor = ParentChildDocumentProcessor(self.config)
        
        stats = processor.get_processing_stats([], [])
        
        assert stats['total_parent_chunks'] == 0
        assert stats['total_child_chunks'] == 0
        assert stats['child_chunk_types'] == {}
        assert stats['table_types'] == {}
        assert stats['pages_processed'] == 0
        assert stats['compression_ratio'] == 0
        assert stats['avg_parent_length'] == 0
        assert stats['avg_child_length'] == 0


class TestCreateParentChildProcessor:
    """测试父子文档处理器工厂函数"""
    
    @patch('src.data.parent_child_document_processor.DocumentProcessor')
    @patch('src.data.parent_child_document_processor.create_table_extractor')
    def test_create_with_default_config(self, mock_create_extractor, mock_doc_processor):
        """测试使用默认配置创建"""
        processor = create_parent_child_processor()
        
        assert processor.parent_chunk_size == 4000
        assert processor.child_chunk_size == 1000
        assert processor.child_chunk_overlap == 200
    
    @patch('src.data.parent_child_document_processor.DocumentProcessor')
    @patch('src.data.parent_child_document_processor.create_table_extractor')
    def test_create_with_custom_config(self, mock_create_extractor, mock_doc_processor):
        """测试使用自定义配置创建"""
        config = {
            'parent_chunk_size': 5000,
            'child_chunk_size': 1200,
            'child_chunk_overlap': 300
        }
        
        processor = create_parent_child_processor(config)
        
        assert processor.parent_chunk_size == 5000
        assert processor.child_chunk_size == 1200
        assert processor.child_chunk_overlap == 300


if __name__ == '__main__':
    pytest.main([__file__])