"""
多源文献检索 - 统一入口
整合ArXiv、Semantic Scholar等多个数据源
"""
from typing import List, Optional, Dict
from models import ResearchIntent, PaperMetadata
from modules.literature_discovery import search_arxiv
from modules.semantic_scholar import search_semantic_scholar
from utils import logger
import os


def search_multi_source(
    intent: ResearchIntent,
    max_results_per_source: int = 50,
    sources: List[str] = None
) -> Dict[str, List[PaperMetadata]]:
    """
    从多个数据源检索文献
    
    Args:
        intent: 研究意图
        max_results_per_source: 每个源的最大结果数
        sources: 要使用的数据源列表（默认使用所有）
    
    Returns:
        {source_name: papers}的字典
    """
    if sources is None:
        sources = ["arxiv", "semantic_scholar"]
    
    results = {}
    
    # ArXiv
    if "arxiv" in sources:
        logger.info("Searching ArXiv...")
        try:
            arxiv_papers = search_arxiv(intent, max_results_per_source)
            results["arxiv"] = arxiv_papers
            logger.info(f"ArXiv: Found {len(arxiv_papers)} papers")
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            results["arxiv"] = []
    
    # Semantic Scholar
    if "semantic_scholar" in sources:
        logger.info("Searching Semantic Scholar...")
        try:
            s2_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
            s2_papers = search_semantic_scholar(
                query=intent.keywords,
                max_results=max_results_per_source,
                year_start=intent.year_start,
                year_end=intent.year_end,
                api_key=s2_api_key
            )
            results["semantic_scholar"] = s2_papers
            logger.info(f"Semantic Scholar: Found {len(s2_papers)} papers")
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            results["semantic_scholar"] = []
    
    # TODO: 添加更多数据源
    # - PubMed
    # - Google Scholar
    # - IEEE Xplore
    
    return results


def merge_and_deduplicate(
    multi_source_results: Dict[str, List[PaperMetadata]]
) -> List[PaperMetadata]:
    """
    合并多源结果并去重
    
    Args:
        multi_source_results: 多源检索结果
    
    Returns:
        去重后的论文列表
    """
    # 收集所有论文
    all_papers = []
    for source, papers in multi_source_results.items():
        for paper in papers:
            all_papers.append((source, paper))
    
    logger.info(f"Total papers before deduplication: {len(all_papers)}")
    
    # 去重策略：
    # 1. 优先使用ArXiv ID匹配
    # 2. 使用标题相似度匹配
    # 3. DOI匹配
    
    seen_arxiv_ids = set()
    seen_titles = {}
    unique_papers = []
    
    for source, paper in all_papers:
        # 检查ArXiv ID
        if paper.arxiv_id:
            if paper.arxiv_id in seen_arxiv_ids:
                logger.debug(f"Duplicate by ArXiv ID: {paper.arxiv_id}")
                continue
            seen_arxiv_ids.add(paper.arxiv_id)
        
        # 检查标题
        title_norm = normalize_title(paper.title)
        
        if title_norm in seen_titles:
            # 已存在，选择信息更完整的
            existing_source, existing_paper = seen_titles[title_norm]
            
            # 优先级：arxiv > semantic_scholar > others
            source_priority = {"arxiv": 3, "semantic_scholar": 2}
            existing_priority = source_priority.get(existing_source, 1)
            current_priority = source_priority.get(source, 1)
            
            if current_priority > existing_priority:
                # 替换为当前论文
                unique_papers = [p for p in unique_papers if p != existing_paper]
                unique_papers.append(paper)
                seen_titles[title_norm] = (source, paper)
                logger.debug(f"Replaced paper from {existing_source} with {source}")
            else:
                logger.debug(f"Duplicate by title: {title_norm[:50]}...")
            
            continue
        
        seen_titles[title_norm] = (source, paper)
        unique_papers.append(paper)
    
    logger.info(f"Papers after deduplication: {len(unique_papers)}")
    
    return unique_papers


def normalize_title(title: str) -> str:
    """
    标准化标题用于匹配
    
    Args:
        title: 原始标题
    
    Returns:
        标准化后的标题
    """
    # 转小写
    title = title.lower()
    
    # 移除标点和多余空格
    import re
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title)
    title = title.strip()
    
    return title


def calculate_cross_source_relevance(
    papers: List[PaperMetadata],
    intent: ResearchIntent
) -> List[PaperMetadata]:
    """
    计算跨源综合相关度评分
    
    Args:
        papers: 论文列表
        intent: 研究意图
    
    Returns:
        带评分的论文列表
    """
    keywords = intent.keywords.lower().split()
    
    for paper in papers:
        score = 0.0
        
        title_lower = paper.title.lower()
        abstract_lower = (paper.abstract or "").lower()
        
        # 标题匹配（权重高）
        for keyword in keywords:
            if keyword in title_lower:
                score += 0.3
        
        # 摘要匹配
        for keyword in keywords:
            if keyword in abstract_lower:
                score += 0.1
        
        # 类型匹配
        if intent.paper_type.value != "any":
            if paper.paper_type and paper.paper_type.value == intent.paper_type.value:
                score += 0.2
        
        # 时间新近性
        if paper.published:
            try:
                year = int(paper.published.split('-')[0])
                from datetime import datetime
                current_year = datetime.now().year
                recency = 1.0 - (current_year - year) / 10.0
                score += max(0, recency * 0.15)
            except:
                pass
        
        # Arxiv论文额外加分（通常更新、开放获取）
        if paper.arxiv_id:
            score += 0.05
        
        paper.relevance_score = min(1.0, score)
    
    # 按相关度排序
    papers.sort(key=lambda p: p.relevance_score, reverse=True)
    
    return papers
