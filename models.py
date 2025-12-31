"""
AI-Researcher 核心数据模型
定义系统中所有模块使用的数据结构
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JournalLevel(Enum):
    """期刊/会议水平"""
    TOP = "top"  # 顶级
    Q1 = "q1"    # 一区
    Q2 = "q2"    # 二区
    ANY = "any"  # 不限


class PaperType(Enum):
    """文献类型"""
    SURVEY = "survey"      # 综述
    RESEARCH = "research"  # 原创研究
    ANY = "any"           # 不限


class ResearchField(Enum):
    """学科方向"""
    CV = "cv"              # 计算机视觉
    NLP = "nlp"            # 自然语言处理
    SYSTEMS = "systems"    # 系统
    ML = "ml"              # 机器学习
    BIO = "bio"            # 生物
    CROSS = "cross"        # 交叉领域
    ANY = "any"           # 不限


@dataclass
class ResearchIntent:
    """研究意图 - 用户输入的结构化表示"""
    keywords: str  # 主题关键词（必填）
    year_start: Optional[int] = None  # 起始年份
    year_end: Optional[int] = None    # 结束年份
    journal_level: JournalLevel = JournalLevel.ANY
    paper_type: PaperType = PaperType.ANY
    field: ResearchField = ResearchField.ANY
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['journal_level'] = self.journal_level.value
        result['paper_type'] = self.paper_type.value
        result['field'] = self.field.value
        return result


@dataclass
class PaperMetadata:
    """文献元数据"""
    title: str
    authors: List[str]
    abstract: str
    url: str
    published: str  # 发表日期
    paper_type: Optional[PaperType] = None
    journal: Optional[str] = None
    relevance_score: float = 0.0  # 相关度评分
    arxiv_id: Optional[str] = None
    partition: Optional[str] = None  # 分区
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        if self.paper_type:
            result['paper_type'] = self.paper_type.value
        return result


@dataclass
class PaperAnalysis:
    """文献阅读分析结果 - 结构化输出"""
    paper_id: str  # 论文唯一标识
    core_problem: str  # 核心问题
    key_method: str  # 关键方法
    technical_approach: str  # 技术路线
    experiment_conclusions: List[str]  # 实验结论
    limitations: List[str]  # 局限性/不足
    contributions: List[str]  # 贡献点
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ResearchCluster:
    """研究聚类 - 相似方向的文献组"""
    cluster_name: str  # 聚类名称
    papers: List[str]  # 论文ID列表
    key_themes: List[str]  # 关键主题
    technical_evolution: str  # 技术演进描述


@dataclass
class ResearchLandscape:
    """研究脉络全景"""
    clusters: List[ResearchCluster]  # 研究方向聚类
    solved_problems: List[str]  # 已解决的问题
    partially_solved: List[str]  # 半解决的问题
    unsolved_problems: List[str]  # 未解决的问题（ranked）
    technical_evolution: Dict[str, str]  # 技术演进路线图
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'clusters': [asdict(c) for c in self.clusters],
            'solved_problems': self.solved_problems,
            'partially_solved': self.partially_solved,
            'unsolved_problems': self.unsolved_problems,
            'technical_evolution': self.technical_evolution
        }


@dataclass
class ResearchIdea:
    """研究想法"""
    idea_id: str  # 想法ID
    title: str  # 想法标题
    motivation: str  # 研究动机
    core_hypothesis: str  # 核心假设
    expected_contribution: str  # 预期贡献
    difference_from_existing: str  # 与现有方法的区别
    feasibility_score: float = 0.0  # 可行性评分
    novelty_score: float = 0.0  # 新颖性评分
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class MethodDesign:
    """方法设计"""
    idea_id: str  # 对应的研究想法ID
    overview: str  # 方法概述
    model_framework: str  # 整体模型框架
    modules: List[Dict[str, str]]  # 核心模块列表 [{name, function, description}]
    baseline_differences: List[str]  # 与baseline的差异点
    theoretical_justification: str  # 理论/直觉解释
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ExperimentPlan:
    """实验设计"""
    method_id: str  # 对应的方法ID
    experiment_setup: str  # 实验设置
    baselines: List[str]  # baseline方法列表
    ablation_studies: List[Dict[str, str]]  # ablation设计 [{component, purpose}]
    expected_results: Dict[str, Any]  # 预期结果（带假设标注）
    metrics: List[str]  # 评估指标
    risk_factors: List[str]  # 风险点
    is_hypothetical: bool = True  # 是否为假设性结果
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class PaperSection:
    """论文章节"""
    section_name: str  # 章节名称
    content: str  # 内容
    source_type: str  # 来源类型：'literature' | 'hypothesis' | 'original'
    citations: List[str] = field(default_factory=list)  # 引用的论文ID


@dataclass
class PaperDraft:
    """论文草稿"""
    title: str
    abstract: PaperSection
    introduction: PaperSection
    related_work: PaperSection
    method: PaperSection
    experiments: PaperSection
    discussion: PaperSection
    conclusion: PaperSection
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'title': self.title,
            'abstract': asdict(self.abstract),
            'introduction': asdict(self.introduction),
            'related_work': asdict(self.related_work),
            'method': asdict(self.method),
            'experiments': asdict(self.experiments),
            'discussion': asdict(self.discussion),
            'conclusion': asdict(self.conclusion),
            'generated_at': self.generated_at
        }


@dataclass
class WorkflowState:
    """工作流状态 - 追踪整个研究流程"""
    research_intent: Optional[ResearchIntent] = None
    papers_metadata: List[PaperMetadata] = field(default_factory=list)
    papers_analysis: Dict[str, PaperAnalysis] = field(default_factory=dict)
    landscape: Optional[ResearchLandscape] = None
    ideas: List[ResearchIdea] = field(default_factory=list)
    selected_idea: Optional[ResearchIdea] = None
    method_design: Optional[MethodDesign] = None
    experiment_plan: Optional[ExperimentPlan] = None
    paper_draft: Optional[PaperDraft] = None
    current_step: str = "intent"  # 当前步骤
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'research_intent': self.research_intent.to_dict() if self.research_intent else None,
            'papers_metadata': [p.to_dict() for p in self.papers_metadata],
            'papers_analysis': {k: v.to_dict() for k, v in self.papers_analysis.items()},
            'landscape': self.landscape.to_dict() if self.landscape else None,
            'ideas': [i.to_dict() for i in self.ideas],
            'selected_idea': self.selected_idea.to_dict() if self.selected_idea else None,
            'method_design': self.method_design.to_dict() if self.method_design else None,
            'experiment_plan': self.experiment_plan.to_dict() if self.experiment_plan else None,
            'paper_draft': self.paper_draft.to_dict() if self.paper_draft else None,
            'current_step': self.current_step,
            'created_at': self.created_at
        }
