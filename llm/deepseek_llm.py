"""
DeepSeek LLM适配器
DeepSeek使用兼容OpenAI的API
"""
from llm.openai_llm import OpenAILLM
from llm.base import LLMConfig, LLMProvider


class DeepSeekLLM(OpenAILLM):
    """DeepSeek LLM实现（基于OpenAI兼容API）"""
    
    def _init_client(self):
        """初始化DeepSeek客户端"""
        # DeepSeek使用OpenAI兼容API
        if not self.config.base_url:
            self.config.base_url = "https://api.deepseek.com/v1"
        
        super()._init_client()
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """
        计算DeepSeek成本
        DeepSeek的定价通常比OpenAI便宜很多
        """
        # DeepSeek定价（示例，需要根据实际调整）
        pricing = {
            "deepseek-chat": 0.00014 / 1000,  # 约 $0.14 per 1M tokens
            "deepseek-coder": 0.00014 / 1000,
        }
        
        for model_key, price in pricing.items():
            if model_key in self.config.model.lower():
                return tokens_used * price
        
        # 默认定价
        return tokens_used * 0.00014 / 1000
