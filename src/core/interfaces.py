"""
系统核心接口定义

本模块定义了AI投资分析师系统中各个组件的抽象基类和接口，
确保系统的模块化设计和可扩展性。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..data.models import (
    Document, Chunk, Table, InvestmentQuery, 
    AnalysisResult, SourceCitation, RetrievalResult
)


class BaseConfig(ABC):
    """配置基类"""
    
    @abstractmethod
    def validate(self) -> bool:
        """验证配置的有效性"""
        pass


class ModelConfig(BaseConfig):
    """模型配置类"""
    
    def __init__(self, base_model: str, device: str, max_memory: str, quantization: str):
        self.base_model = base_model
        self.device = device
        self.max_memory = max_memory
        self.quantization = quantization
    
    def validate(self) -> bool:
        """验证模型配置"""
        return all([
            self.base_model,
            self.device in ["cuda", "cpu", "mps"],
            self.quantization in ["4bit", "8bit", "none"]
        ])


class DataConfig(BaseConfig):
    """数据配置类"""
    
    def __init__(self, reports_dir: str, corpus_dir: str, chunk_size: int, chunk_overlap: int):
        self.reports_dir = reports_dir
        self.corpus_dir = corpus_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def validate(self) -> bool:
        """验证数据配置"""
        return all([
            self.reports_dir,
            self.corpus_dir,
            self.chunk_size > 0,
            self.chunk_overlap >= 0,
            self.chunk_overlap < self.chunk_size
        ])


class RetrievalConfig(BaseConfig):
    """检索配置类"""
    
    def __init__(self, embedding_model: str, reranker_model: str, 
                 vector_store_path: str, top_k: int, rerank_top_k: int):
        self.embedding_model = embedding_model
        self.reranker_model = reranker_model
        self.vector_store_path = vector_store_path
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k
    
    def validate(self) -> bool:
        """验证检索配置"""
        return all([
            self.embedding_model,
            self.reranker_model,
            self.vector_store_path,
            self.top_k > 0,
            self.rerank_top_k > 0,
            self.rerank_top_k <= self.top_k
        ])


class PromptConfig(BaseConfig):
    """Prompt配置类"""
    
    def __init__(self, query_rewrite_version: str, generation_version: str,
                 style_version: str, judge_version: str):
        self.query_rewrite_version = query_rewrite_version
        self.generation_version = generation_version
        self.style_version = style_version
        self.judge_version = judge_version
    
    def validate(self) -> bool:
        """验证Prompt配置"""
        return all([
            self.query_rewrite_version,
            self.generation_version,
            self.style_version,
            self.judge_version
        ])


class ConfigManagerInterface(ABC):
    """配置管理器接口"""
    
    @abstractmethod
    def __init__(self, config_path: str):
        """初始化配置管理器"""
        pass
    
    @abstractmethod
    def get_model_config(self) -> ModelConfig:
        """获取模型配置"""
        pass
    
    @abstractmethod
    def get_data_config(self) -> DataConfig:
        """获取数据配置"""
        pass
    
    @abstractmethod
    def get_retrieval_config(self) -> RetrievalConfig:
        """获取检索配置"""
        pass
    
    @abstractmethod
    def get_prompt_config(self) -> PromptConfig:
        """获取Prompt配置"""
        pass
    
    @abstractmethod
    def reload_config(self) -> None:
        """重新加载配置"""
        pass


class DocumentProcessorInterface(ABC):
    """文档处理器接口"""
    
    @abstractmethod
    def __init__(self, config: DataConfig):
        """初始化文档处理器"""
        pass
    
    @abstractmethod
    def parse_pdf(self, pdf_path: str) -> List[Document]:
        """解析PDF文档"""
        pass
    
    @abstractmethod
    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """文档分块"""
        pass
    
    @abstractmethod
    def extract_metadata(self, document: Document) -> Dict[str, Any]:
        """提取文档元数据"""
        pass
    
    @abstractmethod
    def process_tables(self, document: Document) -> List[Table]:
        """处理文档中的表格"""
        pass
    
    @abstractmethod
    def extract_financial_data(self, tables: List[Table]) -> Dict[str, Any]:
        """提取财务数据"""
        pass


class RetrievalSystemInterface(ABC):
    """检索系统接口"""
    
    @abstractmethod
    def __init__(self, config: RetrievalConfig):
        """初始化检索系统"""
        pass
    
    @abstractmethod
    def build_index(self, documents: List[Chunk]) -> None:
        """构建向量索引"""
        pass
    
    @abstractmethod
    def retrieve(self, queries: List[str], top_k: int = 10) -> List[RetrievalResult]:
        """检索相关文档"""
        pass
    
    @abstractmethod
    def rerank(self, query: str, candidates: List[Chunk], top_k: int = 3) -> List[Chunk]:
        """重排序候选文档"""
        pass
    
    @abstractmethod
    def hybrid_search(self, query: str) -> List[Chunk]:
        """混合检索"""
        pass
    
    @abstractmethod
    def update_index(self, new_documents: List[Chunk]) -> None:
        """更新索引"""
        pass


class PromptManagerInterface(ABC):
    """Prompt管理器接口"""
    
    @abstractmethod
    def __init__(self, config: PromptConfig):
        """初始化Prompt管理器"""
        pass
    
    @abstractmethod
    def get_query_rewrite_prompt(self, query: str) -> str:
        """获取查询重写Prompt"""
        pass
    
    @abstractmethod
    def get_drafting_prompt(self, query: str, context: str) -> str:
        """获取初稿生成Prompt"""
        pass
    
    @abstractmethod
    def get_refinement_prompt(self, query: str, draft: str, context: str) -> str:
        """获取修正Prompt"""
        pass
    
    @abstractmethod
    def get_style_prompt(self, content: str) -> str:
        """获取风格对齐Prompt"""
        pass
    
    @abstractmethod
    def get_judge_prompt(self, query: str, answer: str) -> str:
        """获取评判Prompt"""
        pass
    
    @abstractmethod
    def load_prompt_template(self, template_path: str) -> str:
        """加载Prompt模板"""
        pass


class ModelManagerInterface(ABC):
    """模型管理器接口"""
    
    @abstractmethod
    def __init__(self, config: ModelConfig):
        """初始化模型管理器"""
        pass
    
    @abstractmethod
    def load_base_model(self, model_name: str) -> Any:
        """加载基础模型"""
        pass
    
    @abstractmethod
    def load_embedding_model(self, model_name: str) -> Any:
        """加载嵌入模型"""
        pass
    
    @abstractmethod
    def load_reranker_model(self, model_name: str) -> Any:
        """加载重排序模型"""
        pass
    
    @abstractmethod
    def setup_quantization(self, bits: int) -> None:
        """设置量化"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass
    
    @abstractmethod
    def optimize_memory(self) -> None:
        """优化内存使用"""
        pass


