"""
表格提取器单元测试

测试高保真表格提取功能的各个组件。
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.data.table_extractor import TableExtractor, create_table_extractor
from src.data.models import TableChunk
from src.core.exceptions import DocumentProcessingError


class TestTableExtractor:
    """表格提取器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.config = {
            'min_table_rows': 2,
            'min_table_cols': 2,
            'table_settings': {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines"
            }
        }
        
    @patch('src.data.table_extractor.PDFPLUMBER_AVAILABLE', True)
    def test_init_success(self):
        """测试成功初始化"""
        extractor = TableExtractor(self.config)
        
        assert extractor.min_table_rows == 2
        assert extractor.min_table_cols == 2
        assert extractor.table_settings['vertical_strategy'] == 'lines'
    
    @patch('src.data.table_extractor.PDFPLUMBER_AVAILABLE', False)
    def test_init_without_pdfplumber(self):
        """测试没有pdfplumber时的初始化"""
        with pytest.raises(DocumentProcessingError) as exc_info:
            TableExtractor(self.config)
        
        assert "pdfplumber is required" in str(exc_info.value)
    
    def test_is_valid_table_empty_data(self):
        """测试空表格数据验证"""
        extractor = TableExtractor(self.config)
        
        # 空数据
        assert not extractor._is_valid_table([])
        assert not extractor._is_valid_table(None)
    
    def test_is_valid_table_insufficient_rows(self):
        """测试行数不足的表格验证"""
        extractor = TableExtractor(self.config)
        
        # 只有一行
        table_data = [['Header1', 'Header2']]
        assert not extractor._is_valid_table(table_data)
    
    def test_is_valid_table_insufficient_cols(self):
        """测试列数不足的表格验证"""
        extractor = TableExtractor(self.config)
        
        # 只有一列
        table_data = [['Header1'], ['Data1']]
        assert not extractor._is_valid_table(table_data)
    
    def test_is_valid_table_too_many_empty_cells(self):
        """测试空单元格过多的表格验证"""
        extractor = TableExtractor(self.config)
        
        # 大部分单元格为空
        table_data = [
            ['Header1', 'Header2', 'Header3'],
            ['', '', ''],
            ['', '', 'Data1']
        ]
        assert not extractor._is_valid_table(table_data)
    
    def test_is_valid_table_valid_data(self):
        """测试有效表格数据验证"""
        extractor = TableExtractor(self.config)
        
        # 有效表格数据
        table_data = [
            ['Header1', 'Header2', 'Header3'],
            ['Data1', 'Data2', 'Data3'],
            ['Data4', 'Data5', 'Data6']
        ]
        assert extractor._is_valid_table(table_data)
    
    def test_get_table_boundary_box(self):
        """测试获取表格边界框"""
        extractor = TableExtractor(self.config)
        
        # 模拟表格对象
        mock_table = Mock()
        mock_table.bbox = (10.0, 20.0, 100.0, 200.0)
        
        boundary_box = extractor._get_table_boundary_box(mock_table)
        
        expected = {
            'x0': 10.0,
            'y0': 20.0,
            'x1': 100.0,
            'y1': 200.0
        }
        assert boundary_box == expected
    
    def test_convert_to_dataframe_empty_data(self):
        """测试空数据转换为DataFrame"""
        extractor = TableExtractor(self.config)
        
        df = extractor._convert_to_dataframe([])
        assert df.empty
    
    def test_convert_to_dataframe_with_headers(self):
        """测试带标题的数据转换为DataFrame"""
        extractor = TableExtractor(self.config)
        
        table_data = [
            ['Name', 'Age', 'City'],
            ['Alice', '25', 'Beijing'],
            ['Bob', '30', 'Shanghai']
        ]
        
        df = extractor._convert_to_dataframe(table_data)
        
        assert list(df.columns) == ['Name', 'Age', 'City']
        assert len(df) == 2
        assert df.iloc[0, 0] == 'Alice'
        assert df.iloc[1, 2] == 'Shanghai'
    
    def test_convert_to_dataframe_single_row(self):
        """测试单行数据转换为DataFrame"""
        extractor = TableExtractor(self.config)
        
        table_data = [['Data1', 'Data2', 'Data3']]
        
        df = extractor._convert_to_dataframe(table_data)
        
        assert list(df.columns) == ['Column_0', 'Column_1', 'Column_2']
        assert len(df) == 1
        assert df.iloc[0, 0] == 'Data1'
    
    def test_convert_to_dataframe_uneven_rows(self):
        """测试不规则行数据转换为DataFrame"""
        extractor = TableExtractor(self.config)
        
        table_data = [
            ['Name', 'Age'],
            ['Alice', '25', 'Extra'],
            ['Bob']
        ]
        
        df = extractor._convert_to_dataframe(table_data)
        
        # 应该补齐到最大列数
        assert len(df.columns) == 3
        assert df.iloc[1, 2] == 'Extra'  # 额外的列
        assert df.iloc[1, 1] == ''  # 补齐的空列
    
    def test_clean_dataframe(self):
        """测试DataFrame清理"""
        extractor = TableExtractor(self.config)
        
        # 创建包含空行和空列的DataFrame
        df = pd.DataFrame({
            'Name': ['Alice', '', 'Bob'],
            'Age': ['25', '30', ''],
            'Empty': ['', '', '']
        })
        
        cleaned_df = extractor._clean_dataframe(df)
        
        # 空列应该被移除
        assert 'Empty' not in cleaned_df.columns
        # 数据应该被清理
        assert cleaned_df.iloc[0, 0] == 'Alice'
    
    def test_serialize_to_markdown_empty_df(self):
        """测试空DataFrame序列化为Markdown"""
        extractor = TableExtractor(self.config)
        
        df = pd.DataFrame()
        markdown = extractor._serialize_to_markdown(df)
        
        assert markdown == ""
    
    def test_serialize_to_markdown_valid_df(self):
        """测试有效DataFrame序列化为Markdown"""
        extractor = TableExtractor(self.config)
        
        df = pd.DataFrame({
            'Name': ['Alice', 'Bob'],
            'Age': ['25', '30']
        })
        
        markdown = extractor._serialize_to_markdown(df)
        
        # 检查Markdown格式
        assert '| Name | Age |' in markdown
        assert '| Alice | 25 |' in markdown
        assert '| Bob | 30 |' in markdown
    
    def test_manual_markdown_conversion(self):
        """测试手动Markdown转换"""
        extractor = TableExtractor(self.config)
        
        df = pd.DataFrame({
            'Name': ['Alice', 'Bob'],
            'Age': ['25', '30']
        })
        
        markdown = extractor._manual_markdown_conversion(df)
        
        lines = markdown.split('\n')
        assert '| Name | Age |' in lines[0]
        assert '| --- | --- |' in lines[1]
        assert '| Alice | 25 |' in lines[2]
        assert '| Bob | 30 |' in lines[3]
    
    def test_classify_table_type_financial(self):
        """测试财务表格类型分类"""
        extractor = TableExtractor(self.config)
        
        df = pd.DataFrame({
            '营业收入': ['1000万', '1200万'],
            '净利润': ['100万', '150万']
        })
        
        table_type = extractor._classify_table_type(df, "财务报表")
        assert table_type == 'financial'
    
    def test_classify_table_type_summary(self):
        """测试摘要表格类型分类"""
        extractor = TableExtractor(self.config)
        
        df = pd.DataFrame({
            '要点': ['重点1', '重点2'],
            '说明': ['说明1', '说明2']
        })
        
        table_type = extractor._classify_table_type(df, "执行摘要")
        assert table_type == 'summary'
    
    def test_classify_table_type_other(self):
        """测试其他表格类型分类"""
        extractor = TableExtractor(self.config)
        
        df = pd.DataFrame({
            '姓名': ['张三', '李四'],
            '部门': ['技术部', '市场部']
        })
        
        table_type = extractor._classify_table_type(df, "员工信息")
        assert table_type == 'other'
    
    @patch('src.data.table_extractor.pdfplumber')
    def test_extract_tables_from_pdf_file_not_exists(self, mock_pdfplumber):
        """测试文件不存在时的表格提取"""
        extractor = TableExtractor(self.config)
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            extractor.extract_tables_from_pdf("nonexistent.pdf")
        
        assert "PDF文件不存在" in str(exc_info.value)
    
    @patch('src.data.table_extractor.pdfplumber')
    @patch('src.data.table_extractor.Path')
    def test_extract_tables_from_pdf_success(self, mock_path, mock_pdfplumber):
        """测试成功提取表格"""
        extractor = TableExtractor(self.config)
        
        # 模拟文件存在
        mock_path.return_value.exists.return_value = True
        
        # 模拟PDF和页面
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        # 模拟表格
        mock_table = MagicMock()
        mock_table.extract.return_value = [
            ['Header1', 'Header2'],
            ['Data1', 'Data2'],
            ['Data3', 'Data4']
        ]
        mock_table.bbox = (0, 0, 100, 100)
        mock_page.find_tables.return_value = [mock_table]
        
        result = extractor.extract_tables_from_pdf("test.pdf")
        
        assert len(result) == 1
        assert isinstance(result[0], TableChunk)
        assert result[0].page_number == 1
        assert 'Header1' in result[0].markdown_content
    
    def test_get_extraction_stats_empty(self):
        """测试空表格列表的统计信息"""
        extractor = TableExtractor(self.config)
        
        stats = extractor.get_extraction_stats([])
        
        expected = {
            'total_tables': 0,
            'pages_with_tables': 0,
            'table_types': {},
            'avg_table_size': 0
        }
        assert stats == expected
    
    def test_get_extraction_stats_with_data(self):
        """测试有数据的统计信息"""
        extractor = TableExtractor(self.config)
        
        # 创建测试表格分块
        table_chunks = [
            TableChunk(
                table_id="table_1",
                markdown_content="| A | B |\n|---|---|\n| 1 | 2 |",
                page_number=1,
                boundary_box={'x0': 0, 'y0': 0, 'x1': 100, 'y1': 100},
                table_type='financial'
            ),
            TableChunk(
                table_id="table_2",
                markdown_content="| C | D |\n|---|---|\n| 3 | 4 |",
                page_number=2,
                boundary_box={'x0': 0, 'y0': 0, 'x1': 100, 'y1': 100},
                table_type='other'
            )
        ]
        
        stats = extractor.get_extraction_stats(table_chunks)
        
        assert stats['total_tables'] == 2
        assert stats['pages_with_tables'] == 2
        assert stats['table_types']['financial'] == 1
        assert stats['table_types']['other'] == 1
        assert stats['avg_table_size'] > 0


class TestCreateTableExtractor:
    """测试表格提取器工厂函数"""
    
    @patch('src.data.table_extractor.PDFPLUMBER_AVAILABLE', True)
    def test_create_with_default_config(self):
        """测试使用默认配置创建"""
        extractor = create_table_extractor()
        
        assert extractor.min_table_rows == 2
        assert extractor.min_table_cols == 2
    
    @patch('src.data.table_extractor.PDFPLUMBER_AVAILABLE', True)
    def test_create_with_custom_config(self):
        """测试使用自定义配置创建"""
        config = {
            'min_table_rows': 3,
            'min_table_cols': 4
        }
        
        extractor = create_table_extractor(config)
        
        assert extractor.min_table_rows == 3
        assert extractor.min_table_cols == 4


if __name__ == '__main__':
    pytest.main([__file__])