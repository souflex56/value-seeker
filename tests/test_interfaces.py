"""
接口和配置类单元测试

测试所有核心接口和配置类的行为。
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.core.interfaces import (
    ModelConfig, DataConfig, RetrievalConfig, PromptConfig,
    ConfigManagerInterface, DocumentProcessorInterface,
    RetrievalSystemInterface, PromptManagerInterface,
    ModelManagerInterface, ValueSeekerRAGInterface,
    EvaluatorInterface, TrainerInterface
)


class TestModelConfig:
    """ModelConfig配置类测试"""
    
    def test_model_config_creation_valid(self):
        """测试有效的ModelConfig创建"""
        config = ModelConfig(
            base_model="Qwen/Qwen2.5-7B-Instruct",
            device="cuda",
            max_memory="20GB",
            quantization="4bit"
        )
        
        assert config.base_model == "Qwen/Qwen2.5-7B-Instruct"
        assert config.device == "cuda"
        assert config.max_memory == "20GB"
        assert config.quantization == "4bit"
    
    def test_model_config_validation_valid(self):
        """测试有效配置的验证"""
        config = ModelConfig(
            base_model="Qwen/Qwen2.5-7B-Instruct",
            device="cuda",
            max_memory="20GB",
            quantization="4bit"
        )
        
        assert config.validate() is True
    
    def test_model_config_validation_invalid_device(self):
        """测试无效设备的验证"""
        config = ModelConfig(
            base_model="Qwen/Qwen2.5-7B-Instruct",
            device="invalid_device",
            max_memory="20GB",
            quantization="4bit"
        )
        
        assert config.validate() is False
    
    def test_model_config_validation_invalid_quantization(self):
        """测试无效量化的验证"""
        config = ModelConfig(
            base_model="Qwen/Qwen2.5-7B-Instruct",
            device="cuda",
            max_memory="20GB",
            quantization="invalid_quant"
        )
        
        assert config.validate() is False
    
    def test_model_config_validation_empty_model(self):
        """测试空模型名的验证"""
        config = ModelConfig(
            base_model="",
            device="cuda",
            max_memory="20GB",
            quantization="4bit"
        )
        
        assert config.validate() is False


class TestDataConfig:
    """DataConfig配置类测试"""
    
    def test_data_config_creation_valid(self):
        """测试有效的DataConfig创建"""
        config = DataConfig(
            reports_dir="./data/reports/",
            corpus_dir="./data/dyp_corpus/",
            chunk_size=512,
            chunk_overlap=50
        )
        
        assert config.reports_dir == "./data/reports/"
        assert config.corpus_dir == "./data/dyp_corpus/"
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
    
    def test_data_config_validation_valid(self):
        """测试有效配置的验证"""
        config = DataConfig(
            reports_dir="./data/reports/",
            corpus_dir="./data/dyp_corpus/",
            chunk_size=512,
            chunk_overlap=50
        )
        
        assert config.validate() is True
    
    def test_data_config_validation_invalid_chunk_size(self):
        """测试无效chunk_size的验证"""
        config = DataConfig(
            reports_dir="./data/reports/",
            corpus_dir="./data/dyp_corpus/",
            chunk_size=0,
            chunk_overlap=50
        )
        
        assert config.validate() is False
    
    def test_data_config_validation_overlap_too_large(self):
        """测试overlap过大的验证"""
        config = DataConfig(
            reports_dir="./data/reports/",
            corpus_dir="./data/dyp_corpus/",
            chunk_size=512,
            chunk_overlap=512
        )
        
        assert config.validate() is False


class TestRetrievalConfig:
    """RetrievalConfig配置类测试"""
    
    def test_retrieval_config_creation_valid(self):
        """测试有效的RetrievalConfig创建"""
        config = RetrievalConfig(
            embedding_model="BAAI/bge-m3",
            reranker_model="BAAI/bge-reranker-large",
            vector_store_path="./deploy/vector_store/",
            top_k=10,
            rerank_top_k=3
        )
        
        assert config.embedding_model == "BAAI/bge-m3"
        assert config.reranker_model == "BAAI/bge-reranker-large"
        assert config.vector_store_path == "./deploy/vector_store/"
        assert config.top_k == 10
        assert config.rerank_top_k == 3
    
    def test_retrieval_config_validation_valid(self):
        """测试有效配置的验证"""
        config = RetrievalConfig(
            embedding_model="BAAI/bge-m3",
            reranker_model="BAAI/bge-reranker-large",
            vector_store_path="./deploy/vector_store/",
            top_k=10,
            rerank_top_k=3
        )
        
        assert config.validate() is True
    
    def test_retrieval_config_validation_rerank_too_large(self):
        """测试rerank_top_k过大的验证"""
        config = RetrievalConfig(
            embedding_model="BAAI/bge-m3",
            reranker_model="BAAI/bge-reranker-large",
            vector_store_path="./deploy/vector_store/",
            top_k=5,
            rerank_top_k=10
        )
        
        assert config.validate() is False


class TestPromptConfig:
    """PromptConfig配置类测试"""
    
    def test_prompt_config_creation_valid(self):
        """测试有效的PromptConfig创建"""
        config = PromptConfig(
            query_rewrite_version="v1",
            generation_version="v1",
            style_version="v1",
            judge_version="v2"
        )
        
        assert config.query_rewrite_version == "v1"
        assert config.generation_version == "v1"
        assert config.style_version == "v1"
        assert config.judge_version == "v2"
    
    def test_prompt_config_validation_valid(self):
        """测试有效配置的验证"""
        config = PromptConfig(
            query_rewrite_version="v1",
            generation_version="v1",
            style_version="v1",
            judge_version="v2"
        )
        
        assert config.validate() is True
    
    def test_prompt_config_validation_empty_version(self):
        """测试空版本的验证"""
        config = PromptConfig(
            query_rewrite_version="",
            generation_version="v1",
            style_version="v1",
            judge_version="v2"
        )
        
        assert config.validate() is False


class TestInterfaceAbstractMethods:
    """测试接口的抽象方法"""
    
    def test_config_manager_interface_is_abstract(self):
        """测试ConfigManagerInterface是抽象的"""
        with pytest.raises(TypeError):
            ConfigManagerInterface("config.yaml")
    
    def test_document_processor_interface_is_abstract(self):
        """测试DocumentProcessorInterface是抽象的"""
        config = DataConfig("./data/reports/", "./data/corpus/", 512, 50)
        with pytest.raises(TypeError):
            DocumentProcessorInterface(config)
    
    def test_retrieval_system_interface_is_abstract(self):
        """测试RetrievalSystemInterface是抽象的"""
        config = RetrievalConfig("model", "reranker", "./vector/", 10, 3)
        with pytest.raises(TypeError):
            RetrievalSystemInterface(config)
    
    def test_prompt_manager_interface_is_abstract(self):
        """测试PromptManagerInterface是抽象的"""
        config = PromptConfig("v1", "v1", "v1", "v2")
        with pytest.raises(TypeError):
            PromptManagerInterface(config)
    
    def test_model_manager_interface_is_abstract(self):
        """测试ModelManagerInterface是抽象的"""
        config = ModelConfig("model", "cuda", "20GB", "4bit")
        with pytest.raises(TypeError):
            ModelManagerInterface(config)
    
    def test_value_seeker_rag_interface_is_abstract(self):
        """测试ValueSeekerRAGInterface是抽象的"""
        with pytest.raises(TypeError):
            ValueSeekerRAGInterface({})
    
    def test_evaluator_interface_is_abstract(self):
        """测试EvaluatorInterface是抽象的"""
        with pytest.raises(TypeError):
            EvaluatorInterface()
    
    def test_trainer_interface_is_abstract(self):
        """测试TrainerInterface是抽象的"""
        with pytest.raises(TypeError):
            TrainerInterface()


class MockConfigManager(ConfigManagerInterface):
    """ConfigManagerInterface的Mock实现"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
    
    def get_model_config(self) -> ModelConfig:
        return ModelConfig("model", "cuda", "20GB", "4bit")
    
    def get_data_config(self) -> DataConfig:
        return DataConfig("./data/reports/", "./data/corpus/", 512, 50)
    
    def get_retrieval_config(self) -> RetrievalConfig:
        return RetrievalConfig("embedding", "reranker", "./vector/", 10, 3)
    
    def get_prompt_config(self) -> PromptConfig:
        return PromptConfig("v1", "v1", "v1", "v2")
    
    def reload_config(self) -> None:
        pass


