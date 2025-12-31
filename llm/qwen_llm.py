"""
Qwen LLM适配器 (阿里云通义千问)
使用OpenAI兼容API
"""
from llm.openai_llm import OpenAILLM


class QwenLLM(OpenAILLM):
    """Qwen LLM实现（基于OpenAI兼容API）"""
    
    def _init_client(self):
        """初始化Qwen客户端"""
        if not self.config.base_url:
            self.config.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        super()._init_client()
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """计算Qwen成本"""
        pricing = {
            "qwen-max": 0.00012 / 1000,
            "qwen-plus": 0.00004 / 1000,
            "qwen-turbo": 0.000002 / 1000,
        }
        
        for model_key, price in pricing.items():
            if model_key in self.config.model.lower():
                return tokens_used * price
        
        return tokens_used * 0.00004 / 1000
