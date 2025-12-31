"""
论文草稿生成模块
生成符合学术规范的论文各章节
"""
import json
from typing import Dict, List
from openai import OpenAI
from models import (
    ResearchIdea, MethodDesign, ExperimentPlan,
    PaperDraft, PaperSection, PaperMetadata, PaperAnalysis,
    ResearchLandscape
)
from utils import logger
import config


def generate_paper_draft(
    idea: ResearchIdea,
    method: MethodDesign,
    experiment: ExperimentPlan,
    papers_metadata: List[PaperMetadata],
    papers_analysis: Dict[str, PaperAnalysis],
    landscape: ResearchLandscape,
    api_key: str
) -> PaperDraft:
    """
    生成完整的论文草稿
    
    Args:
        idea: 研究想法
        method: 方法设计
        experiment: 实验设计
        papers_metadata: 文献元数据列表
        papers_analysis: 文献分析结果
        landscape: 研究脉络
        api_key: OpenAI API密钥
    
    Returns:
        论文草稿对象
    """
    logger.info("Generating paper draft...")
    
    client = OpenAI(api_key=api_key)
    
    # 准备上下文
    context = {
        'idea': idea,
        'method': method,
        'experiment': experiment,
        'papers': papers_metadata,
        'analysis': papers_analysis,
        'landscape': landscape
    }
    
    # 生成各部分
    sections = {}
    
    section_order = [
        ('abstract', '摘要'),
        ('introduction', '引言'),
        ('related_work', '相关工作'),
        ('method', '方法'),
        ('experiments', '实验'),
        ('discussion', '讨论'),
        ('conclusion', '结论')
    ]
    
    for section_key, section_name_cn in section_order:
        logger.info(f"Generating {section_name_cn}...")
        section = generate_section(section_key, context, client)
        sections[section_key] = section
    
    # 生成论文标题
    title = generate_title(idea, client)
    
    # 构建PaperDraft对象
    draft = PaperDraft(
        title=title,
        abstract=sections['abstract'],
        introduction=sections['introduction'],
        related_work=sections['related_work'],
        method=sections['method'],
        experiments=sections['experiments'],
        discussion=sections['discussion'],
        conclusion=sections['conclusion']
    )
    
    logger.info("Paper draft generated successfully")
    return draft


def generate_section(section_key: str, context: Dict, client: OpenAI) -> PaperSection:
    """
    生成单个章节
    
    Args:
        section_key: 章节键名
        context: 上下文信息
        client: OpenAI客户端
    
    Returns:
        论文章节对象
    """
    # 准备该章节的上下文
    section_context = prepare_section_context(section_key, context)
    
    # 构建提示词
    prompt = config.PROMPTS["paper_draft"].format(
        section=section_key,
        context=section_context
    )
    
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一位经验丰富的学术论文作者。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        
        content = response.choices[0].message.content
        
        # 确定来源类型
        source_type = determine_source_type(section_key)
        
        # 提取引用
        citations = extract_citations(content, context)
        
        section = PaperSection(
            section_name=section_key,
            content=content,
            source_type=source_type,
            citations=citations
        )
        
        return section
        
    except Exception as e:
        logger.error(f"Failed to generate section {section_key}: {e}")
        raise


def prepare_section_context(section_key: str, context: Dict) -> str:
    """
    准备章节上下文
    
    Args:
        section_key: 章节键名
        context: 完整上下文
    
    Returns:
        格式化的上下文文本
    """
    idea = context['idea']
    method = context['method']
    experiment = context['experiment']
    landscape = context['landscape']
    
    if section_key == 'abstract':
        return f"""
研究动机: {idea.motivation}
核心方法: {method.overview}
主要贡献: {idea.expected_contribution}
"""
    
    elif section_key == 'introduction':
        unsolved_problems = '\n'.join(f"- {p}" for p in landscape.unsolved_problems[:5])
        return f"""
研究背景:
{unsolved_problems}

我们的研究动机:
{idea.motivation}

研究假设:
{idea.core_hypothesis}

主要贡献:
{idea.expected_contribution}
"""
    
    elif section_key == 'related_work':
        # 准备文献综述内容
        clusters = '\n\n'.join([
            f"## {cluster.cluster_name}\n主题: {', '.join(cluster.key_themes)}"
            for cluster in landscape.clusters
        ])
        return f"""
研究方向分类:
{clusters}

我们方法的不同之处:
{idea.difference_from_existing}
"""
    
    elif section_key == 'method':
        modules = '\n'.join([
            f"- {m.get('name')}: {m.get('function')}"
            for m in method.modules
        ])
        return f"""
方法概述:
{method.overview}

模型框架:
{method.model_framework}

核心模块:
{modules}

理论依据:
{method.theoretical_justification}
"""
    
    elif section_key == 'experiments':
        baselines = '\n'.join(f"- {b}" for b in experiment.baselines)
        metrics = '\n'.join(f"- {m}" for m in experiment.metrics)
        return f"""
实验设置:
{experiment.experiment_setup}

Baseline方法:
{baselines}

评估指标:
{metrics}

注意: 以下为假设性结果分析
预期结果:
{json.dumps(experiment.expected_results, ensure_ascii=False, indent=2)}
"""
    
    elif section_key == 'discussion':
        limitations = '\n'.join(f"- {r}" for r in experiment.risk_factors)
        return f"""
研究贡献:
{idea.expected_contribution}

潜在局限性:
{limitations}
"""
    
    elif section_key == 'conclusion':
        return f"""
研究总结:
- 核心问题: {idea.motivation}
- 提出方法: {method.overview}
- 主要贡献: {idea.expected_contribution}
"""
    
    return ""


