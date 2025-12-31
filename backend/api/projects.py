"""
研究项目相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.db.database import get_db
from backend.db import models
from backend import schemas
from backend.schemas import (
    ResearchIntentCreate, ProjectResponse, ProjectList, MessageResponse
)
from backend.api.auth_utils import get_current_active_user

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ResearchIntentCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建研究项目"""
    new_project = models.ResearchProject(
        user_id=current_user.id,
        title=project_data.title,
        keywords=project_data.keywords,
        year_start=project_data.year_start,
        year_end=project_data.year_end,
        journal_level=project_data.journal_level.value,
        paper_type=project_data.paper_type.value,
        field=project_data.field.value,
        current_step="intent"
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project


@router.get("/", response_model=ProjectList)
def list_projects(
    skip: int = 0,
    limit: int = 10,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的研究项目列表"""
    query = db.query(models.ResearchProject).filter(
        models.ResearchProject.user_id == current_user.id
    )
    
    total = query.count()
    projects = query.order_by(models.ResearchProject.created_at.desc()).offset(skip).limit(limit).all()
    
    return {"projects": projects, "total": total}


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取单个项目详情"""
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ResearchIntentCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新项目"""
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 更新字段
    project.title = project_data.title
    project.keywords = project_data.keywords
    project.year_start = project_data.year_start
    project.year_end = project_data.year_end
    project.journal_level = project_data.journal_level.value
    project.paper_type = project_data.paper_type.value
    project.field = project_data.field.value
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
    project_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除项目"""
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/papers", response_model=List[schemas.PaperResponse])
def get_project_papers(
    project_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目的文献列表"""
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    papers = db.query(models.Paper).filter(
        models.Paper.project_id == project_id
    ).order_by(models.Paper.relevance_score.desc()).all()
    
    return papers


@router.get("/{project_id}/ideas", response_model=List[schemas.ResearchIdeaResponse])
def get_project_ideas(
    project_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取项目的研究想法列表"""
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    ideas = db.query(models.ResearchIdeaDB).filter(
        models.ResearchIdeaDB.project_id == project_id
    ).order_by(
        models.ResearchIdeaDB.novelty_score.desc(),
        models.ResearchIdeaDB.feasibility_score.desc()
    ).all()
    
    return ideas
