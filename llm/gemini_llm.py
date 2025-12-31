"""
Gemini LLM适配器 (Google)
"""
from typing import List, Optional
from llm.base import BaseLLM, LLMMessage, LLMResponse, LLMProvider
import time


class GeminiLLM(BaseLLM):
    """Gemini LLM实现"""
    
    def _init_client(self):
        """初始化Gemini客户端"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            self._client = genai.GenerativeModel(self.config.model)
            self._genai = genai
        except ImportError:
            raise ImportError("请安装google-generativeai库: pip install google-generativeai")
    
    def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Gemini聊天接口"""
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        # Gemini格式：需要分离system和user消息
        system_instruction = None
        chat_history = []
        
        for i, msg in enumerate(messages):
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                chat_history.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                chat_history.append({"role": "model", "parts": [msg.content]})
        
        # 配置生成参数
        generation_config = {
            "temperature": temp,
        }
        
        if tokens:
            generation_config["max_output_tokens"] = tokens
        
        if json_mode:
            generation_config["response_mime_type"] = "application/json"
        
        # 重试机制
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                # 创建chat session
                if system_instruction:
                    model = self._genai.GenerativeModel(
                        self.config.model,
                        system_instruction=system_instruction
                    )
                else:
                    model = self._client
                
                # 如果有历史消息，使用chat模式
                if len(chat_history) > 1:
                    chat = model.start_chat(history=chat_history[:-1])
                    response = chat.send_message(
                        chat_history[-1]["parts"][0],
                        generation_config=generation_config
                    )
                else:
                    # 单次生成
                    response = model.generate_content(
                        chat_history[0]["parts"][0] if chat_history else "",
                        generation_config=generation_config
                    )
                
                content = response.text
                tokens_used = None  # Gemini不直接返回token数
                finish_reason = response.candidates[0].finish_reason.name if response.candidates else None
                
                cost = 0.0  # Gemini定价较复杂，暂时设为0
                
                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    provider=LLMProvider.GEMINI,
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
        
        raise Exception(f"Gemini API call failed after {self.config.max_retries} retries: {last_error}")
    
    def stream_chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Gemini流式聊天接口"""
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        system_instruction = None
        chat_history = []
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                chat_history.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                chat_history.append({"role": "model", "parts": [msg.content]})
        
        generation_config = {"temperature": temp}
        if tokens:
            generation_config["max_output_tokens"] = tokens
        
        if system_instruction:
            model = self._genai.GenerativeModel(
                self.config.model,
                system_instruction=system_instruction
            )
        else:
            model = self._client
        
        response = model.generate_content(
            chat_history[-1]["parts"][0] if chat_history else "",
            generation_config=generation_config,
            stream=True
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """计算Gemini成本"""
        # Gemini定价（按字符计费，这里简化处理）
        pricing = {
            "gemini-1.5-pro": 0.00125 / 1000,
            "gemini-1.5-flash": 0.000075 / 1000,
        }
        
        for model_key, price in pricing.items():
            if model_key in self.config.model.lower():
                return tokens_used * price if tokens_used else 0.0
        
        return 0.0
