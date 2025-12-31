"""
方法设计模块
将研究想法转化为具体方法框架
"""
import json
from openai import OpenAI
from models import ResearchIdea, MethodDesign
from utils import logger
import config


def design_method(idea: ResearchIdea, api_key: str) -> MethodDesign:
    """
    设计研究方法
    
    Args:
        idea: 研究想法对象
        api_key: OpenAI API密钥
    
    Returns:
        方法设计对象
    """
    logger.info(f"Designing method for idea: {idea.idea_id}")
    
    # 准备想法描述
    idea_description = format_idea_for_design(idea)
    
    # 调用LLM
    client = OpenAI(api_key=api_key)
    
    prompt = config.PROMPTS["method_design"].format(idea=idea_description)
    
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一位算法设计专家。请严格按照JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # 构建MethodDesign对象
        method = MethodDesign(
            idea_id=idea.idea_id,
            overview=result_json.get("overview", ""),
            model_framework=result_json.get("model_framework", ""),
            modules=result_json.get("modules", []),
            baseline_differences=result_json.get("baseline_differences", []),
            theoretical_justification=result_json.get("theoretical_justification", "")
        )
        
        logger.info(f"Method designed with {len(method.modules)} modules")
        return method
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise ValueError(f"API返回的不是有效的JSON格式")
    
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise


def format_idea_for_design(idea: ResearchIdea) -> str:
    """
    格式化研究想法用于方法设计
    
    Args:
        idea: 研究想法对象
    
    Returns:
        格式化的文本
    """
    return f"""
想法ID: {idea.idea_id}
研究动机: {idea.motivation}
核心假设: {idea.core_hypothesis}
预期贡献: {idea.expected_contribution}
与现有方法的区别: {idea.difference_from_existing}
"""


def format_method_summary(method: MethodDesign) -> str:
    """
    格式化方法设计摘要
    
    Args:
        method: 方法设计对象
    
    Returns:
        Markdown格式的摘要
    """
    sections = ["# 方法设计\n"]
    
    sections.append(f"## 方法概述\n{method.overview}\n")
    sections.append(f"\n## 模型框架\n{method.model_framework}\n")
    
    sections.append("\n## 核心模块\n")
    for i, module in enumerate(method.modules, 1):
        sections.append(f"### {i}. {module.get('name', 'Module')}\n")
        sections.append(f"**功能**: {module.get('function', '')}\n")
        sections.append(f"**描述**: {module.get('description', '')}\n")
    
    if method.baseline_differences:
        sections.append("\n## 与Baseline的差异\n")
        for diff in method.baseline_differences:
            sections.append(f"- {diff}\n")
    
    sections.append(f"\n## 理论依据\n{method.theoretical_justification}\n")
    
    return "".join(sections)
