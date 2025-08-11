"""
财务报告分块器测试
测试pdfplumber + unstructured混合处理方案
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from src.data.financial_report_chunker import FinancialReportChunker, create_financial_chunker
from src.data.models import Chunk


class TestFinancialReportChunker:
    """财务报告分块器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = {
            "snap_tolerance": 5,
            "strategy": "hi_res",
            "chunk_size": 512,
            "chunk_overlap": 50
        }
        self.chunker = FinancialReportChunker(self.config)
    
    def test_init(self):
        """测试初始化"""
        assert self.chunker.config == self.config
        assert self.chunker.table_settings["snap_tolerance"] == 5
        assert self.chunker.unstructured_config["strategy"] == "hi_res"
        assert self.chunker.unstructured_config["infer_table_structure"] is False
        assert self.chunker.chunk_size == 512
        assert self.chunker.chunk_overlap == 50
    
    def test_classify_table_type_financial(self):
        """测试财务表格分类"""
        # 创建包含财务关键词的DataFrame
        financial_data = {
            '项目': ['营业收入', '净利润', '资产总计'],
            '金额': ['1000万', '200万', '5000万']
        }
        df = pd.DataFrame(financial_data)
        
        table_type = self.chunker._classify_table_type(df)
        assert table_type == 'financial'
    
    def test_classify_table_type_summary(self):
        """测试摘要表格分类"""
        summary_data = {
            '摘要': ['公司概况', '主要业务'],
            '内容': ['科技公司', '软件开发']
        }
        df = pd.DataFrame(summary_data)
        
        table_type = self.chunker._classify_table_type(df)
        assert table_type == 'summary'
    
    def test_classify_table_type_other(self):
        """测试其他类型表格分类"""
        other_data = {
            '姓名': ['张三', '李四'],
            '部门': ['技术部', '市场部']
        }
        df = pd.DataFrame(other_data)
        
        table_type = self.chunker._classify_table_type(df)
        assert table_type == 'other'
    
    def test_split_text_into_chunks(self):
        """测试文本分块"""
        text = "这是第一句话。这是第二句话。" * 100  # 创建长文本
        
        chunks = self.chunker._split_text_into_chunks(text)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= self.chunker.chunk_size + 100 for chunk in chunks)  # 允许一些误差
        assert all(chunk.strip() for chunk in chunks)  # 确保没有空块
    
    def test_create_table_chunk(self):
        """测试创建表格块"""
        # 模拟表格信息
        table_info = {
            "page": 1,
            "table_index": 0,
            "dataframe": pd.DataFrame({
                '项目': ['营业收入', '净利润'],
                '金额': ['1000万', '200万']
            }),
            "table_type": "financial",
            "caption": "财务数据表",
            "row_count": 2,
            "col_count": 2
        }
        
        metadata = {
            "source_file": "test.pdf",
            "processing_method": "pdfplumber_unstructured_hybrid"
        }
        
        chunk = self.chunker._create_table_chunk(table_info, metadata)
        
        assert isinstance(chunk, Chunk)
        assert chunk.chunk_id == "table_1_0"
        assert chunk.metadata["chunk_type"] == "table"
        assert chunk.metadata["table_type"] == "financial"
        assert chunk.metadata["is_financial_data"] is True
        assert "营业收入" in chunk.content
        assert "净利润" in chunk.content
    
    def test_create_text_chunks(self):
        """测试创建文本块"""
        # 模拟unstructured元素
        mock_elements = []
        for i in range(3):
            element = Mock()
            element.text = f"这是第{i+1}段文本内容。" * 50
            mock_elements.append(element)
        
        metadata = {
            "source_file": "test.pdf",
            "processing_method": "pdfplumber_unstructured_hybrid"
        }
        
        chunks = self.chunker._create_text_chunks(mock_elements, metadata)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.metadata["chunk_type"] == "text" for chunk in chunks)
        assert all(chunk.metadata["is_financial_data"] is False for chunk in chunks)
    
    @patch('pdfplumber.open')
    def test_extract_tables_with_pdfplumber(self, mock_pdfplumber):
        """测试pdfplumber表格提取"""
        # 模拟pdfplumber返回
        mock_page = Mock()
        mock_page.page_number = 1
        mock_page.extract_tables.return_value = [
            [
                ['项目', '金额'],
                ['营业收入', '1000万'],
                ['净利润', '200万']
            ]
        ]
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            table_data = self.chunker._extract_tables_with_pdfplumber(tmp_path)
            
            assert len(table_data) == 1
            assert table_data[0]["page"] == 1
            assert table_data[0]["table_type"] == "financial"
            assert table_data[0]["row_count"] == 2
            assert table_data[0]["col_count"] == 2
        finally:
            os.unlink(tmp_path)
    
    @patch('src.data.financial_report_chunker.partition_pdf')
    def test_extract_text_with_unstructured(self, mock_partition):
        """测试unstructured文本提取"""
        # 模拟unstructured返回
        mock_elements = []
        for i in range(3):
            element = Mock()
            element.category = 'NarrativeText'
            element.text = f"这是第{i+1}段文本内容。"
            mock_elements.append(element)
        
        # 添加一个表格元素（应该被过滤）
        table_element = Mock()
        table_element.category = 'Table'
        table_element.text = "表格内容"
        mock_elements.append(table_element)
        
        mock_partition.return_value = mock_elements
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            elements = self.chunker._extract_text_with_unstructured(tmp_path)
            
            # 应该过滤掉表格元素
            assert len(elements) == 3
            assert all(hasattr(e, 'text') for e in elements)
            assert all(e.category != 'Table' for e in elements)
        finally:
            os.unlink(tmp_path)
    
    @patch('src.data.financial_report_chunker.partition_pdf')
    @patch('pdfplumber.open')
    def test_process_pdf_integration(self, mock_pdfplumber, mock_partition):
        """测试完整PDF处理流程"""
        # 模拟pdfplumber
        mock_page = Mock()
        mock_page.page_number = 1
        mock_page.extract_tables.return_value = [
            [
                ['项目', '金额'],
                ['营业收入', '1000万']
            ]
        ]
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # 模拟unstructured
        mock_element = Mock()
        mock_element.category = 'NarrativeText'
        mock_element.text = "这是文本内容。"
        mock_partition.return_value = [mock_element]
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = self.chunker.process_pdf(tmp_path)
            
            assert "tables" in result
            assert "text_blocks" in result
            assert "metadata" in result
            assert len(result["tables"]) == 1
            assert len(result["text_blocks"]) == 1
            assert result["metadata"]["processing_method"] == "pdfplumber_unstructured_hybrid"
        finally:
            os.unlink(tmp_path)
    
    def test_create_document_chunks_integration(self):
        """测试文档块创建集成"""
        # 模拟处理后的数据
        processed_data = {
            "tables": [
                {
                    "page": 1,
                    "table_index": 0,
                    "dataframe": pd.DataFrame({
                        '项目': ['营业收入'],
                        '金额': ['1000万']
                    }),
                    "table_type": "financial",
                    "caption": "财务表",
                    "row_count": 1,
                    "col_count": 2
                }
            ],
            "text_blocks": [
                Mock(text="这是文本内容。" * 20)
            ],
            "metadata": {
                "source_file": "test.pdf",
                "processing_method": "pdfplumber_unstructured_hybrid"
            }
        }
        
        chunks = self.chunker.create_document_chunks(processed_data)
        
        assert len(chunks) >= 2  # 至少一个表格块和一个文本块
        
        # 检查表格块
        table_chunks = [c for c in chunks if c.metadata["chunk_type"] == "table"]
        assert len(table_chunks) == 1
        assert table_chunks[0].metadata["is_financial_data"] is True
        
        # 检查文本块
        text_chunks = [c for c in chunks if c.metadata["chunk_type"] == "text"]
        assert len(text_chunks) >= 1
        assert all(c.metadata["is_financial_data"] is False for c in text_chunks)
    
    def test_file_not_found_error(self):
        """测试文件不存在错误"""
        with pytest.raises(FileNotFoundError):
            self.chunker.process_pdf("nonexistent.pdf")


class TestFactoryFunction:
    """测试工厂函数"""
    
    def test_create_financial_chunker_default(self):
        """测试默认配置创建"""
        chunker = create_financial_chunker()
        
        assert isinstance(chunker, FinancialReportChunker)
        assert chunker.config["snap_tolerance"] == 5
        assert chunker.config["strategy"] == "hi_res"
        assert chunker.config["chunk_size"] == 512
        assert chunker.config["chunk_overlap"] == 50
    
    def test_create_financial_chunker_custom(self):
        """测试自定义配置创建"""
        custom_config = {
            "snap_tolerance": 10,
            "chunk_size": 1024
        }
        
        chunker = create_financial_chunker(custom_config)
        
        assert chunker.config["snap_tolerance"] == 10
        assert chunker.config["chunk_size"] == 1024
        assert chunker.config["strategy"] == "hi_res"  # 默认值


if __name__ == "__main__":
    pytest.main([__file__])