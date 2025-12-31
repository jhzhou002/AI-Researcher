"""
文献检索相关的Celery任务
"""
from backend.tasks.celery_app import celery_app
from backend.tasks.base import DatabaseTask, ProgressTracker
from backend.db.database import SessionLocal
from backend.db import models
from modules.multi_source_search import (
    search_multi_source, merge_and_deduplicate, calculate_cross_source_relevance
)
from models import ResearchIntent, JournalLevel, PaperType, ResearchField
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="literature.discovery",
    max_retries=2,
    default_retry_delay=30
)
def literature_discovery_task(self, project_id: int, max_results: int = 50):
    """
    文献检索异步任务
    
    Args:
        project_id: 研究项目ID
        max_results: 最大结果数
    
    Returns:
        dict: 包含检索结果的字典
    """
    task_id = self.request.id
    tracker = ProgressTracker(self, task_id, total_steps=6)
    
    try:
        with SessionLocal() as db:
            # 步骤1: 获取项目
            tracker.set_progress(5, "Loading project...")
            
            project = db.query(models.ResearchProject).filter(
                models.ResearchProject.id == project_id
            ).first()
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # 步骤2: 更新任务状态为运行中
            tracker.set_progress(10, "Initializing search...")
            self.update_task_status(
                task_id=task_id,
                status="running"
            )
            
            # 步骤3: 构建研究意图
            tracker.set_progress(15, "Building research intent...")
            
            intent = ResearchIntent(
                keywords=project.keywords,
                year_start=project.year_start,
                year_end=project.year_end,
                journal_level=JournalLevel(project.journal_level) if project.journal_level else JournalLevel.ANY,
                paper_type=PaperType(project.paper_type) if project.paper_type else PaperType.ANY,
                field=ResearchField(project.field) if project.field else ResearchField.ANY
            )
            
            # 步骤4: 多源检索
            tracker.set_progress(20, "Searching ArXiv and Semantic Scholar...")
            
            multi_results = search_multi_source(
                intent,
                max_results_per_source=max_results // 2,
                sources=["arxiv", "semantic_scholar"]
            )
            
            # 步骤5: 合并去重
            tracker.set_progress(60, "Merging and deduplicating results...")
            
            papers = merge_and_deduplicate(multi_results)
            logger.info(f"Found {len(papers)} papers after deduplication")
            
            # 步骤6: 计算相关度
            tracker.set_progress(75, "Calculating relevance scores...")
            
            papers = calculate_cross_source_relevance(papers, intent)
            
            # 步骤7: 保存到数据库
            tracker.set_progress(85, "Saving to database...")
            
            saved_count = 0
            for paper in papers[:max_results]:
                db_paper = models.Paper(
                    project_id=project_id,
                    title=paper.title,
                    authors=paper.authors,
                    abstract=paper.abstract,
                    url=paper.url,
                    published=paper.published,
                    paper_type=paper.paper_type.value if paper.paper_type else None,
                    journal=paper.journal,
                    relevance_score=paper.relevance_score,
                    arxiv_id=paper.arxiv_id
                )
                db.add(db_paper)
                saved_count += 1
            
            db.commit()
            
            # 更新项目状态
            project.current_step = "discovery"
            db.commit()
            
            # 完成
            tracker.set_progress(100, "Discovery completed!")
            
            result = {
                "success": True,
                "papers_found": len(papers),
                "papers_saved": saved_count,
                "sources_used": list(multi_results.keys()),
                "avg_relevance": sum(p.relevance_score for p in papers[:saved_count]) / saved_count if saved_count > 0 else 0
            }
            
            logger.info(f"Literature discovery completed for project {project_id}: {result}")
            
            return result
    
    except Exception as exc:
        logger.error(f"Literature discovery failed: {exc}", exc_info=True)
        # Celery会自动调用on_failure
        raise


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="literature.fetch_pdf",
    max_retries=3,
    default_retry_delay=60
)
def fetch_pdf_task(self, paper_id: int):
    """
    获取论文PDF（未来实现）
    
    Args:
        paper_id: 论文ID
    
    Returns:
        dict: PDF下载信息
    """
    task_id = self.request.id
    
    try:
        with SessionLocal() as db:
            paper = db.query(models.Paper).filter(
                models.Paper.id == paper_id
            ).first()
            
            if not paper:
                raise ValueError(f"Paper {paper_id} not found")
            
            # TODO: 实现PDF下载逻辑
            # 1. 从ArXiv下载
            # 2. 从Semantic Scholar获取开放获取PDF
            # 3. 保存到本地存储
            
            logger.info(f"PDF fetch task for paper {paper_id} (not yet implemented)")
            
            return {
                "success": False,
                "message": "PDF fetch not yet implemented"
            }
    
    except Exception as exc:
        logger.error(f"PDF fetch failed: {exc}")
        raise
