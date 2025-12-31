"""
想法生成和论文草稿相关的Celery任务
"""
import sys
import os
# 确保项目根目录在 Python 路径中（Celery worker需要）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.tasks.celery_app import celery_app
from backend.tasks.base import DatabaseTask, ProgressTracker
from backend.db.database import SessionLocal
from backend.db import models
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="generation.ideas",
    max_retries=2,
    default_retry_delay=60
)
def idea_generation_task(self, project_id: int, num_ideas: int = 5):
    """
    生成研究想法
    
    Args:
        project_id: 研究项目ID
        num_ideas: 生成想法数量
    
    Returns:
        dict: 生成结果
    """
    task_id = self.request.id
    tracker = ProgressTracker(self, task_id, total_steps=num_ideas + 3)
    
    try:
        with SessionLocal() as db:
            # 更新任务状态
            self.update_task_status(task_id=task_id, status="running")
            
            tracker.update("Loading research landscape...")
            
            # 获取脉络分析结果
            landscape_db = db.query(models.ResearchLandscapeDB).filter(
                models.ResearchLandscapeDB.project_id == project_id
            ).first()
            
            if not landscape_db:
                raise ValueError("No research landscape found. Please run landscape analysis first.")
            
            tracker.update("Generating research ideas...")
            
            # 导入业务模块
            from modules.idea_generator import ResearchIdeaGenerator  
            from models import ResearchLandscape
            from llm.manager import llm_manager
            
            generator = ResearchIdeaGenerator(llm_manager=llm_manager)
            
            # 转换为业务模型
            landscape = ResearchLandscape(
                clusters=landscape_db.clusters,
                solved_problems=landscape_db.solved_problems,
                partially_solved=landscape_db.partially_solved,
                unsolved_problems=landscape_db.unsolved_problems,
                technical_evolution=landscape_db.technical_evolution
            )
            
            # 生成想法
            ideas = generator.generate_ideas(landscape, num_ideas=num_ideas)
            
            logger.info(f"Generated {len(ideas)} ideas for project {project_id}")
            
            # 保存每个想法
            for i, idea in enumerate(ideas):
                tracker.update(f"Saving idea {i+1}/{len(ideas)}: {idea.title[:30]}...")
                
                db_idea = models.ResearchIdeaDB(
                    project_id=project_id,
                    idea_id=idea.idea_id,
                    title=idea.title,
                    motivation=idea.motivation,
                    core_hypothesis=idea.core_hypothesis,
                    expected_contribution=idea.expected_contribution,
                    difference_from_existing=idea.difference_from_existing,
                    novelty_score=idea.novelty_score,
                    feasibility_score=idea.feasibility_score
                )
                
                db.add(db_idea)
            
            db.commit()
            
            # 更新项目状态
            tracker.update("Updating project status...")
            
            project = db.query(models.ResearchProject).filter(
                models.ResearchProject.id == project_id
            ).first()
            
            if project:
                project.current_step = "ideas"
                db.commit()
            
            result = {
                "success": True,
                "ideas_generated": len(ideas),
                "avg_novelty_score": sum(idea.novelty_score for idea in ideas) / len(ideas) if ideas else 0,
                "avg_feasibility_score": sum(idea.feasibility_score for idea in ideas) / len(ideas) if ideas else 0
            }
            
            logger.info(f"Idea generation completed for project {project_id}: {result}")
            
            return result
    
    except Exception as exc:
        logger.error(f"Idea generation failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="generation.method",
    max_retries=2,
    default_retry_delay=60
)
def method_design_task(self, project_id: int, idea_id: str):
    """
    为研究想法设计方法
    
    Args:
        project_id: 研究项目ID
        idea_id: 研究想法ID
    
    Returns:
        dict: 设计结果
    """
    task_id = self.request.id
    tracker = ProgressTracker(self, task_id, total_steps=4)
    
    try:
        with SessionLocal() as db:
            self.update_task_status(task_id=task_id, status="running")
            
            tracker.update("Loading research idea...")
            
            # 获取研究想法
            idea_db = db.query(models.ResearchIdeaDB).filter(
                models.ResearchIdeaDB.project_id == project_id,
                models.ResearchIdeaDB.idea_id == idea_id
            ).first()
            
            if not idea_db:
                raise ValueError(f"Research idea {idea_id} not found")
            
            tracker.update("Designing method...")
            
            # 导入业务模块
            from modules.method_designer import MethodDesigner
            from models import ResearchIdea
            from llm.manager import llm_manager
            
            designer = MethodDesigner(llm_manager=llm_manager)
            
            # 转换为业务模型
            idea = ResearchIdea(
                id=idea_db.idea_id,
                title=idea_db.title,
                motivation=idea_db.motivation,
                hypothesis=idea_db.hypothesis,
                contributions=idea_db.contributions,
                difference_from_existing=idea_db.difference_from_existing,
                novelty_score=idea_db.novelty_score,
                feasibility_score=idea_db.feasibility_score
            )
            
            # 设计方法
            method = designer.design_method(idea)
            
            tracker.update("Saving results...")
            
            # 保存到数据库
            db_method = models.MethodDesignDB(
                project_id=project_id,
                idea_id=idea_id,
                algorithm_framework=method.algorithm_framework,
                key_modules=method.key_modules,
                data_requirements=method.data_requirements,
                evaluation_metrics=method.evaluation_metrics
            )
            
            db.add(db_method)
            db.commit()
            
            # 更新项目状态
            project = db.query(models.ResearchProject).filter(
                models.ResearchProject.id == project_id
            ).first()
            
            if project:
                project.current_step = "method"
                db.commit()
            
            result = {
                "success": True,
                "method_id": db_method.id,
                "innovation_points": len(method.innovation_points)
            }
            
            logger.info(f"Method design completed for project {project_id}: {result}")
            
            return result
    
    except Exception as exc:
        logger.error(f"Method design failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="generation.paper_draft",
    max_retries=1,
    default_retry_delay=120
)
def paper_draft_task(self, project_id: int, idea_id: str):
    """
    生成论文草稿
    
    Args:
        project_id: 研究项目ID
        idea_id: 研究想法ID
    
    Returns:
        dict: 生成结果
    """
    task_id = self.request.id
    tracker = ProgressTracker(self, task_id, total_steps=8)
    
    try:
        with SessionLocal() as db:
            self.update_task_status(task_id=task_id, status="running")
            
            tracker.update("Loading research idea and method...")
            
            # 获取研究想法
            idea_db = db.query(models.ResearchIdeaDB).filter(
                models.ResearchIdeaDB.project_id == project_id,
                models.ResearchIdeaDB.idea_id == idea_id
            ).first()
            
            if not idea_db:
                raise ValueError(f"Research idea {idea_id} not found")
            
            # 获取方法设计
            method_db = db.query(models.MethodDesignDB).filter(
                models.MethodDesignDB.project_id == project_id,
                models.MethodDesignDB.idea_id == idea_id
            ).first()
            
            if not method_db:
                raise ValueError("Method design not found. Please run method design first.")
            
            tracker.update("Initializing paper generator...")
            
            # 导入业务模块
            from modules.paper_draft_generator import PaperDraftGenerator
            from models import ResearchIdea, MethodDesign
            from llm.manager import llm_manager
            
            generator = PaperDraftGenerator(llm_manager=llm_manager)
            
            # 转换为业务模型
            idea = ResearchIdea(
                id=idea_db.idea_id,
                title=idea_db.title,
                motivation=idea_db.motivation,
                hypothesis=idea_db.hypothesis,
                contributions=idea_db.contributions,
                difference_from_existing=idea_db.difference_from_existing,
                novelty_score=idea_db.novelty_score,
                feasibility_score=idea_db.feasibility_score
            )
            
            method = MethodDesign(
                id=str(method_db.id),
                idea_id=idea_id,
                algorithm_framework=method_db.algorithm_framework,
                key_modules=method_db.key_modules or [],
                data_requirements=method_db.data_requirements or "",
                evaluation_metrics=method_db.evaluation_metrics or [],
                expected_challenges=[],
                innovation_points=[]
            )
            
            # 进度回调
            def progress_callback(current, total, message):
                progress = int(20 + (current / total) * 70)
                tracker.set_progress(progress, message)
            
            # 生成论文草稿
            draft = generator.generate_draft(
                idea=idea,
                method=method,
                progress_callback=progress_callback
            )
            
            tracker.update("Saving paper draft...")
            
            # 保存到数据库
            sections_dict = {}
            for key, section in draft.sections.items():
                sections_dict[key] = {
                    "section_name": section.section_name,
                    "content": section.content,
                    "source_type": section.source_type
                }
            
            db_draft = models.PaperDraftDB(
                project_id=project_id,
                idea_id=idea_id,
                title=draft.title,
                sections=sections_dict
            )
            
            db.add(db_draft)
            db.commit()
            
            # 更新项目状态
            project = db.query(models.ResearchProject).filter(
                models.ResearchProject.id == project_id
            ).first()
            
            if project:
                project.current_step = "draft"
                db.commit()
            
            result = {
                "success": True,
                "draft_id": db_draft.id,
                "sections": list(sections_dict.keys())
            }
            
            logger.info(f"Paper draft completed for project {project_id}: {result}")
            
            return result
    
    except Exception as exc:
        logger.error(f"Paper draft generation failed: {exc}", exc_info=True)
        raise

