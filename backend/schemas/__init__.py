"""
Pydantic Schemas - 请求和响应模型
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class JournalLevelEnum(str, Enum):
    """期刊水平"""
    TOP = "top"
    Q1 = "q1"
    Q2 = "q2"
    ANY = "any"


class PaperTypeEnum(str, Enum):
    """论文类型"""
    SURVEY = "survey"
    RESEARCH = "research"
    ANY = "any"


class ResearchFieldEnum(str, Enum):
    """学科方向"""
    CV = "cv"
    NLP = "nlp"
    SYSTEMS = "systems"
    ML = "ml"
    BIO = "bio"
    CROSS = "cross"
    ANY = "any"


class TaskStatusEnum(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==================== 用户相关 ====================

class UserCreate(BaseModel):
    """用户注册"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT Token"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据"""
    username: Optional[str] = None


# ==================== 研究项目相关 ====================

class ResearchIntentCreate(BaseModel):
    """创建研究意图"""
    title: str = Field(..., min_length=1, max_length=500)
    keywords: str = Field(..., min_length=1, max_length=500)
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    journal_level: JournalLevelEnum = JournalLevelEnum.ANY
    paper_type: PaperTypeEnum = PaperTypeEnum.ANY
    field: ResearchFieldEnum = ResearchFieldEnum.ANY


class ProjectResponse(BaseModel):
    """项目响应"""
    id: int
    user_id: int
    title: str
    keywords: str
    year_start: Optional[int]
    year_end: Optional[int]
    journal_level: Optional[str]
    paper_type: Optional[str]
    field: Optional[str]
    current_step: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    """项目列表"""
    projects: List[ProjectResponse]
    total: int


# ==================== 文献相关 ====================

class PaperResponse(BaseModel):
    """文献响应"""
    id: int
    project_id: int
    title: str
    authors: List[str]
    abstract: Optional[str]
    url: Optional[str]
    published: Optional[str]
    paper_type: Optional[str]
    journal: Optional[str]
    relevance_score: float
    arxiv_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaperAnalysisResponse(BaseModel):
    """文献分析响应"""
    id: int
    project_id: int
    paper_id: int
    core_problem: Optional[str]
    key_method: Optional[str]
    technical_approach: Optional[str]
    experiment_conclusions: Optional[List[str]]
    limitations: Optional[List[str]]
    contributions: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 研究脉络相关 ====================

class ResearchLandscapeResponse(BaseModel):
    """研究脉络响应"""
    id: int
    project_id: int
    clusters: Optional[List[Dict[str, Any]]]
    solved_problems: Optional[List[str]]
    partially_solved: Optional[List[str]]
    unsolved_problems: Optional[List[str]]
    technical_evolution: Optional[Dict[str, str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 研究想法相关 ====================

class ResearchIdeaResponse(BaseModel):
    """研究想法响应"""
    id: int
    project_id: int
    idea_id: str
    motivation: Optional[str]
    core_hypothesis: Optional[str]
    expected_contribution: Optional[str]
    difference_from_existing: Optional[str]
    feasibility_score: float
    novelty_score: float
    is_selected: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class IdeaSelect(BaseModel):
    """选择研究想法"""
    idea_id: int


# ==================== 异步任务相关 ====================

class TaskResponse(BaseModel):
    """任务响应"""
    id: int
    task_id: str
    task_name: str
    task_type: Optional[str]
    status: TaskStatusEnum
    progress: int
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    """创建任务请求"""
    task_name: str
    task_type: str
    project_id: Optional[int] = None


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    error_code: Optional[str] = None


# ==================== 健康检查 ====================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    llms_available: List[str]
    default_llm: Optional[str]
    database_connected: bool = True
