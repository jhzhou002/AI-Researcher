"""
Kimi LLM适配器 (月之暗面)
使用OpenAI兼容API
"""
from llm.openai_llm import OpenAILLM


class KimiLLM(OpenAILLM):
    """Kimi LLM实现（基于OpenAI兼容API）"""
    
    def _init_client(self):
        """初始化Kimi客户端"""
        if not self.config.base_url:
            self.config.base_url = "https://api.moonshot.cn/v1"
        
        super()._init_client()
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """计算Kimi成本"""
        pricing = {
            "moonshot-v1-8k": 0.000012 / 1000,
            "moonshot-v1-32k": 0.000024 / 1000,
            "moonshot-v1-128k": 0.00006 / 1000,
        }
        
        for model_key, price in pricing.items():
            if model_key in self.config.model.lower():
                return tokens_used * price
        
        return tokens_used * 0.000024 / 1000
