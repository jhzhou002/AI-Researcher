"""
LLM配置初始化（从环境变量）
"""
import os
from llm import llm_manager, LLMProvider
from dotenv import load_dotenv

load_dotenv()


def init_llms_from_env():
    """从环境变量初始化所有配置的LLM（仅支持DeepSeek、Qwen、Kimi、GLM）"""
    
    # 优先注册国内模型
    
    # DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        llm_manager.register_llm(
            name="deepseek",
            provider=LLMProvider.DEEPSEEK,
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            temperature=0.5,
            is_default=True # DeepSeek作为默认
        )
    
    # Qwen (Alibaba)
    if os.getenv("QWEN_API_KEY"):
        llm_manager.register_llm(
            name="qwen",
            provider=LLMProvider.QWEN,
            api_key=os.getenv("QWEN_API_KEY"),
            model=os.getenv("QWEN_MODEL", "qwen-plus"),
            temperature=0.5
        )
    
    # Kimi (Moonshot)
    if os.getenv("KIMI_API_KEY"):
        llm_manager.register_llm(
            name="kimi",
            provider=LLMProvider.KIMI,
            api_key=os.getenv("KIMI_API_KEY"),
            model=os.getenv("KIMI_MODEL", "moonshot-v1-32k"),
            temperature=0.5
        )
        
    # 注意：不再注册 OpenAI, Claude, Gemini 以避免连接问题


def get_llm_for_task(task: str) -> str:
    """
    根据任务类型选择合适的LLM（仅国内模型）
    """
    # 确定默认可用模型（优先级：DeepSeek > Qwen > Kimi）
    default_model = None
    if os.getenv("DEEPSEEK_API_KEY"):
        default_model = "deepseek"
    elif os.getenv("QWEN_API_KEY"):
        default_model = "qwen"
    elif os.getenv("KIMI_API_KEY"):
        default_model = "kimi"
        
    if not default_model:
        # 如果没有任何国内key，回退到openai（虽然可能不通，但作为最后手段）
        if os.getenv("OPENAI_API_KEY"):
             # 这里不注册，只是返回名字，如果上面没注册就会报错，所以这里只是个占位
             return "openai-smart"
        raise ValueError("No supported domestic LLM (DeepSeek/Qwen/Kimi) API key found.")

    # 所有任务都映射到可用的国内模型
    # 代码任务稍微特殊一点，优先DeepSeek
    code_model = "deepseek" if os.getenv("DEEPSEEK_API_KEY") else default_model
    # 长上下文任务优先Kimi
    long_ctx_model = "kimi" if os.getenv("KIMI_API_KEY") else default_model
    
    task_llm_mapping = {
        "analysis": default_model,
        "generation": default_model,
        "fast": default_model,
        "code": code_model,
        "long_context": long_ctx_model,
    }
    
    llm_name = task_llm_mapping.get(task, default_model)
    
    # 验证该LLM是否已注册
    available_llms = llm_manager.list_llms()
    if llm_name not in available_llms:
        # 如果指定模型未注册（例如没有key），回退到默认
        return llm_manager.get_default_llm_name()
    
    return llm_name
