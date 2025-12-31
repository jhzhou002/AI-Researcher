"""
数据库模型定义
使用SQLAlchemy ORM
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    """用户角色"""
    ADMIN = "admin"
    USER = "user"


class TaskStatus(enum.Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    projects = relationship("ResearchProject", back_populates="user", cascade="all, delete-orphan")
    api_usage = relationship("APIUsage", back_populates="user")


class ResearchProject(Base):
    """研究项目表"""
    __tablename__ = "research_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    keywords = Column(String(500), nullable=False)
    
    # 研究意图参数
    year_start = Column(Integer)
    year_end = Column(Integer)
    journal_level = Column(String(50))
    paper_type = Column(String(50))
    field = Column(String(50))
    
    # 当前进度
    current_step = Column(String(50), default="intent")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="projects")
    papers = relationship("Paper", back_populates="project")
    analyses = relationship("PaperAnalysisDB", back_populates="project")
    landscape = relationship("ResearchLandscapeDB", back_populates="project", uselist=False)
    ideas = relationship("ResearchIdeaDB", back_populates="project")
    method = relationship("MethodDesignDB", back_populates="project", uselist=False)
    experiment = relationship("ExperimentPlanDB", back_populates="project", uselist=False)
    draft = relationship("PaperDraftDB", back_populates="project", uselist=False)
    tasks = relationship("AsyncTask", back_populates="project")


class Paper(Base):
    """文献元数据表"""
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False)
    
    title = Column(Text, nullable=False)
    authors = Column(JSON)  # JSON数组
    abstract = Column(Text)
    url = Column(String(500))
    published = Column(String(50))
    paper_type = Column(String(50))
    journal = Column(String(255))
    relevance_score = Column(Float, default=0.0)
    arxiv_id = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("ResearchProject", back_populates="papers")
    analysis = relationship("PaperAnalysisDB", back_populates="paper", uselist=False)


class PaperAnalysisDB(Base):
    """文献分析结果表"""
    __tablename__ = "paper_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    
    core_problem = Column(Text)
    key_method = Column(Text)
    technical_approach = Column(Text)
    experiment_conclusions = Column(JSON)  # JSON数组
    limitations = Column(JSON)  # JSON数组
    contributions = Column(JSON)  # JSON数组
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("ResearchProject", back_populates="analyses")
    paper = relationship("Paper", back_populates="analysis")


class ResearchLandscapeDB(Base):
    """研究脉络表"""
    __tablename__ = "research_landscapes"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False, unique=True)
    
    clusters = Column(JSON)  # JSON数组
    solved_problems = Column(JSON)
    partially_solved = Column(JSON)
    unsolved_problems = Column(JSON)
    technical_evolution = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("ResearchProject", back_populates="landscape")


class ResearchIdeaDB(Base):
    """研究想法表"""
    __tablename__ = "research_ideas"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False)
    
    idea_id = Column(String(100), nullable=False)
    title = Column(String(500))  # Ensure this matches migration
    motivation = Column(Text)
    core_hypothesis = Column(Text)
    expected_contribution = Column(Text)
    difference_from_existing = Column(Text)
    feasibility_score = Column(Float, default=0.5)
    novelty_score = Column(Float, default=0.5)
    
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("ResearchProject", back_populates="ideas")


class MethodDesignDB(Base):
    """方法设计表"""
    __tablename__ = "method_designs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False, unique=True)
    idea_id = Column(String(100))
    
    overview = Column(Text)
    model_framework = Column(Text)
    modules = Column(JSON)
    baseline_differences = Column(JSON)
    theoretical_justification = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("ResearchProject", back_populates="method")


class ExperimentPlanDB(Base):
    """实验设计表"""
    __tablename__ = "experiment_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False, unique=True)
    method_id = Column(String(100))
    
    experiment_setup = Column(Text)
    baselines = Column(JSON)
    ablation_studies = Column(JSON)
    expected_results = Column(JSON)
    metrics = Column(JSON)
    risk_factors = Column(JSON)
    is_hypothetical = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("ResearchProject", back_populates="experiment")


class PaperDraftDB(Base):
    """论文草稿表"""
    __tablename__ = "paper_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False, unique=True)
    
    title = Column(String(500))
    abstract = Column(JSON)  # PaperSection as JSON
    introduction = Column(JSON)
    related_work = Column(JSON)
    method = Column(JSON)
    experiments = Column(JSON)
    discussion = Column(JSON)
    conclusion = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("ResearchProject", back_populates="draft")


class AsyncTask(Base):
    """异步任务表"""
    __tablename__ = "async_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    task_id = Column(String(100), unique=True, index=True, nullable=False)  # Celery task ID
    task_name = Column(String(255), nullable=False)
    task_type = Column(String(100))  # discovery/analysis/generation等
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    result = Column(JSON)
    error_message = Column(Text)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    project = relationship("ResearchProject", back_populates="tasks")


class APIUsage(Base):
    """API使用统计表"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    llm_provider = Column(String(50), nullable=False)
    llm_model = Column(String(100), nullable=False)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    task_type = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="api_usage")
