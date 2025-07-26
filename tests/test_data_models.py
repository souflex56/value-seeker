"""
数据模型单元测试

测试所有核心数据模型的创建、验证和行为。
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any

from src.data.models import (
    Document, Chunk, Table, InvestmentQuery, 
    AnalysisResult, SourceCitation, RetrievalResult
)


class TestDocument:
    """Document数据模型测试"""
    
    def test_document_creation_valid(self):
        """测试有效的Document创建"""
        tables = [
            Table(
                data=pd.DataFrame({"col1": [1, 2], "col2": [3, 4]}),
                caption="Test table",
                page_number=1,
                table_type="financial"
            )
        ]
        
        doc = Document(
            content="This is a test document content.",
            metadata={"author": "test", "date": "2024-01-01"},
            tables=tables,
            source="/path/to/document.pdf",
            page_number=1
        )
        
        assert doc.content == "This is a test document content."
        assert doc.metadata["author"] == "test"
        assert len(doc.tables) == 1
        assert doc.source == "/path/to/document.pdf"
        assert doc.page_number == 1
    
    def test_document_empty_content_raises_error(self):
        """测试空内容抛出异常"""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            Document(
                content="",
                metadata={},
                tables=[],
                source="/path/to/document.pdf",
                page_number=1
            )
    
    def test_document_invalid_page_number_raises_error(self):
        """测试无效页码抛出异常"""
        with pytest.raises(ValueError, match="Page number must be positive"):
            Document(
                content="Valid content",
                metadata={},
                tables=[],
                source="/path/to/document.pdf",
                page_number=0
            )


class TestChunk:
    """Chunk数据模型测试"""
    
    def test_chunk_creation_valid(self):
        """测试有效的Chunk创建"""
        embedding = np.array([0.1, 0.2, 0.3])
        
        chunk = Chunk(
            content="This is a chunk of text.",
            metadata={"chunk_index": 0},
            embedding=embedding,
            chunk_id="chunk_001",
            document_id="doc_001"
        )
        
        assert chunk.content == "This is a chunk of text."
        assert chunk.metadata["chunk_index"] == 0
        assert np.array_equal(chunk.embedding, embedding)
        assert chunk.chunk_id == "chunk_001"
        assert chunk.document_id == "doc_001"
    
    def test_chunk_without_embedding(self):
        """测试没有嵌入向量的Chunk"""
        chunk = Chunk(
            content="This is a chunk of text.",
            metadata={"chunk_index": 0},
            embedding=None,
            chunk_id="chunk_001",
            document_id="doc_001"
        )
        
        assert chunk.embedding is None
    
    def test_chunk_empty_content_raises_error(self):
        """测试空内容抛出异常"""
        with pytest.raises(ValueError, match="Chunk content cannot be empty"):
            Chunk(
                content="",
                metadata={},
                embedding=None,
                chunk_id="chunk_001",
                document_id="doc_001"
            )
    
    def test_chunk_empty_ids_raise_error(self):
        """测试空ID抛出异常"""
        with pytest.raises(ValueError, match="Chunk ID cannot be empty"):
            Chunk(
                content="Valid content",
                metadata={},
                embedding=None,
                chunk_id="",
                document_id="doc_001"
            )
        
        with pytest.raises(ValueError, match="Document ID cannot be empty"):
            Chunk(
                content="Valid content",
                metadata={},
                embedding=None,
                chunk_id="chunk_001",
                document_id=""
            )


class TestTable:
    """Table数据模型测试"""
    
    def test_table_creation_valid(self):
        """测试有效的Table创建"""
        data = pd.DataFrame({
            "Revenue": [1000, 1100, 1200],
            "Profit": [100, 120, 150]
        })
        
        table = Table(
            data=data,
            caption="Financial Summary",
            page_number=2,
            table_type="financial"
        )
        
        assert table.data.equals(data)
        assert table.caption == "Financial Summary"
        assert table.page_number == 2
        assert table.table_type == "financial"
    
    def test_table_default_type(self):
        """测试Table默认类型"""
        data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        
        table = Table(
            data=data,
            caption="Test table",
            page_number=1
        )
        
        assert table.table_type == "other"
    
    def test_table_empty_data_raises_error(self):
        """测试空数据抛出异常"""
        with pytest.raises(ValueError, match="Table data cannot be empty"):
            Table(
                data=pd.DataFrame(),
                caption="Empty table",
                page_number=1
            )
    
    def test_table_invalid_type_raises_error(self):
        """测试无效类型抛出异常"""
        data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        
        with pytest.raises(ValueError, match="Table type must be one of"):
            Table(
                data=data,
                caption="Test table",
                page_number=1,
                table_type="invalid_type"
            )
    
    def test_table_invalid_page_number_raises_error(self):
        """测试无效页码抛出异常"""
        data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        
        with pytest.raises(ValueError, match="Page number must be positive"):
            Table(
                data=data,
                caption="Test table",
                page_number=0
            )


class TestInvestmentQuery:
    """InvestmentQuery数据模型测试"""
    
    def test_investment_query_creation_valid(self):
        """测试有效的InvestmentQuery创建"""
        timestamp = datetime.now()
        
        query = InvestmentQuery(
            query_id="query_001",
            original_query="What is the revenue growth of Apple?",
            rewritten_queries=["Apple revenue growth", "AAPL financial performance"],
            timestamp=timestamp,
            user_id="user_123"
        )
        
        assert query.query_id == "query_001"
        assert query.original_query == "What is the revenue growth of Apple?"
        assert len(query.rewritten_queries) == 2
        assert query.timestamp == timestamp
        assert query.user_id == "user_123"
    
    def test_investment_query_default_values(self):
        """测试InvestmentQuery默认值"""
        query = InvestmentQuery(
            query_id="query_001",
            original_query="What is the revenue growth of Apple?"
        )
        
        assert query.rewritten_queries == []
        assert isinstance(query.timestamp, datetime)
        assert query.user_id is None
    
    def test_investment_query_empty_id_raises_error(self):
        """测试空ID抛出异常"""
        with pytest.raises(ValueError, match="Query ID cannot be empty"):
            InvestmentQuery(
                query_id="",
                original_query="Valid query"
            )
    
    def test_investment_query_empty_query_raises_error(self):
        """测试空查询抛出异常"""
        with pytest.raises(ValueError, match="Original query cannot be empty"):
            InvestmentQuery(
                query_id="query_001",
                original_query=""
            )


class TestAnalysisResult:
    """AnalysisResult数据模型测试"""
    
    def test_analysis_result_creation_valid(self):
        """测试有效的AnalysisResult创建"""
        sources = [
            SourceCitation(
                document_id="doc_001",
                chunk_id="chunk_001",
                content="Apple's revenue grew by 10%",
                page_number=1,
                relevance_score=0.95,
                citation_text="[1] Apple's revenue grew by 10%"
            )
        ]
        
        result = AnalysisResult(
            query_id="query_001",
            answer="Apple's revenue has shown strong growth...",
            confidence_score=0.85,
            sources=sources,
            processing_time=2.5,
            style_score=4.2
        )
        
        assert result.query_id == "query_001"
        assert result.answer == "Apple's revenue has shown strong growth..."
        assert result.confidence_score == 0.85
        assert len(result.sources) == 1
        assert result.processing_time == 2.5
        assert result.style_score == 4.2
    
    def test_analysis_result_invalid_confidence_score_raises_error(self):
        """测试无效置信度分数抛出异常"""
        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            AnalysisResult(
                query_id="query_001",
                answer="Valid answer",
                confidence_score=1.5,
                sources=[],
                processing_time=1.0,
                style_score=3.0
            )
    
    def test_analysis_result_negative_processing_time_raises_error(self):
        """测试负处理时间抛出异常"""
        with pytest.raises(ValueError, match="Processing time cannot be negative"):
            AnalysisResult(
                query_id="query_001",
                answer="Valid answer",
                confidence_score=0.8,
                sources=[],
                processing_time=-1.0,
                style_score=3.0
            )
    
    def test_analysis_result_invalid_style_score_raises_error(self):
        """测试无效风格分数抛出异常"""
        with pytest.raises(ValueError, match="Style score must be between 0.0 and 5.0"):
            AnalysisResult(
                query_id="query_001",
                answer="Valid answer",
                confidence_score=0.8,
                sources=[],
                processing_time=1.0,
                style_score=6.0
            )


class TestSourceCitation:
    """SourceCitation数据模型测试"""
    
    def test_source_citation_creation_valid(self):
        """测试有效的SourceCitation创建"""
        citation = SourceCitation(
            document_id="doc_001",
            chunk_id="chunk_001",
            content="Apple's revenue grew by 10% in Q4",
            page_number=15,
            relevance_score=0.92,
            citation_text="[1] Apple's revenue grew by 10% in Q4 (Page 15)"
        )
        
        assert citation.document_id == "doc_001"
        assert citation.chunk_id == "chunk_001"
        assert citation.content == "Apple's revenue grew by 10% in Q4"
        assert citation.page_number == 15
        assert citation.relevance_score == 0.92
        assert citation.citation_text == "[1] Apple's revenue grew by 10% in Q4 (Page 15)"
    
    def test_source_citation_empty_ids_raise_error(self):
        """测试空ID抛出异常"""
        with pytest.raises(ValueError, match="Document ID cannot be empty"):
            SourceCitation(
                document_id="",
                chunk_id="chunk_001",
                content="Valid content",
                page_number=1,
                relevance_score=0.8,
                citation_text="Valid citation"
            )
    
    def test_source_citation_invalid_relevance_score_raises_error(self):
        """测试无效相关性分数抛出异常"""
        with pytest.raises(ValueError, match="Relevance score must be between 0.0 and 1.0"):
            SourceCitation(
                document_id="doc_001",
                chunk_id="chunk_001",
                content="Valid content",
                page_number=1,
                relevance_score=1.5,
                citation_text="Valid citation"
            )


class TestRetrievalResult:
    """RetrievalResult数据模型测试"""
    
    def test_retrieval_result_creation_valid(self):
        """测试有效的RetrievalResult创建"""
        chunks = [
            Chunk(
                content="First chunk",
                metadata={},
                embedding=None,
                chunk_id="chunk_001",
                document_id="doc_001"
            ),
            Chunk(
                content="Second chunk",
                metadata={},
                embedding=None,
                chunk_id="chunk_002",
                document_id="doc_001"
            )
        ]
        scores = [0.95, 0.87]
        
        result = RetrievalResult(
            chunks=chunks,
            scores=scores,
            query="test query",
            total_time=0.5
        )
        
        assert len(result.chunks) == 2
        assert result.scores == [0.95, 0.87]
        assert result.query == "test query"
        assert result.total_time == 0.5
    
    def test_retrieval_result_mismatched_lengths_raises_error(self):
        """测试长度不匹配抛出异常"""
        chunks = [
            Chunk(
                content="First chunk",
                metadata={},
                embedding=None,
                chunk_id="chunk_001",
                document_id="doc_001"
            )
        ]
        scores = [0.95, 0.87]  # 长度不匹配
        
        with pytest.raises(ValueError, match="Chunks and scores lists must have the same length"):
            RetrievalResult(
                chunks=chunks,
                scores=scores,
                query="test query",
                total_time=0.5
            )
    
    def test_retrieval_result_negative_time_raises_error(self):
        """测试负时间抛出异常"""
        with pytest.raises(ValueError, match="Total time cannot be negative"):
            RetrievalResult(
                chunks=[],
                scores=[],
                query="test query",
                total_time=-1.0
            )


# 集成测试
class TestDataModelIntegration:
    """数据模型集成测试"""
    
    def test_complete_workflow_data_flow(self):
        """测试完整工作流程的数据流"""
        # 1. 创建文档和表格
        table_data = pd.DataFrame({
            "Metric": ["Revenue", "Profit"],
            "Q1": [1000, 100],
            "Q2": [1100, 120]
        })
        
        table = Table(
            data=table_data,
            caption="Quarterly Financial Results",
            page_number=5,
            table_type="financial"
        )
        
        document = Document(
            content="This document contains quarterly financial results for the company.",
            metadata={"company": "Apple", "quarter": "Q2 2024"},
            tables=[table],
            source="/reports/apple_q2_2024.pdf",
            page_number=5
        )
        
        # 2. 创建文档块
        chunk = Chunk(
            content="Apple's Q2 revenue reached $1100M, up from $1000M in Q1.",
            metadata={"extracted_from": "financial_table"},
            embedding=np.array([0.1, 0.2, 0.3, 0.4]),
            chunk_id="apple_q2_revenue_chunk",
            document_id="apple_q2_2024_doc"
        )
        
        # 3. 创建投资查询
        query = InvestmentQuery(
            query_id="apple_revenue_query_001",
            original_query="How did Apple's revenue perform in Q2 2024?",
            rewritten_queries=[
                "Apple Q2 2024 revenue performance",
                "AAPL quarterly revenue growth Q2",
                "Apple financial results second quarter 2024"
            ]
        )
        
        # 4. 创建引用来源
        citation = SourceCitation(
            document_id="apple_q2_2024_doc",
            chunk_id="apple_q2_revenue_chunk",
            content="Apple's Q2 revenue reached $1100M, up from $1000M in Q1.",
            page_number=5,
            relevance_score=0.95,
            citation_text="[1] Apple's Q2 revenue reached $1100M, up from $1000M in Q1. (Apple Q2 2024 Report, Page 5)"
        )
        
        # 5. 创建分析结果
        analysis = AnalysisResult(
            query_id="apple_revenue_query_001",
            answer="Apple demonstrated strong revenue growth in Q2 2024, with revenue increasing from $1000M in Q1 to $1100M in Q2, representing a 10% quarter-over-quarter growth. This performance aligns with the company's consistent growth trajectory and market expansion strategies.",
            confidence_score=0.92,
            sources=[citation],
            processing_time=3.2,
            style_score=4.5
        )
        
        # 6. 创建检索结果
        retrieval_result = RetrievalResult(
            chunks=[chunk],
            scores=[0.95],
            query="Apple Q2 2024 revenue performance",
            total_time=0.8
        )
        
        # 验证数据流的完整性
        assert document.tables[0].table_type == "financial"
        assert chunk.document_id == citation.document_id
        assert query.query_id == analysis.query_id
        assert analysis.sources[0].relevance_score == 0.95
        assert retrieval_result.chunks[0].chunk_id == citation.chunk_id
        
        # 验证数据的一致性
        assert len(retrieval_result.chunks) == len(retrieval_result.scores)
        assert analysis.confidence_score <= 1.0
        assert citation.page_number == document.page_number
        
        print("✅ 完整数据流测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])