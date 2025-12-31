"""
文献检索模块
支持多源文献搜索和智能过滤
"""
import arxiv
from typing import List, Optional
from models import ResearchIntent, PaperMetadata, PaperType
from utils import logger, get_cache_key, save_to_cache, load_from_cache
import config
from datetime import datetime


def search_papers(intent: ResearchIntent, max_results: int = None) -> List[PaperMetadata]:
    """
    根据研究意图搜索文献
    
    Args:
        intent: 研究意图对象
        max_results: 最大结果数量
    
    Returns:
        文献元数据列表
    """
    if max_results is None:
        max_results = config.ARXIV_MAX_RESULTS
    
    # 检查缓存
    cache_key = get_cache_key({
        'keywords': intent.keywords,
        'year_start': intent.year_start,
        'year_end': intent.year_end,
        'max_results': max_results
    })
    
    cached_results = load_from_cache(cache_key, cache_type="papers")
    if cached_results:
        logger.info(f"Loaded {len(cached_results)} papers from cache")
        return [PaperMetadata(**p) for p in cached_results]
    
    # 搜索ArXiv
    papers = search_arxiv(intent, max_results)
    
    # 应用过滤
    filtered_papers = filter_papers(papers, intent)
    
    # 计算相关度评分
    scored_papers = score_relevance(filtered_papers, intent)
    
    # 排序
    sorted_papers = sorted(scored_papers, key=lambda p: p.relevance_score, reverse=True)
    
    # 保存到缓存
    save_to_cache(cache_key, [p.to_dict() for p in sorted_papers], cache_type="papers")
    
    logger.info(f"Found {len(sorted_papers)} papers after filtering")
    return sorted_papers


def search_arxiv(intent: ResearchIntent, max_results: int) -> List[PaperMetadata]:
    """
    搜索ArXiv
    
    Args:
        intent: 研究意图
        max_results: 最大结果数
    
    Returns:
        论文元数据列表
    """
    query = build_arxiv_query(intent)
    logger.info(f"Searching ArXiv with query: {query}")
    
    # 临时禁用代理（ArXiv不需要代理，且代理可能导致SSL错误）
    import os
    old_http_proxy = os.environ.get('HTTP_PROXY')
    old_https_proxy = os.environ.get('HTTPS_PROXY')
    old_http_proxy_lower = os.environ.get('http_proxy')
    old_https_proxy_lower = os.environ.get('https_proxy')
    
    try:
        # 清除代理设置
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            if key in os.environ:
                del os.environ[key]
        
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        for result in client.results(search):
            # 提取ArXiv ID
            arxiv_id = result.entry_id.split('/')[-1]
            
            paper = PaperMetadata(
                title=result.title,
                authors=[author.name for author in result.authors],
                abstract=result.summary,
                url=result.pdf_url,
                published=result.published.strftime("%Y-%m-%d"),
                arxiv_id=arxiv_id,
                relevance_score=0.0  # 初始化，后续计算
            )
            papers.append(paper)
        
        logger.info(f"Retrieved {len(papers)} papers from ArXiv")
        return papers
            
    except Exception as e:
        logger.error(f"Error searching ArXiv: {e}")
        raise
    finally:
        # 恢复代理设置
        if old_http_proxy:
            os.environ['HTTP_PROXY'] = old_http_proxy
        if old_https_proxy:
            os.environ['HTTPS_PROXY'] = old_https_proxy
        if old_http_proxy_lower:
            os.environ['http_proxy'] = old_http_proxy_lower
        if old_https_proxy_lower:
            os.environ['https_proxy'] = old_https_proxy_lower


def build_arxiv_query(intent: ResearchIntent) -> str:
    """
    构建ArXiv查询字符串
    
    Args:
        intent: 研究意图
    
    Returns:
        查询字符串
    """
    query_parts = [intent.keywords]
    
    # 添加学科分类（如果指定）
    field_mapping = {
        "cv": "cs.CV",
        "nlp": "cs.CL",
        "ml": "cs.LG",
        "systems": "cs.DC OR cs.OS",
    }
    
    if intent.field.value != "any" and intent.field.value in field_mapping:
        query_parts.append(f"cat:{field_mapping[intent.field.value]}")
    
    query = " AND ".join(query_parts)
    return query


def filter_papers(papers: List[PaperMetadata], intent: ResearchIntent) -> List[PaperMetadata]:
    """
    根据意图过滤论文
    
    Args:
        papers: 论文列表
        intent: 研究意图
    
    Returns:
        过滤后的论文列表
    """
    filtered = []
    
    for paper in papers:
        # 年份过滤
        if intent.year_start or intent.year_end:
            try:
                year = int(paper.published.split('-')[0])
                if intent.year_start and year < intent.year_start:
                    continue
                if intent.year_end and year > intent.year_end:
                    continue
            except:
                pass
        
        # 文献类型过滤
        if intent.paper_type != PaperType.ANY:
            paper_type = detect_paper_type(paper)
            paper.paper_type = paper_type
            if paper_type != intent.paper_type and intent.paper_type != PaperType.ANY:
                continue
        
        filtered.append(paper)
    
    return filtered


def detect_paper_type(paper: PaperMetadata) -> PaperType:
    """
    检测论文类型（综述或研究）
    
    Args:
        paper: 论文元数据
    
    Returns:
        论文类型
    """
    # 简单的启发式规则
    title_lower = paper.title.lower()
    abstract_lower = paper.abstract.lower()
    
    survey_keywords = ['survey', 'review', 'overview', 'tutorial', '综述']
    
    for keyword in survey_keywords:
        if keyword in title_lower:
            return PaperType.SURVEY
    
    # 检查摘要中是否有大量综述特征
    survey_count = sum(1 for kw in survey_keywords if kw in abstract_lower)
    if survey_count >= 2:
        return PaperType.SURVEY
    
    return PaperType.RESEARCH


def score_relevance(papers: List[PaperMetadata], intent: ResearchIntent) -> List[PaperMetadata]:
    """
    计算论文相关度评分
    
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
        abstract_lower = paper.abstract.lower()
        
        # 标题匹配（权重更高）
        for keyword in keywords:
            if keyword in title_lower:
                score += 0.3
        
        # 摘要匹配
        for keyword in keywords:
            if keyword in abstract_lower:
                score += 0.1
        
        # 类型匹配奖励
        if intent.paper_type != PaperType.ANY and paper.paper_type == intent.paper_type:
            score += 0.2
        
        # 时间新近性奖励
        try:
            year = int(paper.published.split('-')[0])
            current_year = datetime.now().year
            recency = 1.0 - (current_year - year) / 10.0  # 10年衰减
            score += max(0, recency * 0.1)
        except:
            pass
        
        paper.relevance_score = min(1.0, score)  # 归一化到[0, 1]
    
    return papers


def deduplicate_papers(papers: List[PaperMetadata]) -> List[PaperMetadata]:
    """
    去重论文（处理ArXiv版本和期刊版本）
    
    Args:
        papers: 论文列表
    
    Returns:
        去重后的论文列表
    """
    seen_titles = set()
    unique_papers = []
    
    for paper in papers:
        # 简单的标题相似度去重
        title_normalized = paper.title.lower().strip()
        
        if title_normalized not in seen_titles:
            seen_titles.add(title_normalized)
            unique_papers.append(paper)
        else:
            logger.debug(f"Duplicate paper filtered: {paper.title}")
    
    logger.info(f"Deduplicated: {len(papers)} -> {len(unique_papers)} papers")
    return unique_papers
