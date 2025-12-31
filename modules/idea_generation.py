"""
研究想法生成模块
基于研究脉络生成创新想法
"""
import json
from typing import List
from openai import OpenAI
from models import ResearchLandscape, ResearchIdea
from utils import logger
import config


def generate_research_ideas(
    landscape: ResearchLandscape,
    api_key: str,
    num_ideas: int = None
) -> List[ResearchIdea]:
    """
    生成研究想法
    
    Args:
        landscape: 研究脉络对象
        api_key: OpenAI API密钥
        num_ideas: 生成想法的数量
    
    Returns:
        研究想法列表
    """
    if num_ideas is None:
        num_ideas = config.MAX_IDEAS_TO_GENERATE
    
    logger.info(f"Generating {num_ideas} research ideas...")
    
    # 准备输入
    landscape_summary = prepare_landscape_input(landscape)
    
    # 调用LLM
    client = OpenAI(api_key=api_key)
    
    prompt = config.PROMPTS["idea_generation"].format(
        landscape=landscape_summary,
        num_ideas=num_ideas
    )
    
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一位富有创新精神的研究者。请严格按照JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # 较高的温度以增加创造性
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # 解析结果
        ideas = []
        ideas_data = result_json.get("ideas", []) if isinstance(result_json, dict) and "ideas" in result_json else result_json if isinstance(result_json, list) else []
        
        for idea_data in ideas_data:
            idea = ResearchIdea(
                idea_id=idea_data.get("idea_id", f"idea_{len(ideas)+1}"),
                motivation=idea_data.get("motivation", ""),
                core_hypothesis=idea_data.get("core_hypothesis", ""),
                expected_contribution=idea_data.get("expected_contribution", ""),
                difference_from_existing=idea_data.get("difference_from_existing", ""),
                feasibility_score=float(idea_data.get("feasibility_score", 0.5)),
                novelty_score=float(idea_data.get("novelty_score", 0.5))
            )
            ideas.append(idea)
        
        logger.info(f"Generated {len(ideas)} research ideas")
        return ideas
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise ValueError(f"API返回的不是有效的JSON格式")
    
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise


def prepare_landscape_input(landscape: ResearchLandscape) -> str:
    """
    准备研究脉络输入
    
    Args:
        landscape: 研究脉络对象
    
    Returns:
        格式化的文本
    """
    sections = []
    
    # 研究方向
    sections.append("## 研究方向聚类")
    for cluster in landscape.clusters:
        sections.append(f"- {cluster.cluster_name}: {', '.join(cluster.key_themes)}")
    
    # 未解决问题
    sections.append("\n## 未解决的研究问题")
    for i, problem in enumerate(landscape.unsolved_problems[:10], 1):  # 只取前10个
        sections.append(f"{i}. {problem}")
    
    # 半解决问题
    if landscape.partially_solved:
        sections.append("\n## 半解决的问题")
        for problem in landscape.partially_solved[:5]:
            sections.append(f"- {problem}")
    
    return "\n".join(sections)


def rank_ideas(ideas: List[ResearchIdea]) -> List[ResearchIdea]:
    """
    对想法进行排序
    
    Args:
        ideas: 研究想法列表
    
    Returns:
        排序后的想法列表
    """
    # 综合评分 = 0.6 * 新颖性 + 0.4 * 可行性
    def score(idea: ResearchIdea) -> float:
        return 0.6 * idea.novelty_score + 0.4 * idea.feasibility_score
    
    sorted_ideas = sorted(ideas, key=score, reverse=True)
    logger.info(f"Ranked {len(sorted_ideas)} ideas")
    
    return sorted_ideas


def format_idea_summary(idea: ResearchIdea, index: int = None) -> str:
    """
    格式化研究想法摘要
    
    Args:
        idea: 研究想法对象
        index: 索引号
    
    Returns:
        Markdown格式的摘要
    """
    sections = []
    
    if index:
        sections.append(f"## 想法 {index}: {idea.idea_id}\n")
    else:
        sections.append(f"## {idea.idea_id}\n")
    
    sections.append(f"**研究动机**: {idea.motivation}\n")
    sections.append(f"**核心假设**: {idea.core_hypothesis}\n")
    sections.append(f"**预期贡献**: {idea.expected_contribution}\n")
    sections.append(f"**与现有方法的区别**: {idea.difference_from_existing}\n")
    sections.append(f"**评分**: 新颖性 {idea.novelty_score:.2f} | 可行性 {idea.feasibility_score:.2f}\n")
    
    return "".join(sections)
