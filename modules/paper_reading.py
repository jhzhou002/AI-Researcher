"""
文献阅读引擎
使用LLM对论文进行结构化分析
"""
import json
from typing import List, Dict
from openai import OpenAI
from models import PaperMetadata, PaperAnalysis
from utils import logger, get_cache_key, save_to_cache, load_from_cache
import config


def analyze_papers(
    papers: List[PaperMetadata],
    api_key: str,
    max_papers: int = None
) -> Dict[str, PaperAnalysis]:
    """
    批量分析论文
    
    Args:
        papers: 论文元数据列表
        api_key: OpenAI API密钥
        max_papers: 最多分析的论文数量
    
    Returns:
        论文ID到分析结果的映射
    """
    if max_papers is None:
        max_papers = config.MAX_PAPERS_TO_ANALYZE
    
    # 限制分析数量
    papers_to_analyze = papers[:max_papers]
    logger.info(f"Analyzing {len(papers_to_analyze)} papers...")
    
    analysis_results = {}
    
    # 批量处理
    for i in range(0, len(papers_to_analyze), config.BATCH_SIZE):
        batch = papers_to_analyze[i:i + config.BATCH_SIZE]
        logger.info(f"Processing batch {i//config.BATCH_SIZE + 1}/{(len(papers_to_analyze)-1)//config.BATCH_SIZE + 1}")
        
        for paper in batch:
            paper_id = paper.arxiv_id or paper.title
            
            # 检查缓存
            cache_key = get_cache_key({'paper_id': paper_id, 'title': paper.title})
            cached_analysis = load_from_cache(cache_key, cache_type="analysis")
            
            if cached_analysis:
                analysis_results[paper_id] = PaperAnalysis(**cached_analysis)
                logger.info(f"Loaded analysis from cache: {paper.title[:50]}...")
                continue
            
            # 分析论文
            try:
                analysis = analyze_single_paper(paper, api_key)
                analysis_results[paper_id] = analysis
                
                # 保存到缓存
                save_to_cache(cache_key, analysis.to_dict(), cache_type="analysis")
                logger.info(f"Analyzed: {paper.title[:50]}...")
                
            except Exception as e:
                logger.error(f"Failed to analyze paper {paper.title}: {e}")
                continue
    
    logger.info(f"Successfully analyzed {len(analysis_results)} papers")
    return analysis_results


def analyze_single_paper(paper: PaperMetadata, api_key: str) -> PaperAnalysis:
    """
    分析单篇论文
    
    Args:
        paper: 论文元数据
        api_key: OpenAI API密钥
    
    Returns:
        论文分析结果
    """
    client = OpenAI(api_key=api_key)
    
    # 构建提示词
    prompt = config.PROMPTS["paper_analysis"].format(
        title=paper.title,
        authors=", ".join(paper.authors[:5]),
        abstract=paper.abstract
    )
    
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL_MINI,  # 使用轻量模型节省成本
            messages=[
                {"role": "system", "content": "你是一位专业的学术研究分析专家。请严格按照JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # 创建PaperAnalysis对象
        paper_id = paper.arxiv_id or paper.title
        analysis = PaperAnalysis(
            paper_id=paper_id,
            core_problem=result_json.get("core_problem", ""),
            key_method=result_json.get("key_method", ""),
            technical_approach=result_json.get("technical_approach", ""),
            experiment_conclusions=result_json.get("experiment_conclusions", []),
            limitations=result_json.get("limitations", []),
            contributions=result_json.get("contributions", [])
        )
        
        return analysis
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise ValueError(f"API返回的不是有效的JSON格式")
    
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise


def summarize_paper_analysis(analysis: PaperAnalysis) -> str:
    """
    生成论文分析摘要
    
    Args:
        analysis: 论文分析结果
    
    Returns:
        摘要文本
    """
    summary_parts = [
        f"**核心问题**: {analysis.core_problem}",
        f"**关键方法**: {analysis.key_method}",
        f"**技术路线**: {analysis.technical_approach}",
    ]
    
    if analysis.contributions:
        summary_parts.append(f"**主要贡献**: {'; '.join(analysis.contributions)}")
    
    if analysis.limitations:
        summary_parts.append(f"**局限性**: {'; '.join(analysis.limitations)}")
    
    return "\n\n".join(summary_parts)
