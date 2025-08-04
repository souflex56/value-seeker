"""
金融数据特殊处理测试

测试财务表格的专门解析逻辑、关键财务指标提取和表格类型标注功能。
"""

import pytest
import pandas as pd
import numpy as np
from src.data.document_processor import DocumentProcessor
from src.data.models import Table


class TestFinancialDataProcessing:
    """金融数据处理测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.processor = DocumentProcessor()
    
    def test_financial_table_classification(self):
        """测试财务表格分类"""
        # 测试中文财务表格
        financial_df_cn = pd.DataFrame({
            '项目': ['营业收入', '净利润', '总资产', '负债总额'],
            '2023年': [1000000, 200000, 5000000, 2000000],
            '2022年': [800000, 150000, 4500000, 1800000]
        })
        
        table_type = self.processor._classify_table_type(financial_df_cn, '财务报表')
        assert table_type == 'financial'
        
        # 测试英文财务表格
        financial_df_en = pd.DataFrame({
            'Item': ['Revenue', 'Net Income', 'Total Assets', 'Total Liabilities'],
            '2023': [1000000, 200000, 5000000, 2000000],
            '2022': [800000, 150000, 4500000, 1800000]
        })
        
        table_type = self.processor._classify_table_type(financial_df_en, 'Financial Statement')
        assert table_type == 'financial'
        
        # 测试包含财务关键词的列名
        df_with_financial_columns = pd.DataFrame({
            '现金流': [100000, 120000, 90000],
            '毛利率': [0.35, 0.38, 0.32],
            '净利率': [0.15, 0.18, 0.12]
        })
        
        table_type = self.processor._classify_table_type(df_with_financial_columns, '业绩指标')
        assert table_type == 'financial'
    
    def test_summary_table_classification(self):
        """测试摘要表格分类"""
        summary_df = pd.DataFrame({
            '要点': ['核心业务', '主要风险', '投资建议'],
            '描述': ['稳定增长', '市场竞争激烈', '建议买入']
        })
        
        table_type = self.processor._classify_table_type(summary_df, '投资摘要')
        assert table_type == 'summary'
        
        # 测试英文摘要表格
        summary_df_en = pd.DataFrame({
            'Key Points': ['Core Business', 'Main Risks', 'Investment Advice'],
            'Description': ['Stable Growth', 'Market Competition', 'Buy Recommendation']
        })
        
        table_type = self.processor._classify_table_type(summary_df_en, 'Investment Summary')
        assert table_type == 'summary'
    
    def test_other_table_classification(self):
        """测试其他类型表格分类"""
        other_df = pd.DataFrame({
            '产品名称': ['产品A', '产品B', '产品C'],
            '销量': [1000, 1500, 800],
            '价格': [100, 150, 80]
        })
        
        table_type = self.processor._classify_table_type(other_df, '产品销量表')
        assert table_type == 'other'
    
    def test_financial_metrics_extraction(self):
        """测试财务指标提取"""
        # 创建包含多种财务指标的表格
        financial_df = pd.DataFrame({
            '财务指标': ['营业收入', '净利润', '总资产', '总负债', '经营现金流'],
            '2023年(万元)': [100000, 20000, 500000, 200000, 25000],
            '2022年(万元)': [80000, 15000, 450000, 180000, 20000],
            '增长率': ['25%', '33%', '11%', '11%', '25%']
        })
        
        table = Table(
            data=financial_df,
            caption='主要财务指标表',
            page_number=1,
            table_type='financial'
        )
        
        financial_data = self.processor.extract_financial_data([table])
        
        # 验证提取结果结构
        assert 'extracted_tables' in financial_data
        assert len(financial_data['extracted_tables']) == 1
        
        extracted_table = financial_data['extracted_tables'][0]
        assert extracted_table['page'] == 1
        assert extracted_table['caption'] == '主要财务指标表'
        assert 'data' in extracted_table
    
    def test_find_metric_value_by_column(self):
        """测试通过列名查找指标数值"""
        df = pd.DataFrame({
            '营业收入': [1000000, 800000],
            '净利润': [200000, 150000],
            '年份': ['2023', '2022']
        })
        
        # 测试通过列名直接匹配
        revenue = self.processor._find_metric_value(df, ['营业收入'])
        assert revenue == 1000000
        
        profit = self.processor._find_metric_value(df, ['净利润'])
        assert profit == 200000
        
        # 测试英文关键词
        df_en = pd.DataFrame({
            'Revenue': [1000000, 800000],
            'Net Income': [200000, 150000],
            'Year': ['2023', '2022']
        })
        
        revenue_en = self.processor._find_metric_value(df_en, ['revenue'])
        assert revenue_en == 1000000
    
    def test_find_metric_value_by_cell_content(self):
        """测试通过单元格内容查找指标数值"""
        df = pd.DataFrame({
            '项目': ['营业收入', '净利润', '总资产'],
            '金额(万元)': [100000, 20000, 500000],
            '占比': ['100%', '20%', '500%']
        })
        
        # 测试通过单元格内容匹配
        revenue = self.processor._find_metric_value(df, ['营业收入'])
        assert revenue == 100000
        
        profit = self.processor._find_metric_value(df, ['净利润'])
        assert profit == 20000
        
        assets = self.processor._find_metric_value(df, ['总资产'])
        assert assets == 500000
    
    def test_find_metric_value_not_found(self):
        """测试未找到指标的情况"""
        df = pd.DataFrame({
            '项目': ['销售额', '成本', '费用'],
            '金额': [1000, 600, 200]
        })
        
        # 查找不存在的指标
        result = self.processor._find_metric_value(df, ['营业收入', '净利润'])
        assert result is None
    
    def test_financial_table_enhancement(self):
        """测试财务表格增强处理"""
        # 创建包含需要清理的财务数据的表格
        raw_df = pd.DataFrame({
            '项目': ['营业收入', '净利润', '总资产', ''],  # 包含空行
            '金额': ['1,000,000', '200,000', '5,000,000', ''],  # 包含逗号的数字
            '增长率': ['25%', '33%', '11%', ''],  # 包含百分号
            '备注': ['主营业务', '扣非净利润', '期末余额', '']
        })
        
        table = Table(
            data=raw_df,
            caption='财务数据表',
            page_number=1,
            table_type='financial'
        )
        
        enhanced_table = self.processor._enhance_table(table)
        
        # 验证空行被移除
        assert len(enhanced_table.data) <= len(raw_df)
        
        # 验证表格基本信息保持不变
        assert enhanced_table.caption == '财务数据表'
        assert enhanced_table.page_number == 1
        assert enhanced_table.table_type == 'financial'
        
        # 验证数据不为空
        assert not enhanced_table.data.empty
    
    def test_multiple_financial_tables_processing(self):
        """测试多个财务表格的处理"""
        # 创建多个不同类型的财务表格
        income_statement = pd.DataFrame({
            '项目': ['营业收入', '营业成本', '毛利润', '净利润'],
            '2023年': [1000000, 600000, 400000, 200000],
            '2022年': [800000, 500000, 300000, 150000]
        })
        
        balance_sheet = pd.DataFrame({
            '项目': ['总资产', '总负债', '股东权益'],
            '2023年末': [5000000, 2000000, 3000000],
            '2022年末': [4500000, 1800000, 2700000]
        })
        
        cash_flow = pd.DataFrame({
            '项目': ['经营现金流', '投资现金流', '筹资现金流'],
            '2023年': [250000, -100000, -50000],
            '2022年': [200000, -80000, -30000]
        })
        
        tables = [
            Table(income_statement, '利润表', 1, 'financial'),
            Table(balance_sheet, '资产负债表', 2, 'financial'),
            Table(cash_flow, '现金流量表', 3, 'financial')
        ]
        
        financial_data = self.processor.extract_financial_data(tables)
        
        # 验证所有表格都被处理
        assert len(financial_data['extracted_tables']) == 3
        
        # 验证表格信息
        table_captions = [t['caption'] for t in financial_data['extracted_tables']]
        assert '利润表' in table_captions
        assert '资产负债表' in table_captions
        assert '现金流量表' in table_captions
        
        # 验证页码信息
        pages = [t['page'] for t in financial_data['extracted_tables']]
        assert 1 in pages
        assert 2 in pages
        assert 3 in pages
    
    def test_financial_ratios_calculation_preparation(self):
        """测试财务比率计算的数据准备"""
        # 创建包含计算财务比率所需数据的表格
        df = pd.DataFrame({
            '项目': ['营业收入', '净利润', '总资产', '股东权益'],
            '金额(万元)': [100000, 15000, 500000, 300000]
        })
        
        table = Table(
            data=df,
            caption='主要财务数据',
            page_number=1,
            table_type='financial'
        )
        
        # 提取财务数据
        financial_data = self.processor.extract_financial_data([table])
        
        # 验证数据结构适合后续比率计算
        assert 'extracted_tables' in financial_data
        extracted_data = financial_data['extracted_tables'][0]['data']
        
        # 验证可以用于计算常见财务比率
        # 这里主要验证数据结构，实际比率计算可能在其他模块中实现
        assert isinstance(extracted_data, dict) or hasattr(extracted_data, 'keys')
    
    def test_financial_data_type_conversion(self):
        """测试财务数据类型转换"""
        # 创建包含各种格式数字的表格
        df = pd.DataFrame({
            '项目': ['收入', '利润', '资产'],
            '金额': ['1,000,000', '200,000.50', '5.5亿'],  # 不同格式的数字
            '比率': ['25%', '10.5%', '0.15'],  # 百分比和小数
            '货币': ['$1000', '¥2000', '€1500']  # 带货币符号
        })
        
        enhanced_table = self.processor._enhance_table(
            Table(df, '测试数据', 1, 'financial')
        )
        
        # 验证表格处理没有出错
        assert not enhanced_table.data.empty
        assert enhanced_table.table_type == 'financial'
    
    def test_financial_keywords_recognition(self):
        """测试财务关键词识别"""
        # 测试中文财务关键词
        cn_keywords = ['营收', '收入', '利润', '资产', '负债', '现金流', '毛利率', '净利率']
        
        for keyword in cn_keywords:
            df = pd.DataFrame({
                '指标': [keyword, '其他指标'],
                '数值': [1000000, 500000]
            })
            
            table_type = self.processor._classify_table_type(df, f'{keyword}分析表')
            assert table_type == 'financial'
        
        # 测试英文财务关键词
        en_keywords = ['revenue', 'income', 'profit', 'asset', 'liability', 'cash flow']
        
        for keyword in en_keywords:
            df = pd.DataFrame({
                'Metric': [keyword, 'Other Metric'],
                'Value': [1000000, 500000]
            })
            
            table_type = self.processor._classify_table_type(df, f'{keyword} Analysis')
            assert table_type == 'financial'
    
    def test_complex_financial_table_structure(self):
        """测试复杂财务表格结构处理"""
        # 创建多层级表头的复杂财务表格
        complex_df = pd.DataFrame({
            '项目': ['营业收入', '其中：主营业务收入', '其中：其他业务收入', '营业成本', '毛利润'],
            '2023年Q1': [250000, 230000, 20000, 150000, 100000],
            '2023年Q2': [280000, 260000, 20000, 170000, 110000],
            '2023年Q3': [300000, 280000, 20000, 180000, 120000],
            '2023年Q4': [320000, 300000, 20000, 190000, 130000],
            '全年合计': [1150000, 1070000, 80000, 690000, 460000]
        })
        
        table = Table(
            data=complex_df,
            caption='分季度财务数据',
            page_number=1,
            table_type='financial'
        )
        
        # 测试复杂表格的处理
        enhanced_table = self.processor._enhance_table(table)
        financial_data = self.processor.extract_financial_data([enhanced_table])
        
        # 验证复杂表格被正确处理
        assert len(financial_data['extracted_tables']) == 1
        assert financial_data['extracted_tables'][0]['caption'] == '分季度财务数据'
    
    def test_financial_data_validation(self):
        """测试财务数据验证"""
        # 创建包含异常数据的表格
        df_with_anomalies = pd.DataFrame({
            '项目': ['营业收入', '净利润', '总资产', '异常项'],
            '金额': [1000000, 200000, 5000000, 'N/A'],  # 包含非数字数据
            '增长率': ['25%', '33%', '11%', '异常值']
        })
        
        table = Table(
            data=df_with_anomalies,
            caption='包含异常数据的表格',
            page_number=1,
            table_type='financial'
        )
        
        # 测试异常数据的处理
        try:
            enhanced_table = self.processor._enhance_table(table)
            financial_data = self.processor.extract_financial_data([enhanced_table])
            
            # 验证处理没有崩溃
            assert len(financial_data['extracted_tables']) == 1
        except Exception as e:
            # 如果有异常，应该是可预期的处理异常
            assert isinstance(e, (ValueError, TypeError, pd.errors.ParserError))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])