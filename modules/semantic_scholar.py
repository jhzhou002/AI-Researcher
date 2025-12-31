"""
Semantic Scholar文献检索接口
"""
import requests
from typing import List, Optional, Dict, Any
from models import PaperMetadata, PaperType
from utils import logger
import time


class SemanticScholarAPI:
    """Semantic Scholar API封装"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Semantic Scholar API客户端
        
        Args:
            api_key: API密钥（可选，但建议使用以避免速率限制）
        """
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"x-api-key": api_key})
    
    def search_papers(
        self,
        query: str,
        limit: int = 100,
        fields: List[str] = None,
        year_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索论文
        
        Args:
            query: 搜索查询
            limit: 最大结果数
            fields: 要返回的字段
            year_range: 年份范围 (start_year, end_year)
        
        Returns:
            论文列表
        """
        if fields is None:
            fields = [
                "paperId", "title", "abstract", "authors", "year",
                "publicationDate", "venue", "citationCount",
                "influentialCitationCount", "isOpenAccess", "openAccessPdf",
                "externalIds"
            ]
        
        url = f"{self.BASE_URL}/paper/search"
        
        params = {
            "query": query,
            "limit": min(limit, 100),  # API限制
            "fields": ",".join(fields)
        }
        
        # 添加年份过滤
        if year_range:
            params["year"] = f"{year_range[0]}-{year_range[1]}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            papers = data.get("data", [])
            
            logger.info(f"Semantic Scholar: Found {len(papers)} papers")
            
            # 处理分页（如果需要更多结果）
            total = data.get("total", 0)
            offset = len(papers)
            
            while offset < limit and offset < total:
                time.sleep(0.5)  # 避免速率限制
                
                params["offset"] = offset
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                batch = data.get("data", [])
                
                if not batch:
                    break
                
                papers.extend(batch)
                offset += len(batch)
                
                logger.debug(f"Fetched {len(papers)}/{min(limit, total)} papers")
            
            return papers[:limit]
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Semantic Scholar API error: {e}")
            return []
    
    def get_paper_details(self, paper_id: str, fields: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取单篇论文详情
        
        Args:
            paper_id: 论文ID
            fields: 要返回的字段
        
        Returns:
            论文详情
        """
        if fields is None:
            fields = ["paperId", "title", "abstract", "authors", "year", "venue"]
        
        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {"fields": ",".join(fields)}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get paper {paper_id}: {e}")
            return None


def convert_s2_to_metadata(s2_paper: Dict[str, Any]) -> PaperMetadata:
    """
    将Semantic Scholar论文转换为PaperMetadata
    
    Args:
        s2_paper: S2论文数据
    
    Returns:
        PaperMetadata对象
    """
    # 提取作者
    authors = []
    for author in s2_paper.get("authors", []):
        name = author.get("name", "Unknown")
        authors.append(name)
    
    # 确定论文类型（基于标题和摘要）
    title = s2_paper.get("title", "")
    abstract = s2_paper.get("abstract", "")
    paper_type = detect_paper_type_from_text(title, abstract)
    
    # 构建URL
    url = None
    if s2_paper.get("isOpenAccess") and s2_paper.get("openAccessPdf"):
        url = s2_paper["openAccessPdf"].get("url")
    elif s2_paper.get("externalIds"):
        # 尝试构建ArXiv或DOI URL
        ext_ids = s2_paper["externalIds"]
        if "ArXiv" in ext_ids:
            url = f"https://arxiv.org/abs/{ext_ids['ArXiv']}"
        elif "DOI" in ext_ids:
            url = f"https://doi.org/{ext_ids['DOI']}"
    
    # 发表日期
    pub_date = s2_paper.get("publicationDate") or str(s2_paper.get("year", ""))
    
    # 创建元数据对象
    metadata = PaperMetadata(
        title=title,
        authors=authors,
        abstract=abstract or "",
        url=url or f"https://www.semanticscholar.org/paper/{s2_paper.get('paperId', '')}",
        published=pub_date,
        paper_type=paper_type,
        journal=s2_paper.get("venue"),
        relevance_score=0.0,  # 后续计算
        arxiv_id=s2_paper.get("externalIds", {}).get("ArXiv")
    )
    
    return metadata


def detect_paper_type_from_text(title: str, abstract: str) -> PaperType:
    """
    从标题和摘要检测论文类型
    
    Args:
        title: 标题
        abstract: 摘要
    
    Returns:
        论文类型
    """
    text = (title + " " + abstract).lower()
    
    survey_keywords = [
        "survey", "review", "overview", "tutorial", "综述",
        "state of the art", "state-of-the-art", "systematic review"
    ]
    
    for keyword in survey_keywords:
        if keyword in text:
            return PaperType.SURVEY
    
    return PaperType.RESEARCH


def search_semantic_scholar(
    query: str,
    max_results: int = 50,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    api_key: Optional[str] = None
) -> List[PaperMetadata]:
    """
    使用Semantic Scholar搜索论文
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
        year_start: 起始年份
        year_end: 结束年份
        api_key: API密钥
    
    Returns:
        论文元数据列表
    """
    api = SemanticScholarAPI(api_key)
    
    year_range = None
    if year_start and year_end:
        year_range = (year_start, year_end)
    elif year_start:
        import datetime
        year_range = (year_start, datetime.datetime.now().year)
    
    # 搜索论文
    s2_papers = api.search_papers(query, limit=max_results, year_range=year_range)
    
    # 转换为元数据
    papers = []
    for s2_paper in s2_papers:
        try:
            metadata = convert_s2_to_metadata(s2_paper)
            papers.append(metadata)
        except Exception as e:
            logger.warning(f"Failed to convert S2 paper: {e}")
            continue
    
    logger.info(f"Converted {len(papers)} papers from Semantic Scholar")
    
    return papers
