"""
Celery Worker启动脚本
使用方式: python celery_worker.py
"""
import sys
import os

# 添加项目根目录到Python路径（必须在导入任何项目模块之前）
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 验证llm模块可用
print(f"Project root: {project_root}")
print(f"LLM module exists: {os.path.exists(os.path.join(project_root, 'llm'))}")

# 初始化LLM providers（必须在导入celery_app之前）
from llm_config import init_llms_from_env
init_llms_from_env()
print("LLM providers initialized for Celery worker")

# 导入Celery应用
from backend.tasks.celery_app import celery_app

if __name__ == '__main__':
    # 直接启动worker
    celery_app.worker_main(['worker', '--loglevel=info', '--pool=solo'])
