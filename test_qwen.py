"""
测试Qwen LLM连接
"""
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 加载环境变量
load_dotenv()

from llm.qwen_llm import QwenLLM
from llm.base import LLMConfig, LLMProvider, LLMMessage

def test_qwen():
    api_key = os.getenv("QWEN_API_KEY")
    print(f"Qwen API Key: {api_key[:5]}...")
    
    config = LLMConfig(
        provider=LLMProvider.QWEN,
        api_key=api_key,
        model="qwen-plus",
        timeout=30
    )
    
    # 手动打印初始化前的base_url
    print(f"Config base_url before init: {config.base_url}")
    
    llm = QwenLLM(config)
    
    # 打印初始化后的base_url
    print(f"Config base_url after init: {llm.config.base_url}")
    
    messages = [
        LLMMessage(role="user", content="Hello, tell me a short joke.")
    ]
    
    try:
        print("Sending request to Qwen...")
        response = llm.chat(messages)
        print(f"Response: {response.content}")
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qwen()
