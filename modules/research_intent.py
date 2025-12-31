"""
研究意图模块
处理用户输入并创建结构化的研究意图对象
"""
from models import ResearchIntent, JournalLevel, PaperType, ResearchField
from utils import logger


def create_research_intent(
    keywords: str,
    year_start: int = None,
    year_end: int = None,
    journal_level: str = "any",
    paper_type: str = "any",
    field: str = "any"
) -> ResearchIntent:
    """
    创建研究意图对象
    
    Args:
        keywords: 研究主题关键词
        year_start: 起始年份
        year_end: 结束年份
        journal_level: 期刊水平 (top/q1/q2/any)
        paper_type: 文献类型 (survey/research/any)
        field: 学科方向 (cv/nlp/systems/ml/bio/cross/any)
    
    Returns:
        ResearchIntent对象
    """
    if not keywords or not keywords.strip():
        raise ValueError("研究主题关键词不能为空")
    
    # 转换枚举类型
    try:
        journal_level_enum = JournalLevel(journal_level.lower())
        paper_type_enum = PaperType(paper_type.lower())
        field_enum = ResearchField(field.lower())
    except ValueError as e:
        logger.error(f"Invalid enum value: {e}")
        raise ValueError(f"无效的参数值: {e}")
    
    # 验证年份范围
    if year_start and year_end and year_start > year_end:
        raise ValueError("起始年份不能大于结束年份")
    
    intent = ResearchIntent(
        keywords=keywords.strip(),
        year_start=year_start,
        year_end=year_end,
        journal_level=journal_level_enum,
        paper_type=paper_type_enum,
        field=field_enum
    )
    
    logger.info(f"Research intent created: {keywords}")
    logger.debug(f"Intent details: {intent.to_dict()}")
    
    return intent


def validate_research_intent(intent: ResearchIntent) -> bool:
    """
    验证研究意图是否有效
    
    Args:
        intent: ResearchIntent对象
    
    Returns:
        是否有效
    """
    if not intent.keywords or len(intent.keywords.strip()) < 3:
        logger.error("Keywords too short")
        return False
    
    if intent.year_start and intent.year_start < 1900:
        logger.error("Invalid start year")
        return False
    
    if intent.year_end:
        from datetime import datetime
        current_year = datetime.now().year
        if intent.year_end > current_year + 1:
            logger.error("End year in the future")
            return False
    
    return True
