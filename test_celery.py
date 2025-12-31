"""
Celery异步任务系统测试脚本
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Celery异步任务系统测试")
print("=" * 60)
print()

# ==================== 测试1: Celery配置 ====================
print("【测试1】Celery配置测试...")
try:
    from backend.tasks.celery_app import celery_app
    
    print(f"✅ Celery应用创建成功")
    print(f"   Broker: {celery_app.conf.broker_url}")
    print(f"   Backend: {celery_app.conf.result_backend}")
    print(f"   任务序列化: {celery_app.conf.task_serializer}")
    
except Exception as e:
    print(f"❌ Celery配置失败: {e}")

print()

# ==================== 测试2: 任务导入 ====================
print("【测试2】任务模块导入测试...")
try:
    from backend.tasks.base import DatabaseTask, ProgressTracker
    from backend.tasks.literature import literature_discovery_task
    
    print("✅ 任务模块导入成功")
    print(f"   - DatabaseTask ✓")
    print(f"   - ProgressTracker ✓")
    print(f"   - literature_discovery_task ✓")
    print(f"   任务名称: {literature_discovery_task.name}")
    
except Exception as e:
    print(f"❌ 任务导入失败: {e}")
    import traceback
    traceback.print_exc()

print()

# ==================== 测试3: Redis连接 ====================
print("【测试3】Redis连接测试...")
try:
    import redis
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(redis_url)
    
    # 测试连接
    r.ping()
    print(f"✅ Redis连接成功")
    print(f"   URL: {redis_url}")
    print(f"   版本: {r.info()['redis_version']}")
    
except Exception as e:
    print(f"❌ Redis连接失败: {e}")
    print(f"   提示: 请确保Redis正在运行")
    print(f"   Windows: 使用WSL或Docker启动Redis")
    print(f"   命令: docker run -d -p 6379:6379 redis:latest")

print()

# ==================== 测试4: 数据库连接（用于任务） ====================
print("【测试4】数据库连接测试...")
try:
    from backend.db.database import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ 数据库连接成功（任务将使用此连接）")
    
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")

print()

# ==================== 测试5: Celery Worker状态（可选） ====================
print("【测试5】Celery Worker状态...")
try:
    from celery import current_app
    
    # 检查活跃的worker
    inspect = current_app.control.inspect()
    active_workers = inspect.active()
    
    if active_workers:
        print(f"✅ 检测到{len(active_workers)}个活跃worker")
        for worker_name in active_workers.keys():
            print(f"   - {worker_name}")
    else:
        print("⚠️  未检测到活跃的worker")
        print("   提示: 使用以下命令启动worker:")
        print("   celery -A backend.tasks.celery_app worker --loglevel=info --pool=solo")
    
except Exception as e:
    print(f"⚠️  无法检查worker状态: {e}")

print()

# ==================== 总结 ====================
print("=" * 60)
print("测试完成！")
print("=" * 60)
print()
print("📋 启动完整系统的步骤：")
print()
print("1. 启动Redis:")
print("   docker run -d -p 6379:6379 redis:latest")
print()
print("2. 启动Celery Worker:")
print("   celery -A backend.tasks.celery_app worker --loglevel=info --pool=solo")
print()
print("3. 启动FastAPI:")
print("   python run.py")
print()
print("4. 测试API:")
print("   访问 http://localhost:8000/docs")
print("   创建项目并启动文献检索任务")
print()
