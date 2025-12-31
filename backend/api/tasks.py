"""
任务管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.db.database import get_db
from backend.db import models
from backend.schemas import TaskResponse, TaskCreate, MessageResponse
from backend.api.auth_utils import get_current_active_user

router = APIRouter()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_status(
    task_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取任务状态"""
    task = db.query(models.AsyncTask).filter(
        models.AsyncTask.task_id == task_id,
        models.AsyncTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    project_id: int = None,
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的任务列表"""
    query = db.query(models.AsyncTask).filter(
        models.AsyncTask.user_id == current_user.id
    )
    
    if project_id:
        query = query.filter(models.AsyncTask.project_id == project_id)
    
    tasks = query.order_by(models.AsyncTask.created_at.desc()).offset(skip).limit(limit).all()
    
    return tasks


@router.delete("/{task_id}", response_model=MessageResponse)
def cancel_task(
    task_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """取消任务"""
    task = db.query(models.AsyncTask).filter(
        models.AsyncTask.task_id == task_id,
        models.AsyncTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status in [models.TaskStatus.COMPLETED, models.TaskStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed or failed task"
        )
    
    # TODO: 实际取消Celery任务
    # from backend.tasks.celery_app import celery_app
    # celery_app.control.revoke(task_id, terminate=True)
    
    task.status = models.TaskStatus.CANCELLED
    db.commit()
    
    return {"message": "Task cancelled successfully"}
