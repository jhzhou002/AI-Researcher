"""
监控API路由
提供系统状态、性能指标和健康检查
"""
from fastapi import APIRouter, Depends
from backend.monitoring import metrics
from backend.db.database import engine
from sqlalchemy import text
import redis
import os
from datetime import datetime

router = APIRouter()


@router.get("/health")
def health_check():
    """健康检查端点"""
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {}
    }
    
    # 检查数据库
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["components"]["database"] = {"status": "up"}
    except Exception as e:
        checks["components"]["database"] = {"status": "down", "error": str(e)}
        checks["status"] = "degraded"
    
    # 检查Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        checks["components"]["redis"] = {"status": "up"}
    except Exception as e:
        checks["components"]["redis"] = {"status": "down", "error": str(e)}
        checks["status"] = "degraded"
    
    return checks


@router.get("/metrics")
def get_metrics():
    """获取系统性能指标"""
    return metrics.get_summary()


@router.get("/metrics/llm")
def get_llm_metrics():
    """获取LLM调用统计"""
    summary = metrics.get_summary()
    return summary["llm"]


@router.get("/metrics/tasks")
def get_task_metrics():
    """获取任务执行统计"""
    summary = metrics.get_summary()
    return summary["tasks"]


@router.get("/metrics/api")
def get_api_metrics():
    """获取API调用统计"""
    summary = metrics.get_summary()
    return summary["api"]


@router.post("/metrics/reset")
def reset_metrics():
    """重置所有指标"""
    metrics.reset()
    return {"message": "Metrics reset successfully"}


@router.get("/status")
def system_status():
    """获取系统整体状态"""
    health = health_check()
    metrics_summary = metrics.get_summary()
    
    return {
        "health": health,
        "uptime": metrics_summary["uptime_formatted"],
        "llm_calls": metrics_summary["llm"]["total_calls"],
        "total_cost": metrics_summary["llm"]["total_cost"],
        "tasks_completed": metrics_summary["tasks"]["completed"],
        "tasks_failed": metrics_summary["tasks"]["failed"],
        "api_calls": metrics_summary["api"]["total_calls"]
    }
