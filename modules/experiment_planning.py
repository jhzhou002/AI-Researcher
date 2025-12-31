"""
实验设计模块
为研究方法设计实验方案
"""
import json
from openai import OpenAI
from models import MethodDesign, ExperimentPlan
from utils import logger
import config


def design_experiments(method: MethodDesign, api_key: str) -> ExperimentPlan:
    """
    设计实验方案
    
    Args:
        method: 方法设计对象
        api_key: OpenAI API密钥
    
    Returns:
        实验设计对象
    """
    logger.info(f"Designing experiments for method: {method.idea_id}")
    
    # 准备方法描述
    method_description = format_method_for_experiment(method)
    
    # 调用LLM
    client = OpenAI(api_key=api_key)
    
    prompt = config.PROMPTS["experiment_design"].format(method=method_description)
    
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一位实验设计专家。请严格按照JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # 构建ExperimentPlan对象
        experiment = ExperimentPlan(
            method_id=method.idea_id,
            experiment_setup=result_json.get("experiment_setup", ""),
            baselines=result_json.get("baselines", []),
            ablation_studies=result_json.get("ablation_studies", []),
            expected_results=result_json.get("expected_results", {}),
            metrics=result_json.get("metrics", []),
            risk_factors=result_json.get("risk_factors", []),
            is_hypothetical=True  # 明确标记为假设性结果
        )
        
        logger.info(f"Experiment designed with {len(experiment.baselines)} baselines and {len(experiment.ablation_studies)} ablation studies")
        return experiment
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise ValueError(f"API返回的不是有效的JSON格式")
    
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise


def format_method_for_experiment(method: MethodDesign) -> str:
    """
    格式化方法设计用于实验设计
    
    Args:
        method: 方法设计对象
    
    Returns:
        格式化的文本
    """
    sections = [
        f"方法概述: {method.overview}",
        f"模型框架: {method.model_framework}",
    ]
    
    sections.append("核心模块:")
    for module in method.modules:
        sections.append(f"- {module.get('name')}: {module.get('function')}")
    
    sections.append("与baseline的差异:")
    for diff in method.baseline_differences:
        sections.append(f"- {diff}")
    
    return "\n".join(sections)


def format_experiment_summary(experiment: ExperimentPlan) -> str:
    """
    格式化实验设计摘要
    
    Args:
        experiment: 实验设计对象
    
    Returns:
        Markdown格式的摘要
    """
    sections = ["# 实验设计\n"]
    
    if experiment.is_hypothetical:
        sections.append("> ⚠️ **注意**: 以下实验结果为假设性分析，需要实际实验验证。\n\n")
    
    sections.append(f"## 实验设置\n{experiment.experiment_setup}\n")
    
    sections.append("\n## Baseline方法\n")
    for i, baseline in enumerate(experiment.baselines, 1):
        sections.append(f"{i}. {baseline}\n")
    
    sections.append("\n## 评估指标\n")
    for metric in experiment.metrics:
        sections.append(f"- {metric}\n")
    
    if experiment.ablation_studies:
        sections.append("\n## Ablation Study设计\n")
        sections.append("| 移除组件 | 测试目的 |\n")
        sections.append("|---------|----------|\n")
        for study in experiment.ablation_studies:
            sections.append(f"| {study.get('component', '')} | {study.get('purpose', '')} |\n")
    
    if experiment.expected_results:
        sections.append("\n## 预期结果分析（假设）\n")
        for key, value in experiment.expected_results.items():
            sections.append(f"**{key}**: {value}\n\n")
    
    if experiment.risk_factors:
        sections.append("\n## 潜在风险因素\n")
        for risk in experiment.risk_factors:
            sections.append(f"- {risk}\n")
    
    return "".join(sections)