def determine_source_type(section_key: str) -> str:
    """
    确定章节的来源类型
    
    Args:
        section_key: 章节键名
    
    Returns:
        来源类型
    """
    if section_key in ['related_work']:
        return 'literature'
    elif section_key in ['method', 'introduction']:
        return 'original'
    elif section_key in ['experiments', 'discussion']:
        return 'hypothesis'
    else:
        return 'original'


def extract_citations(content: str, context: Dict) -> List[str]:
    """
    从内容中提取引用（简化实现）
    
    Args:
        content: 内容文本
        context: 上下文
    
    Returns:
        引用的论文ID列表
    """
    # 简化实现：返回所有相关论文
    papers = context.get('papers', [])
    return [p.arxiv_id or p.title for p in papers[:10]]  # 限制数量


def generate_title(idea: ResearchIdea, client: OpenAI) -> str:
    """
    生成论文标题
    
    Args:
        idea: 研究想法
        client: OpenAI客户端
    
    Returns:
        论文标题
    """
    prompt = f"""
    基于以下研究想法，生成一个简洁、专业的学术论文标题（英文）。
    
    研究想法:
    {idea.motivation}
    核心方法: {idea.core_hypothesis}
    
    要求:
    1. 标题应该简洁明了（10-15个单词）
    2. 体现核心贡献
    3. 使用学术规范的表达
    
    只输出标题，不要其他内容。
    """
    
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL_MINI,
            messages=[
                {"role": "system", "content": "你是一位学术论文撰写专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        title = response.choices[0].message.content.strip()
        # 移除引号
        title = title.strip('"').strip("'")
        
        return title
        
    except Exception as e:
        logger.error(f"Failed to generate title: {e}")
        return f"Research on {idea.idea_id}"


def format_paper_draft(draft: PaperDraft) -> str:
    """
    格式化论文草稿为Markdown
    
    Args:
        draft: 论文草稿对象
    
    Returns:
        Markdown格式的论文
    """
    sections = []
    
    sections.append(f"# {draft.title}\n")
    sections.append(f"*Generated: {draft.generated_at}*\n\n")
    sections.append("---\n\n")
    
    # Abstract
    sections.append("## Abstract\n")
    sections.append(_format_section_with_source(draft.abstract))
    sections.append("\n\n")
    
    # Introduction
    sections.append("## 1. Introduction\n")
    sections.append(_format_section_with_source(draft.introduction))
    sections.append("\n\n")
    
    # Related Work
    sections.append("## 2. Related Work\n")
    sections.append(_format_section_with_source(draft.related_work))
    sections.append("\n\n")
    
    # Method
    sections.append("## 3. Method\n")
    sections.append(_format_section_with_source(draft.method))
    sections.append("\n\n")
    
    # Experiments
    sections.append("## 4. Experiments\n")
    sections.append(_format_section_with_source(draft.experiments))
    sections.append("\n\n")
    
    # Discussion
    sections.append("## 5. Discussion\n")
    sections.append(_format_section_with_source(draft.discussion))
    sections.append("\n\n")
    
    # Conclusion
    sections.append("## 6. Conclusion\n")
    sections.append(_format_section_with_source(draft.conclusion))
    sections.append("\n")
    
    return "".join(sections)


def _format_section_with_source(section: PaperSection) -> str:
    """
    格式化章节并标注来源
    
    Args:
        section: 论文章节
    
    Returns:
        格式化的文本
    """
    source_labels = {
        'literature': '📚 基于文献',
        'hypothesis': '🔬 假设性分析',
        'original': '💡 原创内容'
    }
    
    label = source_labels.get(section.source_type, '')
    
    result = []
    if label:
        result.append(f"> *{label}*\n\n")
    
    result.append(section.content)
    
    return "".join(result)
