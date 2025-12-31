"""
FastAPI主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting AI-Researcher API...")
    
    # 初始化LLM
    from llm_config import init_llms_from_env
    init_llms_from_env()
    logger.info("LLM providers initialized")
    
    # 初始化数据库
    from backend.db import init_db
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init warning: {e}")
    
    yield
    
    # 关闭时
    logger.info("Shutting down AI-Researcher API...")


# 创建FastAPI应用
app = FastAPI(
    title="AI-Researcher API",
    description="智能科研助手API - 从研究问题到论文草稿",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置 - 必须在所有路由之前
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# 根路由
@app.get("/")
async def root():
    """API根路由"""
    return {
        "name": "AI-Researcher API",
        "version": "1.0.0",
        "status": "running"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    from llm import llm_manager
    
    return {
        "status": "healthy",
        "llms_available": llm_manager.list_llms(),
        "default_llm": llm_manager.get_default_llm_name()
    }


# 导入路由
from backend.api import auth, projects, tasks, workflows
from backend.api import monitor

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(projects.router, prefix="/api/projects", tags=["研究项目"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务管理"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["工作流"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["监控"])

from backend.api import export
app.include_router(export.router, prefix="/api/projects", tags=["导出"])

from backend.api import export
app.include_router(export.router, prefix="/api/projects", tags=["导出"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
