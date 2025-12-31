"""
LLM管理器 - 简化业务代码中的LLM使用
"""
from typing import List, Optional, Dict, Any
from llm.base import (
    BaseLLM, LLMFactory, LLMConfig, LLMProvider,
    LLMMessage, LLMResponse
)
import logging

logger = logging.getLogger(__name__)


class LLMManager:
    """LLM管理器 - 统一管理多个LLM实例"""
    
    def __init__(self):
        self._llms: Dict[str, BaseLLM] = {}
        self._default_llm: Optional[str] = None
    
    def register_llm(
        self,
        name: str,
        provider: LLMProvider,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        is_default: bool = False,
        **kwargs
    ):
        """
        注册一个LLM实例
        
        Args:
            name: LLM实例名称（自定义，如 "fast-llm", "smart-llm"）
            provider: LLM提供商
            api_key: API密钥
            model: 模型名称
            base_url: 基础URL（可选）
            temperature: 温度参数
            max_tokens: 最大token数
            is_default: 是否设为默认LLM
            **kwargs: 其他配置参数
        """
        config = LLMConfig(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        llm = LLMFactory.create(config)
        self._llms[name] = llm
        
        if is_default or not self._default_llm:
            self._default_llm = name
        
        logger.info(f"Registered LLM: {name} ({provider.value}/{model})")
    
    def get_llm(self, name: Optional[str] = None) -> BaseLLM:
        """
        获取LLM实例
        
        Args:
            name: LLM名称，为None时返回默认LLM
        
        Returns:
            LLM实例
        """
        if name is None:
            name = self._default_llm
        
        if name not in self._llms:
            raise ValueError(f"LLM '{name}' not found. Available: {list(self._llms.keys())}")
        
        return self._llms[name]
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        llm_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        便捷的聊天接口
        
        Args:
            messages: 消息列表（字典格式）
            llm_name: 使用的LLM名称
            temperature: 温度参数
            max_tokens: 最大token数
            json_mode: JSON模式
            **kwargs: 其他参数
        
        Returns:
            LLM响应
        """
        llm = self.get_llm(llm_name)
        
        # 转换消息格式
        llm_messages = [
            LLMMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
        
        try:
            response = llm.chat(
                messages=llm_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                **kwargs
            )
            
            # 记录指标
            try:
                from backend.monitoring import metrics
                metrics.record_llm_call(
                    provider=llm.config.provider.value,
                    model=llm.config.model,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    cost=response.cost,
                    success=True
                )
            except Exception:
                pass  # 不影响主流程
            
            return response
            
        except Exception as e:
            # 记录失败
            try:
                from backend.monitoring import metrics
                metrics.record_llm_call(
                    provider=llm.config.provider.value,
                    model=llm.config.model,
                    success=False
                )
            except Exception:
                pass
            raise
    
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        llm_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        便捷的流式聊天接口
        
        Args:
            messages: 消息列表
            llm_name: 使用的LLM名称
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
        
        Yields:
            内容片段
        """
        llm = self.get_llm(llm_name)
        
        llm_messages = [
            LLMMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
        
        yield from llm.stream_chat(
            messages=llm_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def list_llms(self) -> List[str]:
        """列出所有已注册的LLM"""
        return list(self._llms.keys())
    
    def get_default_llm_name(self) -> Optional[str]:
        """获取默认LLM名称"""
        return self._default_llm
    
    def set_default_llm(self, name: str):
        """设置默认LLM"""
        if name not in self._llms:
            raise ValueError(f"LLM '{name}' not found")
        self._default_llm = name


# 全局LLM管理器实例
llm_manager = LLMManager()