class ValueSeekerRAGInterface(ABC):
    """核心RAG逻辑接口"""
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """初始化RAG系统"""
        pass
    
    @abstractmethod
    def generate(self, query: str) -> Dict[str, Any]:
        """生成回答"""
        pass
    
    @abstractmethod
    def _rewrite_query(self, query: str) -> List[str]:
        """查询重写"""
        pass
    
    @abstractmethod
    def _retrieve_documents(self, queries: List[str]) -> List[Chunk]:
        """检索文档"""
        pass
    
    @abstractmethod
    def _generate_draft(self, query: str, context: str) -> str:
        """生成初稿"""
        pass
    
    @abstractmethod
    def _refine_answer(self, query: str, draft: str, context: str) -> str:
        """修正回答"""
        pass
    
    @abstractmethod
    def _format_response(self, answer: str, sources: List[Chunk]) -> Dict[str, Any]:
        """格式化响应"""
        pass


class EvaluatorInterface(ABC):
    """评估器接口"""
    
    @abstractmethod
    def evaluate_faithfulness(self, query: str, answer: str, context: str) -> float:
        """评估忠实度"""
        pass
    
    @abstractmethod
    def evaluate_relevancy(self, query: str, answer: str) -> float:
        """评估相关性"""
        pass
    
    @abstractmethod
    def evaluate_style_alignment(self, answer: str) -> float:
        """评估风格对齐"""
        pass
    
    @abstractmethod
    def generate_evaluation_report(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """生成评估报告"""
        pass


class TrainerInterface(ABC):
    """训练器接口"""
    
    @abstractmethod
    def prepare_training_data(self, queries: List[InvestmentQuery], 
                            results: List[AnalysisResult]) -> Dict[str, Any]:
        """准备训练数据"""
        pass
    
    @abstractmethod
    def train_dpo(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """DPO训练"""
        pass
    
    @abstractmethod
    def train_kto(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """KTO训练"""
        pass
    
    @abstractmethod
    def evaluate_training(self, model_path: str) -> Dict[str, Any]:
        """评估训练结果"""
        pass