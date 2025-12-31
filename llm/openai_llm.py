"""
OpenAI LLM适配器
"""
from typing import List, Optional
from openai import OpenAI
from llm.base import BaseLLM, LLMMessage, LLMResponse, LLMConfig, LLMProvider
import time


class OpenAILLM(BaseLLM):
    """OpenAI LLM实现"""
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        import httpx
        
        # 检查是否为国内服务（不需要代理）
        is_domestic = False
        if self.config.base_url:
            domestic_domains = [
                "deepseek.com", 
                "aliyuncs.com", 
                "moonshot.cn", 
                "volces.com"
            ]
            if any(domain in self.config.base_url for domain in domestic_domains):
                is_domestic = True
        
        # 如果是国内服务，显式禁用代理
        http_client = None
        if is_domestic:
            http_client = httpx.Client(trust_env=False)
            
        self._client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            http_client=http_client
        )
    
    def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        **kwargs
    ) -> LLMResponse:
        """OpenAI聊天接口"""
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        # 准备消息
        formatted_messages = self._prepare_messages(messages)
        
        # 准备参数
        params = {
            "model": self.config.model,
            "messages": formatted_messages,
            "temperature": temp,
        }
        
        if tokens:
            params["max_tokens"] = tokens
        
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        
        # 添加额外参数
        params.update(kwargs)
        
        # 重试机制
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.chat.completions.create(**params)
                
                # 提取响应内容
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else None
                finish_reason = response.choices[0].finish_reason
                
                # 计算成本
                cost = self._calculate_cost(tokens_used) if tokens_used else None
                
                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    provider=LLMProvider.OPENAI,
                    tokens_used=tokens_used,
                    cost=cost,
                    finish_reason=finish_reason,
                    raw_response=response
                )
                
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    # 指数退避
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                break
        
        raise Exception(f"OpenAI API call failed after {self.config.max_retries} retries: {last_error}")
    
    def stream_chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """OpenAI流式聊天接口"""
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        formatted_messages = self._prepare_messages(messages)
        
        params = {
            "model": self.config.model,
            "messages": formatted_messages,
            "temperature": temp,
            "stream": True,
        }
        
        if tokens:
            params["max_tokens"] = tokens
        
        params.update(kwargs)
        
        response = self._client.chat.completions.create(**params)
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """
        计算OpenAI成本
        价格基于gpt-4o和gpt-4o-mini的定价
        """
        # 简化的定价模型（实际应该区分输入/输出token）
        pricing = {
            "gpt-4o": 0.005 / 1000,  # $5 per 1M tokens (平均)
            "gpt-4o-mini": 0.00015 / 1000,  # $0.15 per 1M tokens (平均)
            "gpt-4-turbo": 0.01 / 1000,
            "gpt-3.5-turbo": 0.0005 / 1000,
        }
        
        # 查找最匹配的定价
        for model_key, price in pricing.items():
            if model_key in self.config.model.lower():
                return tokens_used * price
        
        # 默认使用gpt-4o定价
        return tokens_used * pricing["gpt-4o"]