class MockDocumentProcessor(DocumentProcessorInterface):
    """DocumentProcessorInterface的Mock实现"""
    
    def __init__(self, config: DataConfig):
        self.config = config
    
    def parse_pdf(self, pdf_path: str):
        return []
    
    def chunk_documents(self, documents):
        return []
    
    def extract_metadata(self, document):
        return {}
    
    def process_tables(self, document):
        return []
    
    def extract_financial_data(self, tables):
        return {}


class TestInterfaceImplementations:
    """测试接口实现"""
    
    def test_config_manager_implementation(self):
        """测试ConfigManager接口实现"""
        manager = MockConfigManager("config.yaml")
        
        assert manager.config_path == "config.yaml"
        assert isinstance(manager.get_model_config(), ModelConfig)
        assert isinstance(manager.get_data_config(), DataConfig)
        assert isinstance(manager.get_retrieval_config(), RetrievalConfig)
        assert isinstance(manager.get_prompt_config(), PromptConfig)
        
        # 测试reload_config不抛出异常
        manager.reload_config()
    
    def test_document_processor_implementation(self):
        """测试DocumentProcessor接口实现"""
        config = DataConfig("./data/reports/", "./data/corpus/", 512, 50)
        processor = MockDocumentProcessor(config)
        
        assert processor.config == config
        assert processor.parse_pdf("test.pdf") == []
        assert processor.chunk_documents([]) == []
        assert processor.extract_metadata(None) == {}
        assert processor.process_tables(None) == []
        assert processor.extract_financial_data([]) == {}


