"""检查最近的异步任务状态"""
import sys
sys.path.insert(0, '.')

from backend.db.database import SessionLocal
from backend.db import models

db = SessionLocal()
try:
    # 获取最近的任务
    tasks = db.query(models.AsyncTask).order_by(
        models.AsyncTask.created_at.desc()
    ).limit(5).all()
    
    print(f"\n最近 {len(tasks)} 个任务:")
    print("=" * 80)
    
    for task in tasks:
        print(f"\n任务ID: {task.task_id}")
        print(f"名称: {task.task_name}")
        print(f"项目ID: {task.project_id}")
        print(f"状态: {task.status.value}")
        print(f"进度: {task.progress}%")
        print(f"结果: {task.result}")
        print(f"错误: {task.error_message}")
        print("-" * 80)
    
    # 检查对应项目的论文数
    if tasks:
        project_id = tasks[0].project_id
        papers = db.query(models.Paper).filter(
            models.Paper.project_id == project_id
        ).all()
        print(f"\n项目 {project_id} 的论文数: {len(papers)}")
        
finally:
    db.close()
