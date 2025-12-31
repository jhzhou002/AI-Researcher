"""
API调用监控和统计
记录LLM调用、任务执行和系统性能指标
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import wraps
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """性能指标收集器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.llm_calls = defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0.0, "errors": 0})
        self.task_stats = defaultdict(lambda: {"count": 0, "completed": 0, "failed": 0, "total_time": 0.0})
        self.api_calls = defaultdict(lambda: {"count": 0, "total_time": 0.0, "errors": 0})
        self.start_time = datetime.now()
        self._lock = threading.Lock()
    
    def record_llm_call(
        self,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
        success: bool = True
    ):
        """记录LLM调用"""
        key = f"{provider}/{model}"
        with self._lock:
            self.llm_calls[key]["count"] += 1
            self.llm_calls[key]["tokens"] += input_tokens + output_tokens
            self.llm_calls[key]["cost"] += cost
            if not success:
                self.llm_calls[key]["errors"] += 1
    
    def record_task(
        self,
        task_type: str,
        duration: float,
        success: bool = True
    ):
        """记录任务执行"""
        with self._lock:
            self.task_stats[task_type]["count"] += 1
            self.task_stats[task_type]["total_time"] += duration
            if success:
                self.task_stats[task_type]["completed"] += 1
            else:
                self.task_stats[task_type]["failed"] += 1
    
    def record_api_call(
        self,
        endpoint: str,
        duration: float,
        success: bool = True
    ):
        """记录API调用"""
        with self._lock:
            self.api_calls[endpoint]["count"] += 1
            self.api_calls[endpoint]["total_time"] += duration
            if not success:
                self.api_calls[endpoint]["errors"] += 1
    
    def get_summary(self) -> Dict:
        """获取统计摘要"""
        uptime = datetime.now() - self.start_time
        
        # LLM统计
        total_llm_calls = sum(v["count"] for v in self.llm_calls.values())
        total_tokens = sum(v["tokens"] for v in self.llm_calls.values())
        total_cost = sum(v["cost"] for v in self.llm_calls.values())
        llm_errors = sum(v["errors"] for v in self.llm_calls.values())
        
        # 任务统计
        total_tasks = sum(v["count"] for v in self.task_stats.values())
        completed_tasks = sum(v["completed"] for v in self.task_stats.values())
        failed_tasks = sum(v["failed"] for v in self.task_stats.values())
        
        # API统计
        total_api_calls = sum(v["count"] for v in self.api_calls.values())
        api_errors = sum(v["errors"] for v in self.api_calls.values())
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime).split(".")[0],
            "llm": {
                "total_calls": total_llm_calls,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 4),
                "errors": llm_errors,
                "by_provider": dict(self.llm_calls)
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "success_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0,
                "by_type": dict(self.task_stats)
            },
            "api": {
                "total_calls": total_api_calls,
                "errors": api_errors,
                "by_endpoint": dict(self.api_calls)
            }
        }
    
    def reset(self):
        """重置所有统计"""
        with self._lock:
            self.llm_calls.clear()
            self.task_stats.clear()
            self.api_calls.clear()
            self.start_time = datetime.now()


# 全局实例
metrics = MetricsCollector()


def track_api_call(endpoint: str = None):
    """API调用追踪装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            ep = endpoint or func.__name__
            start = time.time()
            success = True
            try:
                return await func(*args, **kwargs)
            except Exception:
                success = False
                raise
            finally:
                duration = time.time() - start
                metrics.record_api_call(ep, duration, success)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            ep = endpoint or func.__name__
            start = time.time()
            success = True
            try:
                return func(*args, **kwargs)
            except Exception:
                success = False
                raise
            finally:
                duration = time.time() - start
                metrics.record_api_call(ep, duration, success)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def track_task(task_type: str = None):
    """任务追踪装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tt = task_type or func.__name__
            start = time.time()
            success = True
            try:
                return func(*args, **kwargs)
            except Exception:
                success = False
                raise
            finally:
                duration = time.time() - start
                metrics.record_task(tt, duration, success)
        
        return wrapper
    
    return decorator


# 导出
__all__ = ['MetricsCollector', 'metrics', 'track_api_call', 'track_task']
