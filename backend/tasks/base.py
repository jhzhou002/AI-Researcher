"""
Celery任务基类
提供数据库会话管理和进度追踪
"""
from celery import Task
from backend.db.database import SessionLocal
from backend.db import models
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """带数据库会话管理的任务基类"""
    
    _db = None
    
    @property
    def db(self):
        """获取数据库会话"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """任务完成后清理资源"""
        if self._db is not None:
            self._db.close()
            self._db = None
    
    def update_task_status(
        self,
        task_id: str,
        status: str = None,
        progress: int = None,
        message: str = None,
        result: dict = None,
        error: str = None
    ):
        """
        更新任务状态到数据库
        
        Args:
            task_id: Celery任务ID
            status: 任务状态
            progress: 进度（0-100）
            message: 当前消息
            result: 结果数据
            error: 错误消息
        """
        try:
            with SessionLocal() as db:
                task = db.query(models.AsyncTask).filter(
                    models.AsyncTask.task_id == task_id
                ).first()
                
                if not task:
                    logger.warning(f"Task {task_id} not found in database")
                    return
                
                # 更新状态
                if status:
                    task.status = models.TaskStatus(status)
                
                # 更新进度
                if progress is not None:
                    task.progress = min(100, max(0, progress))
                
                # 更新消息
                if message:
                    if task.result is None:
                        task.result = {}
                    task.result["current_message"] = message
                
                # 更新结果
                if result:
                    task.result = {**(task.result or {}), **result}
                
                # 更新错误
                if error:
                    task.error_message = error
                
                # 更新时间戳
                if status == "running" and not task.started_at:
                    task.started_at = datetime.utcnow()
                
                if status in ["completed", "failed"]:
                    task.completed_at = datetime.utcnow()
                
                db.commit()
                logger.debug(f"Task {task_id} status updated: {status}, progress: {progress}")
        
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        error_msg = f"{type(exc).__name__}: {str(exc)}"
        self.update_task_status(
            task_id=task_id,
            status="failed",
            progress=0,
            error=error_msg
        )
        logger.error(f"Task {task_id} failed: {error_msg}")
    
    def on_success(self, retval, task_id,args, kwargs):
        """任务成功时的回调"""
        self.update_task_status(
            task_id=task_id,
            status="completed",
            progress=100,
            result=retval if isinstance(retval, dict) else {"result": retval}
        )
        logger.info(f"Task {task_id} completed successfully")


class ProgressTracker:
    """进度追踪辅助类"""
    
    def __init__(self, task: DatabaseTask, task_id: str, total_steps: int):
        """
        初始化进度追踪器
        
        Args:
            task: DatabaseTask实例
            task_id: 任务ID
            total_steps: 总步骤数
        """
        self.task = task
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
    
    def update(self, message: str = ""):
        """更新到下一步"""
        self.current_step += 1
        progress = int((self.current_step / self.total_steps) * 100)
        self.task.update_task_status(
            task_id=self.task_id,
            progress=progress,
            message=message
        )
    
    def set_step(self, step: int, message: str = ""):
        """设置到特定步骤"""
        self.current_step = step
        progress = int((step / self.total_steps) * 100)
        self.task.update_task_status(
            task_id=self.task_id,
            progress=progress,
            message=message
        )
    
    def set_progress(self, progress: int, message: str = ""):
        """直接设置进度百分比"""
        self.task.update_task_status(
            task_id=self.task_id,
            progress=progress,
            message=message
        )
