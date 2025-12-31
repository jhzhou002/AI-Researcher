"""
工作流相关API - 启动研究流程的各个阶段
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.schemas import TaskResponse, MessageResponse
from backend.api.auth_utils import get_current_active_user
from datetime import datetime

router = APIRouter()


@router.post("/projects/{project_id}/discover", response_model=TaskResponse)
def start_literature_discovery(
    project_id: int,
    max_results: int = 50,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启动文献检索任务（使用Celery）"""
    # 验证项目所有权
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 提交Celery任务
    from backend.tasks.literature import literature_discovery_task
    
    celery_result = literature_discovery_task.delay(project_id, max_results)
    
    # 创建任务记录
    task = models.AsyncTask(
        project_id=project_id,
        user_id=current_user.id,
        task_id=celery_result.id,
        task_name="Literature Discovery",
        task_type="discovery",
        status=models.TaskStatus.PENDING,
        progress=0
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/projects/{project_id}/analyze", response_model=TaskResponse)
def start_paper_analysis(
    project_id: int,
    max_papers: int = 20,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启动文献分析任务"""
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查是否有文献
    papers_count = db.query(models.Paper).filter(
        models.Paper.project_id == project_id
    ).count()
    
    if papers_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No papers found. Please run literature discovery first."
        )
    
    # 提交Celery任务
    from backend.tasks.analysis import paper_analysis_task
    
    celery_result = paper_analysis_task.delay(project_id, max_papers)
    
    # 创建任务记录
    task = models.AsyncTask(
        project_id=project_id,
        user_id=current_user.id,
        task_id=celery_result.id,
        task_name="Paper Analysis",
        task_type="analysis",
        status=models.TaskStatus.PENDING,
        progress=0
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


@router.get("/projects/{project_id}/status", response_model=MessageResponse)
def get_project_status(
    project_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目当前阶段状态"""
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 统计各阶段的完成情况
    papers_count = db.query(models.Paper).filter(models.Paper.project_id == project_id).count()
    analyses_count = db.query(models.PaperAnalysisDB).filter(models.PaperAnalysisDB.project_id == project_id).count()
    ideas_count = db.query(models.ResearchIdeaDB).filter(models.ResearchIdeaDB.project_id == project_id).count()
    
    landscape = db.query(models.ResearchLandscapeDB).filter(
        models.ResearchLandscapeDB.project_id == project_id
    ).first()
    
    method = db.query(models.MethodDesignDB).filter(
        models.MethodDesignDB.project_id == project_id
    ).first()
    
    draft = db.query(models.PaperDraftDB).filter(
        models.PaperDraftDB.project_id == project_id
    ).first()
    
    status_info = {
        "current_step": project.current_step,
        "papers_found": papers_count,
        "papers_analyzed": analyses_count,
        "ideas_generated": ideas_count,
        "has_landscape": landscape is not None,
        "has_method": method is not None,
        "has_draft": draft is not None
    }
    
    return {
        "message": f"Project is at step: {project.current_step}",
        "success": True,
        **status_info
    }


@router.post("/projects/{project_id}/landscape", response_model=TaskResponse)
def start_landscape_analysis(
    project_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启动研究脉络分析任务（使用Celery）"""
    # 验证项目所有权
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查是否已有文献分析
    analyses_count = db.query(models.PaperAnalysisDB).filter(
        models.PaperAnalysisDB.project_id == project_id
    ).count()
    
    if analyses_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No paper analyses found. Please run paper analysis first."
        )
    
    # 提交Celery任务
    from backend.tasks.analysis import landscape_analysis_task
    
    celery_result = landscape_analysis_task.delay(project_id)
    
    # 创建任务记录
    task = models.AsyncTask(
        project_id=project_id,
        user_id=current_user.id,
        task_id=celery_result.id,
        task_name="Research Landscape Analysis",
        task_type="landscape",
        status=models.TaskStatus.PENDING,
        progress=0
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/projects/{project_id}/ideas", response_model=TaskResponse)
def start_idea_generation(
    project_id: int,
    num_ideas: int = 5,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启动研究想法生成任务（使用Celery）"""
    # 验证项目所有权
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查是否已有脉络分析
    landscape = db.query(models.ResearchLandscapeDB).filter(
        models.ResearchLandscapeDB.project_id == project_id
    ).first()
    
    if not landscape:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No research landscape found. Please run landscape analysis first."
        )
    
    # 提交Celery任务
    from backend.tasks.generation import idea_generation_task
    
    celery_result = idea_generation_task.delay(project_id, num_ideas)
    
    # 创建任务记录
    task = models.AsyncTask(
        project_id=project_id,
        user_id=current_user.id,
        task_id=celery_result.id,
        task_name="Research Idea Generation",
        task_type="ideas",
        status=models.TaskStatus.PENDING,
        progress=0
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/projects/{project_id}/method", response_model=TaskResponse)
def start_method_design(
    project_id: int,
    idea_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启动方法设计任务（使用Celery）"""
    # 验证项目所有权
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查是否已有该想法
    idea = db.query(models.ResearchIdeaDB).filter(
        models.ResearchIdeaDB.project_id == project_id,
        models.ResearchIdeaDB.idea_id == idea_id
    ).first()
    
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research idea not found."
        )
    
    # 提交Celery任务
    from backend.tasks.generation import method_design_task
    
    celery_result = method_design_task.delay(project_id, idea_id)
    
    # 创建任务记录
    task = models.AsyncTask(
        project_id=project_id,
        user_id=current_user.id,
        task_id=celery_result.id,
        task_name="Method Design",
        task_type="method",
        status=models.TaskStatus.PENDING,
        progress=0
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/projects/{project_id}/draft", response_model=TaskResponse)
def start_paper_draft(
    project_id: int,
    idea_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """启动论文草稿生成任务（使用Celery）"""
    # 验证项目所有权
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查是否已有方法设计
    method = db.query(models.MethodDesignDB).filter(
        models.MethodDesignDB.project_id == project_id,
        models.MethodDesignDB.idea_id == idea_id
    ).first()
    
    if not method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Method design not found. Please run method design first."
        )
    
    # 提交Celery任务
    from backend.tasks.generation import paper_draft_task
    
    celery_result = paper_draft_task.delay(project_id, idea_id)
    
    # 创建任务记录
    task = models.AsyncTask(
        project_id=project_id,
        user_id=current_user.id,
        task_id=celery_result.id,
        task_name="Paper Draft Generation",
        task_type="draft",
        status=models.TaskStatus.PENDING,
        progress=0
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task

