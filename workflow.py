"""
工作流编排器
管理整个研究流程的执行
"""
from typing import Optional
from models import WorkflowState, ResearchIntent
from modules.research_intent import create_research_intent, validate_research_intent
from modules.literature_discovery import search_papers, deduplicate_papers
from modules.paper_reading import analyze_papers
from modules.landscape_analysis import analyze_research_landscape
from modules.idea_generation import generate_research_ideas, rank_ideas
from modules.method_design import design_method
from modules.experiment_planning import design_experiments
from modules.paper_drafting import generate_paper_draft
from utils import logger, save_workflow_state, save_json
import config


class ResearchWorkflow:
    """研究工作流管理器"""
    
    def __init__(self, api_key: str):
        """
        初始化工作流
        
        Args:
            api_key: OpenAI API密钥
        """
        self.api_key = api_key
        self.state = WorkflowState()
        logger.info("Research workflow initialized")
    
    def set_research_intent(
        self,
        keywords: str,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        journal_level: str = "any",
        paper_type: str = "any",
        field: str = "any"
    ) -> ResearchIntent:
        """
        设置研究意图
        
        Args:
            keywords: 研究关键词
            year_start: 起始年份
            year_end: 结束年份
            journal_level: 期刊水平
            paper_type: 论文类型
            field: 学科方向
        
        Returns:
            研究意图对象
        """
        intent = create_research_intent(
            keywords=keywords,
            year_start=year_start,
            year_end=year_end,
            journal_level=journal_level,
            paper_type=paper_type,
            field=field
        )
        
        if not validate_research_intent(intent):
            raise ValueError("Invalid research intent")
        
        self.state.research_intent = intent
        self.state.current_step = "intent"
        
        logger.info(f"Research intent set: {keywords}")
        return intent
    
    def discover_literature(self, max_results: int = None) -> int:
        """
        检索文献
        
        Args:
            max_results: 最大结果数
        
        Returns:
            检索到的论文数量
        """
        if not self.state.research_intent:
            raise ValueError("Research intent not set")
        
        logger.info("Starting literature discovery...")
        
        papers = search_papers(self.state.research_intent, max_results)
        papers = deduplicate_papers(papers)
        
        # 过滤低相关度论文
        filtered_papers = [
            p for p in papers
            if p.relevance_score >= config.MIN_RELEVANCE_SCORE
        ]
        
        self.state.papers_metadata = filtered_papers
        self.state.current_step = "discovery"
        
        logger.info(f"Discovered {len(filtered_papers)} relevant papers")
        
        # 保存中间结果
        if config.SAVE_INTERMEDIATE_RESULTS:
            save_json(
                [p.to_dict() for p in filtered_papers],
                "papers_metadata.json"
            )
        
        return len(filtered_papers)
    
    def analyze_literature(self, max_papers: int = None) -> int:
        """
        分析文献
        
        Args:
            max_papers: 最多分析的论文数
        
        Returns:
            分析的论文数量
        """
        if not self.state.papers_metadata:
            raise ValueError("No papers to analyze")
        
        logger.info("Starting literature analysis...")
        
        papers_analysis = analyze_papers(
            self.state.papers_metadata,
            self.api_key,
            max_papers
        )
        
        self.state.papers_analysis = papers_analysis
        self.state.current_step = "analysis"
        
        logger.info(f"Analyzed {len(papers_analysis)} papers")
        
        # 保存中间结果
        if config.SAVE_INTERMEDIATE_RESULTS:
            save_json(
                {k: v.to_dict() for k, v in papers_analysis.items()},
                "papers_analysis.json"
            )
        
        return len(papers_analysis)
    
    def analyze_landscape(self):
        """分析研究脉络"""
        if not self.state.papers_analysis:
            raise ValueError("No paper analysis available")
        
        logger.info("Analyzing research landscape...")
        
        landscape = analyze_research_landscape(
            self.state.papers_analysis,
            self.api_key
        )
        
        self.state.landscape = landscape
        self.state.current_step = "landscape"
        
        logger.info("Research landscape analyzed")
        
        # 保存中间结果
        if config.SAVE_INTERMEDIATE_RESULTS:
            save_json(landscape.to_dict(), "research_landscape.json")
        
        return landscape
    
    def generate_ideas(self, num_ideas: int = None) -> int:
        """
        生成研究想法
        
        Args:
            num_ideas: 生成想法数量
        
        Returns:
            生成的想法数量
        """
        if not self.state.landscape:
            raise ValueError("Research landscape not analyzed")
        
        logger.info("Generating research ideas...")
        
        ideas = generate_research_ideas(
            self.state.landscape,
            self.api_key,
            num_ideas
        )
        
        # 排序想法
        ranked_ideas = rank_ideas(ideas)
        
        self.state.ideas = ranked_ideas
        self.state.current_step = "ideas"
        
        logger.info(f"Generated {len(ranked_ideas)} research ideas")
        
        # 保存中间结果
        if config.SAVE_INTERMEDIATE_RESULTS:
            save_json([i.to_dict() for i in ranked_ideas], "research_ideas.json")
        
        return len(ranked_ideas)
    
    def select_idea(self, idea_index: int = 0):
        """
        选择研究想法
        
        Args:
            idea_index: 想法索引（0为评分最高）
        """
        if not self.state.ideas:
            raise ValueError("No ideas generated")
        
        if idea_index >= len(self.state.ideas):
            raise ValueError(f"Invalid idea index: {idea_index}")
        
        self.state.selected_idea = self.state.ideas[idea_index]
        logger.info(f"Selected idea: {self.state.selected_idea.idea_id}")
    
    def design_method(self):
        """设计研究方法"""
        if not self.state.selected_idea:
            raise ValueError("No idea selected")
        
        logger.info("Designing research method...")
        
        method = design_method(self.state.selected_idea, self.api_key)
        
        self.state.method_design = method
        self.state.current_step = "method"
        
        logger.info("Method designed")
        
        # 保存中间结果
        if config.SAVE_INTERMEDIATE_RESULTS:
            save_json(method.to_dict(), "method_design.json")
        
        return method
    
    def plan_experiments(self):
        """规划实验"""
        if not self.state.method_design:
            raise ValueError("No method designed")
        
        logger.info("Planning experiments...")
        
        experiment = design_experiments(self.state.method_design, self.api_key)
        
        self.state.experiment_plan = experiment
        self.state.current_step = "experiment"
        
        logger.info("Experiments planned")
        
        # 保存中间结果
        if config.SAVE_INTERMEDIATE_RESULTS:
            save_json(experiment.to_dict(), "experiment_plan.json")
        
        return experiment
    
    def draft_paper(self):
        """生成论文草稿"""
        if not all([
            self.state.selected_idea,
            self.state.method_design,
            self.state.experiment_plan,
            self.state.landscape
        ]):
            raise ValueError("Not all required components are ready")
        
        logger.info("Generating paper draft...")
        
        draft = generate_paper_draft(
            idea=self.state.selected_idea,
            method=self.state.method_design,
            experiment=self.state.experiment_plan,
            papers_metadata=self.state.papers_metadata,
            papers_analysis=self.state.papers_analysis,
            landscape=self.state.landscape,
            api_key=self.api_key
        )
        
        self.state.paper_draft = draft
        self.state.current_step = "draft"
        
        logger.info("Paper draft generated")
        
        # 保存最终结果
        save_json(draft.to_dict(), "paper_draft.json")
        
        return draft
    
    def save_state(self, filename: Optional[str] = None):
        """
        保存工作流状态
        
        Args:
            filename: 文件名
        """
        return save_workflow_state(self.state, filename)
    
    def get_current_step(self) -> str:
        """获取当前步骤"""
        return self.state.current_step
