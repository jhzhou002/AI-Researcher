"""
数据导出API
支持导出文献列表(Excel)和研究想法(Excel/Markdown)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.api.auth_utils import get_current_active_user
import pandas as pd
import io
import urllib.parse

router = APIRouter()

def get_project_or_404(db: Session, project_id: int, user_id: int):
    project = db.query(models.ResearchProject).filter(
        models.ResearchProject.id == project_id,
        models.ResearchProject.user_id == user_id
    ).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project

@router.get("/{project_id}/export/papers")
def export_papers(
    project_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """导出文献列表为Excel"""
    project = get_project_or_404(db, project_id, current_user.id)
    
    # 获取文献
    papers = db.query(models.Paper).filter(
        models.Paper.project_id == project_id
    ).order_by(models.Paper.relevance_score.desc()).all()
    
    if not papers:
        raise HTTPException(status_code=400, detail="No papers to export")
    
    # 构造数据
    data = []
    for p in papers:
        authors = ", ".join(p.authors) if p.authors else ""
        data.append({
            "Title": p.title,
            "Authors": authors,
            "Published Date": p.published,
            "Journal/Venue": p.journal,
            "Partition": p.partition,
            "Relevance (0-1)": p.relevance_score,
            "Abstract": p.abstract,
            "Link": p.url,
            "ArXiv ID": p.arxiv_id,
        })
    
    df = pd.DataFrame(data)
    
    # 导出为Excel流
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Papers')
    
    output.seek(0)
    
    filename = f"papers_project_{project_id}.xlsx"
    # 处理中文文件名 (Need URL encoding usually, or just safe ASCII)
    # Using safe ascii for simplicity or urlencoded
    encoded_filename = urllib.parse.quote(filename)
    
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"; filename*=utf-8\'\'{encoded_filename}'
    }
    
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )

@router.get("/{project_id}/export/ideas")
def export_ideas(
    project_id: int,
    format: str = "excel", # excel or markdown
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """导出研究想法"""
    project = get_project_or_404(db, project_id, current_user.id)
    
    ideas = db.query(models.ResearchIdeaDB).filter(
        models.ResearchIdeaDB.project_id == project_id
    ).order_by(models.ResearchIdeaDB.novelty_score.desc()).all()
    
    if not ideas:
        raise HTTPException(status_code=400, detail="No ideas to export")
    
    if format == "excel":
        data = []
        for idea in ideas:
            data.append({
                "Title": idea.title,
                "Core Hypothesis": idea.core_hypothesis,
                "Motivation": idea.motivation,
                "Difference from Existing": idea.difference_from_existing,
                "Novelty Score": idea.novelty_score,
                "Feasibility Score": idea.feasibility_score,
                "Expected Contribution": idea.expected_contribution
            })
            
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Research Ideas')
            
        output.seek(0)
        
        filename = f"ideas_project_{project_id}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"; filename*=utf-8\'\'{encoded_filename}'
        }
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers=headers
        )
        
    elif format == "markdown":
        content = f"# Research Ideas for Project: {project.title}\n\n"
        
        for i, idea in enumerate(ideas, 1):
            content += f"## {i}. {idea.title or 'Untitled Idea'}\n\n"
            content += f"**Scores**: Novelty={idea.novelty_score:.2f}, Feasibility={idea.feasibility_score:.2f}\n\n"
            content += f"### One-Sentence Hypothesis\n{idea.core_hypothesis}\n\n"
            content += f"### Motivation\n{idea.motivation}\n\n"
            content += f"### Difference from Existing\n{idea.difference_from_existing}\n\n"
            content += f"### Expected Contribution\n{idea.expected_contribution}\n\n"
            content += "---\n\n"
            
        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                'Content-Disposition': f'attachment; filename="ideas_project_{project_id}.md"'
            }
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'excel' or 'markdown'")
