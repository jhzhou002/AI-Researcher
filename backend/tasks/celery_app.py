"""
Celery应用配置
"""
import sys
import os

# 确保项目根目录在 Python 路径中（必须在所有其他导入之前）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# 创建Celery应用
celery_app = Celery(
    "ai_researcher",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# 配置
celery_app.conf.update(
    # 序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 时区
    timezone='Asia/Shanghai',
    enable_utc=False,
    
    # 任务跟踪
    task_track_started=True,
    task_send_sent_event=True,
    
    # 超时设置
    task_time_limit=3600,  # 1小时硬限制
    task_soft_time_limit=3000,  # 50分钟软限制
    
    # 结果
    result_expires=86400,  # 结果保存24小时
    result_backend_transport_options={'master_name': "mymaster"},
    
    # 重试
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # 性能
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 任务路由（可选，用于多队列）
celery_app.conf.task_routes = {
    'backend.tasks.literature.*': {'queue': 'literature'},
    'backend.tasks.analysis.*': {'queue': 'analysis'},
    'backend.tasks.generation.*': {'queue': 'generation'},
}

# 自动发现任务
celery_app.autodiscover_tasks([
    'backend.tasks.literature',
    'backend.tasks.analysis',
    'backend.tasks.generation'
])

# 显式导入任务以确保注册
import backend.tasks.literature
# 尝试导入其他可能存在的任务模块（如果存在）
try:
    import backend.tasks.analysis
except ImportError:
    pass
try:
    import backend.tasks.generation
except ImportError:
    pass

# 导出
__all__ = ['celery_app']