class TestInterfaceMethodSignatures:
    """测试接口方法签名"""
    
    def test_config_manager_method_signatures(self):
        """测试ConfigManager方法签名"""
        # 检查抽象方法是否存在
        methods = [
            'get_model_config',
            'get_data_config', 
            'get_retrieval_config',
            'get_prompt_config',
            'reload_config'
        ]
        
        for method in methods:
            assert hasattr(ConfigManagerInterface, method)
            assert callable(getattr(ConfigManagerInterface, method))
    
    def test_document_processor_method_signatures(self):
        """测试DocumentProcessor方法签名"""
        methods = [
            'parse_pdf',
            'chunk_documents',
            'extract_metadata',
            'process_tables',
            'extract_financial_data'
        ]
        
        for method in methods:
            assert hasattr(DocumentProcessorInterface, method)
            assert callable(getattr(DocumentProcessorInterface, method))
    
    def test_retrieval_system_method_signatures(self):
        """测试RetrievalSystem方法签名"""
        methods = [
            'build_index',
            'retrieve',
            'rerank',
            'hybrid_search',
            'update_index'
        ]
        
        for method in methods:
            assert hasattr(RetrievalSystemInterface, method)
            assert callable(getattr(RetrievalSystemInterface, method))
    
    def test_prompt_manager_method_signatures(self):
        """测试PromptManager方法签名"""
        methods = [
            'get_query_rewrite_prompt',
            'get_drafting_prompt',
            'get_refinement_prompt',
            'get_style_prompt',
            'get_judge_prompt',
            'load_prompt_template'
        ]
        
        for method in methods:
            assert hasattr(PromptManagerInterface, method)
            assert callable(getattr(PromptManagerInterface, method))
    
    def test_model_manager_method_signatures(self):
        """测试ModelManager方法签名"""
        methods = [
            'load_base_model',
            'load_embedding_model',
            'load_reranker_model',
            'setup_quantization',
            'get_model_info',
            'optimize_memory'
        ]
        
        for method in methods:
            assert hasattr(ModelManagerInterface, method)
            assert callable(getattr(ModelManagerInterface, method))
    
    def test_value_seeker_rag_method_signatures(self):
        """测试ValueSeekerRAG方法签名"""
        methods = [
            'generate',
            '_rewrite_query',
            '_retrieve_documents',
            '_generate_draft',
            '_refine_answer',
            '_format_response'
        ]
        
        for method in methods:
            assert hasattr(ValueSeekerRAGInterface, method)
            assert callable(getattr(ValueSeekerRAGInterface, method))
    
    def test_evaluator_method_signatures(self):
        """测试Evaluator方法签名"""
        methods = [
            'evaluate_faithfulness',
            'evaluate_relevancy',
            'evaluate_style_alignment',
            'generate_evaluation_report'
        ]
        
        for method in methods:
            assert hasattr(EvaluatorInterface, method)
            assert callable(getattr(EvaluatorInterface, method))
    
    def test_trainer_method_signatures(self):
        """测试Trainer方法签名"""
        methods = [
            'prepare_training_data',
            'train_dpo',
            'train_kto',
            'evaluate_training'
        ]
        
        for method in methods:
            assert hasattr(TrainerInterface, method)
            assert callable(getattr(TrainerInterface, method))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])