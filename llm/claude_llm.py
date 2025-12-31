"""
Claude LLM适配器 (Anthropic)
"""
from typing import List, Optional
from llm.base import BaseLLM, LLMMessage, LLMResponse, LLMProvider
import time


class ClaudeLLM(BaseLLM):
    """Claude LLM实现"""
    
    def _init_client(self):
        """初始化Claude客户端"""
        try:
            from anthropic import Anthropic
            self._client = Anthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
        except ImportError:
            raise ImportError("请安装anthropic库: pip install anthropic")
    
    def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Claude聊天接口"""
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens or 4096
        
        # Claude API格式略有不同
        system_message = None
        user_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                user_messages.append({"role": msg.role, "content": msg.content})
        
        params = {
            "model": self.config.model,
            "messages": user_messages,
            "max_tokens": tokens,
            "temperature": temp,
        }
        
        if system_message:
            params["system"] = system_message
        
        params.update(kwargs)
        
        # 重试机制
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.messages.create(**params)
                
                content = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
                finish_reason = response.stop_reason
                
                cost = self._calculate_cost(tokens_used)
                
                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    provider=LLMProvider.CLAUDE,
                    tokens_used=tokens_used,
                    cost=cost,
                    finish_reason=finish_reason,
                    raw_response=response
                )
                
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                break
        
        raise Exception(f"Claude API call failed after {self.config.max_retries} retries: {last_error}")
    
    def stream_chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Claude流式聊天接口"""
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens or 4096
        
        system_message = None
        user_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                user_messages.append({"role": msg.role, "content": msg.content})
        
        params = {
            "model": self.config.model,
            "messages": user_messages,
            "max_tokens": tokens,
            "temperature": temp,
            "stream": True,
        }
        
        if system_message:
            params["system"] = system_message
        
        params.update(kwargs)
        
        with self._client.messages.stream(**params) as stream:
            for text in stream.text_stream:
                yield text
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """计算Claude成本"""
        pricing = {
            "claude-3-5-sonnet": 0.003 / 1000,
            "claude-3-opus": 0.015 / 1000,
            "claude-3-haiku": 0.00025 / 1000,
        }
        
        for model_key, price in pricing.items():
            if model_key in self.config.model.lower():
                return tokens_used * price
        
        return tokens_used * 0.003 / 1000
