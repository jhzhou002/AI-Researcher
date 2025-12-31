"""
系统配置管理
"""
import os
from pathlib import Path

# API配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"  # 主要模型
OPENAI_MODEL_MINI = "gpt-4o-mini"  # 用于简单任务的轻量模型

# 文献检索配置
ARXIV_MAX_RESULTS = 50  # ArXiv最大检索数量
ARXIV_SORT_BY = "relevance"  # 排序方式: relevance, lastUpdatedDate, submittedDate

# 相关度评分阈值
MIN_RELEVANCE_SCORE = 0.3  # 最低相关度分数

# 文献分析配置
BATCH_SIZE = 5  # 批量处理论文数量
MAX_PAPERS_TO_ANALYZE = 20  # 最多深度分析的论文数量

# 研究想法生成配置
MAX_IDEAS_TO_GENERATE = 5  # 生成研究想法的最大数量

# 缓存配置
CACHE_DIR = Path("cache")
CACHE_ENABLED = True
CACHE_EXPIRY_DAYS = 7  # 缓存过期天数

# 输出配置
OUTPUT_DIR = Path("outputs")
SAVE_INTERMEDIATE_RESULTS = True  # 是否保存中间结果

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "ai_researcher.log"

# 创建必要的目录
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# 提示词模板配置
PROMPTS = {
    "paper_analysis": """你是一位专业的学术研究分析专家。请仔细阅读以下论文信息，并提取结构化的分析结果。

论文标题：{title}
作者：{authors}
摘要：{abstract}

请按以下JSON格式输出分析结果：
{{
    "core_problem": "这篇论文要解决的核心问题是什么？",
    "key_method": "核心方法或技术是什么？",
    "technical_approach": "具体的技术路线和实现方式",
    "experiment_conclusions": ["主要实验结论1", "主要实验结论2"],
    "limitations": ["局限性1", "局限性2"],
    "contributions": ["贡献点1", "贡献点2"]
}}

请确保输出是有效的JSON格式。""",
    
    "landscape_analysis": """你是一位学术研究综述专家。我已经分析了多篇相关论文，现在需要你帮我梳理研究脉络。

论文分析结果：
{papers_analysis}

请完成以下任务：
1. 将这些论文按研究方向聚类（给出聚类名称和关键主题）
2. 梳理技术演进路线
3. 识别已解决、半解决和未解决的问题
4. 对未解决问题按重要性和可行性排序

请按以下JSON格式输出：
{{
    "clusters": [
        {{"cluster_name": "聚类名称", "papers": ["paper_id1"], "key_themes": ["主题1"], "technical_evolution": "演进描述"}}
    ],
    "solved_problems": ["已解决问题1"],
    "partially_solved": ["半解决问题1"],
    "unsolved_problems": ["未解决问题1（ranked）"],
    "technical_evolution": {{"方向1": "演进描述"}}
}}""",
    
    "idea_generation": """你是一位富有创新精神的研究者。基于以下研究脉络分析，请生成新颖的研究想法。

研究脉络：
{landscape}

请生成{num_ideas}个研究想法，每个想法包含：
- motivation: 研究动机（为什么要做这个研究）
- core_hypothesis: 核心假设
- expected_contribution: 预期贡献
- difference_from_existing: 与现有方法的主要区别
- feasibility_score: 可行性评分（0-1）
- novelty_score: 新颖性评分（0-1）

输出JSON数组格式：
[
    {{
        "idea_id": "idea_1",
        "motivation": "...",
        "core_hypothesis": "...",
        "expected_contribution": "...",
        "difference_from_existing": "...",
        "feasibility_score": 0.8,
        "novelty_score": 0.7
    }}
]""",
    
    "method_design": """你是一位算法设计专家。请将以下研究想法转化为具体的方法设计。

研究想法：
{idea}

请设计具体的方法框架，输出JSON格式：
{{
    "overview": "方法概述",
    "model_framework": "整体模型框架描述",
    "modules": [
        {{"name": "模块名", "function": "功能", "description": "详细描述"}}
    ],
    "baseline_differences": ["与baseline的差异点1"],
    "theoretical_justification": "理论/直觉解释"
}}""",
    
    "experiment_design": """你是一位实验设计专家。请为以下方法设计详细的实验方案。

方法设计：
{method}

请设计实验方案，输出JSON格式：
{{
    "experiment_setup": "实验设置描述（数据集、环境、超参数等）",
    "baselines": ["baseline方法1", "baseline方法2"],
    "ablation_studies": [
        {{"component": "组件名", "purpose": "测试目的"}}
    ],
    "metrics": ["评估指标1", "评估指标2"],
    "expected_results": {{"描述": "预期的结果趋势和分析"}},
    "risk_factors": ["可能的风险点1"]
}}""",
    
    "paper_draft": """你是一位经验丰富的学术论文作者。请根据以下信息撰写论文的{section}部分。

研究背景：
{context}

要求：
1. 符合学术写作规范
2. 明确标注内容来源（文献事实、研究假设、原创想法）
3. 使用规范的学术语言
4. 不伪造实验结果

请输出markdown格式的{section}内容。"""
}
