"""
LLM统一接入层 - 抽象基类
支持多家LLM提供商的统一接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    GEMINI = "gemini"
    QWEN = "qwen"
    KIMI = "kimi"


@dataclass
class LLMMessage:
    """LLM消息格式"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """LLM响应格式"""
    content: str
    model: str
    provider: LLMProvider
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider
    api_key: str
    model: str
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 60
    max_retries: int = 3
    
    # 成本控制
    max_cost_per_request: Optional[float] = None
    daily_budget: Optional[float] = None


class BaseLLM(ABC):
    """LLM基类 - 定义统一接口"""
    
    def __init__(self, config: LLMConfig):
        """
        初始化LLM客户端
        
        Args:
            config: LLM配置对象
        """
        self.config = config
        self.provider = config.provider
        self._client = None
        self._init_client()
    
    @abstractmethod
    def _init_client(self):
        """初始化具体的LLM客户端"""
        pass
    
    @abstractmethod
    def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        聊天接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            json_mode: 是否使用JSON模式
            **kwargs: 其他参数
        
        Returns:
            LLM响应对象
        """
        pass
    
    @abstractmethod
    def stream_chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        流式聊天接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        
        Yields:
            内容片段
        """
        pass
    
    def _prepare_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """
        准备消息格式（转换为API需要的格式）
        
        Args:
            messages: LLMMessage列表
        
        Returns:
            字典格式的消息列表
        """
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """
        计算成本（子类可重写以支持不同的定价）
        
        Args:
            tokens_used: 使用的token数
        
        Returns:
            成本（美元）
        """
        # 默认简单实现，子类应该重写
        return 0.0
    
    def _validate_budget(self, estimated_cost: float) -> bool:
        """
        验证预算
        
        Args:
            estimated_cost: 预估成本
        
        Returns:
            是否在预算内
        """
        if self.config.max_cost_per_request:
            if estimated_cost > self.config.max_cost_per_request:
                return False
        return True
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.config.model
    
    def get_provider(self) -> LLMProvider:
        """获取提供商"""
        return self.provider


class LLMFactory:
    """LLM工厂类 - 创建和管理LLM实例"""
    
    _instances: Dict[str, BaseLLM] = {}
    
    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLM:
        """
        创建LLM实例
        
        Args:
            config: LLM配置
        
        Returns:
            LLM实例
        """
        # 延迟导入以避免循环依赖
        from llm.openai_llm import OpenAILLM
        from llm.deepseek_llm import DeepSeekLLM
        from llm.claude_llm import ClaudeLLM
        from llm.gemini_llm import GeminiLLM
        from llm.qwen_llm import QwenLLM
        from llm.kimi_llm import KimiLLM
        
        provider_map = {
            LLMProvider.OPENAI: OpenAILLM,
            LLMProvider.DEEPSEEK: DeepSeekLLM,
            LLMProvider.CLAUDE: ClaudeLLM,
            LLMProvider.GEMINI: GeminiLLM,
            LLMProvider.QWEN: QwenLLM,
            LLMProvider.KIMI: KimiLLM,
        }
        
        llm_class = provider_map.get(config.provider)
        if not llm_class:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
        
        # 创建实例
        instance = llm_class(config)
        
        return instance
    
    @classmethod
    def get_or_create(cls, config: LLMConfig) -> BaseLLM:
        """
        获取或创建LLM实例（单例模式）
        
        Args:
            config: LLM配置
        
        Returns:
            LLM实例
        """
        key = f"{config.provider.value}:{config.model}"
        
        if key not in cls._instances:
            cls._instances[key] = cls.create(config)
        
        return cls._instances[key]
    
    @classmethod
    def clear_instances(cls):
        """清除所有实例"""
        cls._instances.clear()
