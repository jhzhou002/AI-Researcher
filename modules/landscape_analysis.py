"""
研究脉络分析模块
分析文献集合，识别研究方向和空白
"""
import json
from typing import List, Dict
from openai import OpenAI
from models import PaperAnalysis, ResearchLandscape, ResearchCluster
from utils import logger
import config


def analyze_research_landscape(
    papers_analysis: Dict[str, PaperAnalysis],
    api_key: str
) -> ResearchLandscape:
    """
    分析研究脉络
    
    Args:
        papers_analysis: 论文分析结果字典
        api_key: OpenAI API密钥
    
    Returns:
        研究脉络对象
    """
    logger.info(f"Analyzing research landscape from {len(papers_analysis)} papers...")
    
    if not papers_analysis:
        raise ValueError("没有足够的论文分析结果")
    
    # 准备输入数据
    analysis_summary = prepare_analysis_summary(papers_analysis)
    
    # 调用LLM进行分析
    client = OpenAI(api_key=api_key)
    
    prompt = config.PROMPTS["landscape_analysis"].format(
        papers_analysis=analysis_summary
    )
    
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,  # 使用主模型
            messages=[
                {"role": "system", "content": "你是一位学术研究综述专家。请严格按照JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # 构建ResearchLandscape对象
        clusters = []
        for cluster_data in result_json.get("clusters", []):
            cluster = ResearchCluster(
                cluster_name=cluster_data.get("cluster_name", ""),
                papers=cluster_data.get("papers", []),
                key_themes=cluster_data.get("key_themes", []),
                technical_evolution=cluster_data.get("technical_evolution", "")
            )
            clusters.append(cluster)
        
        landscape = ResearchLandscape(
            clusters=clusters,
            solved_problems=result_json.get("solved_problems", []),
            partially_solved=result_json.get("partially_solved", []),
            unsolved_problems=result_json.get("unsolved_problems", []),
            technical_evolution=result_json.get("technical_evolution", {})
        )
        
        logger.info(f"Identified {len(clusters)} research clusters and {len(landscape.unsolved_problems)} unsolved problems")
        return landscape
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise ValueError(f"API返回的不是有效的JSON格式")
    
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise


def prepare_analysis_summary(papers_analysis: Dict[str, PaperAnalysis]) -> str:
    """
    准备论文分析摘要用于LLM输入
    
    Args:
        papers_analysis: 论文分析字典
    
    Returns:
        格式化的摘要文本
    """
    summaries = []
    
    for paper_id, analysis in papers_analysis.items():
        summary = f"""
Paper ID: {paper_id}
核心问题: {analysis.core_problem}
关键方法: {analysis.key_method}
技术路线: {analysis.technical_approach}
贡献点: {', '.join(analysis.contributions)}
局限性: {', '.join(analysis.limitations)}
"""
        summaries.append(summary)
    
    return "\n---\n".join(summaries)


def format_landscape_summary(landscape: ResearchLandscape) -> str:
    """
    格式化研究脉络摘要
    
    Args:
        landscape: 研究脉络对象
    
    Returns:
        Markdown格式的摘要
    """
    sections = ["# 研究脉络分析\n"]
    
    # 研究方向聚类
    sections.append("## 研究方向聚类\n")
    for i, cluster in enumerate(landscape.clusters, 1):
        sections.append(f"### {i}. {cluster.cluster_name}\n")
        sections.append(f"**关键主题**: {', '.join(cluster.key_themes)}\n")
        sections.append(f"**技术演进**: {cluster.technical_evolution}\n")
        sections.append(f"**相关论文数**: {len(cluster.papers)}\n")
    
    # 问题状态
    sections.append("\n## 研究问题状态\n")
    
    if landscape.solved_problems:
        sections.append("### ✅ 已解决的问题\n")
        for problem in landscape.solved_problems:
            sections.append(f"- {problem}\n")
    
    if landscape.partially_solved:
        sections.append("\n### 🔄 半解决的问题\n")
        for problem in landscape.partially_solved:
            sections.append(f"- {problem}\n")
    
    if landscape.unsolved_problems:
        sections.append("\n### ❓ 未解决的问题（按重要性排序）\n")
        for i, problem in enumerate(landscape.unsolved_problems, 1):
            sections.append(f"{i}. {problem}\n")
    
    # 技术演进
    if landscape.technical_evolution:
        sections.append("\n## 技术演进路线\n")
        for direction, evolution in landscape.technical_evolution.items():
            sections.append(f"**{direction}**: {evolution}\n")
    
    return "".join(sections)
