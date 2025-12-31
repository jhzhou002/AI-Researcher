"""
文献分析相关的Celery任务
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
    name="analysis.papers",
    max_retries=2,
    default_retry_delay=60
)
def paper_analysis_task(self, project_id: int, max_papers: int = 20):
    """
    批量分析文献
    
    Args:
        project_id: 研究项目ID
        max_papers: 最大分析数量
    
    Returns:
        dict: 分析结果统计
    """
    task_id = self.request.id
    
    try:
        with SessionLocal() as db:
            # 更新任务状态
            self.update_task_status(task_id=task_id, status="running", progress=5)
            
            # 获取项目
            project = db.query(models.ResearchProject).filter(
                models.ResearchProject.id == project_id
            ).first()
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # 获取文献（按相关度排序）
            papers = db.query(models.Paper).filter(
                models.Paper.project_id == project_id
            ).order_by(
                models.Paper.relevance_score.desc()
            ).limit(max_papers).all()
            
            if not papers:
                raise ValueError("No papers found for analysis")
            
            logger.info(f"Analyzing {len(papers)} papers for project {project_id}")
            
            # 创建进度追踪器
            total_steps = len(papers) + 2
            tracker = ProgressTracker(self, task_id, total_steps)
            
            tracker.update("Loading LLM and business modules...")
            
            # 导入业务模块
            from modules.paper_reading_engine import PaperReadingEngine
            from llm.manager import llm_manager
            
            reading_engine = PaperReadingEngine(llm_manager=llm_manager)
            
            # 分析每篇论文
            analyzed_count = 0
            for i, paper in enumerate(papers):
                tracker.update(f"Analyzing paper {i+1}/{len(papers)}: {paper.title[:50]}...")
                
                try:
                    # 调用LLM分析
                    analysis_result = reading_engine.analyze_paper(
                        title=paper.title,
                        abstract=paper.abstract or "",
                        full_text=""  # TODO: 如果有PDF可以传入全文
                    )
                    
                    # 保存分析结果
                    db_analysis = models.PaperAnalysisDB(
                        project_id=project_id,
                        paper_id=paper.id,
                        core_problem=analysis_result.core_problem,
                        key_method=analysis_result.key_method,
                        technical_approach=analysis_result.technical_approach,
                        experiment_conclusions=analysis_result.experiment_conclusions,
                        limitations=analysis_result.limitations,
                        contributions=analysis_result.contributions
                    )
                    
                    db.add(db_analysis)
                    db.commit()
                    
                    analyzed_count += 1
                    logger.info(f"Successfully analyzed paper {paper.id}: {paper.title[:50]}")
                
                except Exception as e:
                    logger.error(f"Failed to analyze paper {paper.id}: {e}")
                    # 继续分析下一篇
                    continue
            
            # 更新项目状态
            tracker.update("Updating project status...")
            project.current_step = "analysis"
            db.commit()
            
            result = {
                "success": True,
                "papers_analyzed": analyzed_count,
                "total_papers": len(papers),
                "success_rate": analyzed_count / len(papers) if papers else 0
            }
            
            logger.info(f"Paper analysis completed for project {project_id}: {result}")
            
            return result
    
    except Exception as exc:
        logger.error(f"Paper analysis failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="analysis.landscape",
    max_retries=2,
    default_retry_delay=60
)
def landscape_analysis_task(self, project_id: int):
    """
    研究脉络分析
    
    Args:
        project_id: 研究项目ID
    
    Returns:
        dict: 分析结果
    """
    task_id = self.request.id
    tracker = ProgressTracker(self, task_id, total_steps=5)
    
    try:
        with SessionLocal() as db:
            # 更新任务状态
            self.update_task_status(task_id=task_id, status="running")
            
            tracker.update("Loading paper analyses...")
            
            # 获取所有文献分析结果
            analyses = db.query(models.PaperAnalysisDB).filter(
                models.PaperAnalysisDB.project_id == project_id
            ).all()
            
            if not analyses:
                raise ValueError("No paper analyses found. Please run paper analysis first.")
            
            logger.info(f"Found {len(analyses)} paper analyses for landscape analysis")
            
            tracker.update("Clustering papers by research direction...")
            
            # 导入业务模块
            from modules.landscape_analyzer import ResearchLandscapeAnalyzer
            from llm.manager import llm_manager
            
            analyzer = ResearchLandscapeAnalyzer(llm_manager=llm_manager)
            
            # 转换数据库模型为业务模型
            from models import PaperAnalysis
            business_analyses = []
            for db_analysis in analyses:
                business_analysis = PaperAnalysis(
                    paper_id=db_analysis.paper_id,
                    core_problem=db_analysis.core_problem,
                    key_method=db_analysis.key_method,
                    technical_approach=db_analysis.technical_approach,
                    experiment_conclusions=db_analysis.experiment_conclusions,
                    limitations=db_analysis.limitations,
                    contributions=db_analysis.contributions
                )
                business_analyses.append(business_analysis)
            
            tracker.update("Analyzing research landscape...")
            
            # 执行脉络分析
            landscape = analyzer.analyze_landscape(business_analyses)
            
            tracker.update("Saving results...")
            
            # 保存结果
            db_landscape = models.ResearchLandscapeDB(
                project_id=project_id,
                clusters=landscape.clusters,
                solved_problems=landscape.solved_problems,
                partially_solved=landscape.partially_solved,
                unsolved_problems=landscape.unsolved_problems,
                technical_evolution=landscape.technical_evolution
            )
            
            db.add(db_landscape)
            db.commit()
            
            # 更新项目状态
            project = db.query(models.ResearchProject).filter(
                models.ResearchProject.id == project_id
            ).first()
            
            if project:
                project.current_step = "landscape"
                db.commit()
            
            result = {
                "success": True,
                "clusters": len(landscape.clusters),
                "unsolved_problems": len(landscape.unsolved_problems)
            }
            
            logger.info(f"Landscape analysis completed for project {project_id}: {result}")
            
            return result
    
    except Exception as exc:
        logger.error(f"Landscape analysis failed: {exc}", exc_info=True)
        raise
