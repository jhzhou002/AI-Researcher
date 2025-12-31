"""
论文草稿生成器 - 重构版（适配Celery和llm_manager）
"""
import json
from typing import Optional, Dict
from models import ResearchIdea, MethodDesign, PaperDraft, PaperSection
from utils import logger
import uuid


class PaperDraftGenerator:
    """论文草稿生成器"""
    
    def __init__(self, llm_manager):
        """
        初始化生成器
        
        Args:
            llm_manager: LLM管理器实例
        """
        self.llm_manager = llm_manager
    
    def generate_draft(
        self,
        idea: ResearchIdea,
        method: MethodDesign,
        paper_analyses: list = None,
        progress_callback=None,
        llm_name: Optional[str] = None
    ) -> PaperDraft:
        """
        生成完整论文草稿
        
        Args:
            idea: 研究想法
            method: 方法设计
            paper_analyses: 文献分析列表（用于Related Work）
            progress_callback: 进度回调函数
            llm_name: 使用的LLM名称
        
        Returns:
            论文草稿
        """
        sections = {}
        section_order = [
            ("abstract", "摘要"),
            ("introduction", "引言"),
            ("related_work", "相关工作"),
            ("method", "方法"),
            ("experiment", "实验设计"),
            ("conclusion", "结论")
        ]
        
        for i, (section_key, section_name) in enumerate(section_order):
            if progress_callback:
                progress_callback(i, len(section_order), f"Generating {section_name}...")
            
            content = self._generate_section(
                section_key=section_key,
                idea=idea,
                method=method,
                paper_analyses=paper_analyses,
                existing_sections=sections,
                llm_name=llm_name
            )
            
            sections[section_key] = PaperSection(
                section_name=section_name,
                content=content,
                source_type="ai_generated"
            )
        
        # 创建PaperDraft
        draft = PaperDraft(
            id=str(uuid.uuid4()),
            idea_id=idea.id,
            title=idea.title,
            sections=sections
        )
        
        logger.info(f"Paper draft generated: {idea.title[:50]}")
        
        return draft
    
    def _generate_section(
        self,
        section_key: str,
        idea: ResearchIdea,
        method: MethodDesign,
        paper_analyses: list,
        existing_sections: Dict,
        llm_name: str
    ) -> str:
        """生成单个章节"""
        
        prompts = {
            "abstract": f"""为以下研究写一个学术摘要（约200词）：
标题: {idea.title}
动机: {idea.motivation}
假设: {idea.hypothesis}
方法: {method.algorithm_framework}
创新点: {', '.join(method.innovation_points)}

要求：包含背景、问题、方法、预期结果。""",

            "introduction": f"""为以下研究写Introduction（约500词）：
标题: {idea.title}
动机: {idea.motivation}
假设: {idea.hypothesis}
贡献: {idea.contributions}

要求：
1. 开篇引出研究背景和重要性
2. 指出当前研究的不足
3. 提出本文的解决方案
4. 总结本文贡献""",

            "related_work": f"""基于以下信息写Related Work（约400词）：
研究主题: {idea.title}
相关领域: {idea.motivation}

要求：
1. 综述相关工作的主要方法
2. 指出各方法的优缺点
3. 说明本文方法的定位""",

            "method": f"""基于以下方法设计写Method部分（约600词）：
算法框架: {method.algorithm_framework}
核心模块: {json.dumps(method.key_modules, ensure_ascii=False)}
数据需求: {method.data_requirements}

要求：
1. 详细描述整体框架
2. 分模块介绍各组件
3. 说明关键技术细节""",

            "experiment": f"""基于以下信息设计Experiment部分（约400词）：
评估指标: {', '.join(method.evaluation_metrics)}
预期挑战: {', '.join(method.expected_challenges)}

要求：
1. 描述实验设置（数据集、基线方法）
2. 设计消融实验
3. 说明预期结果""",

            "conclusion": f"""为以下研究写Conclusion（约200词）：
标题: {idea.title}
贡献: {idea.contributions}
创新点: {', '.join(method.innovation_points)}

要求：
1. 总结本文工作
2. 强调主要贡献
3. 提出未来研究方向"""
        }
        
        prompt = prompts.get(section_key, "请生成该章节内容。")
        
        try:
            response = self.llm_manager.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位学术论文写作专家，擅长撰写高质量的英文学术论文。请直接输出论文内容，不要包含任何解释或元信息。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                llm_name=llm_name,
                temperature=0.7
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate section {section_key}: {e}")
            return f"[Section generation failed: {str(e)}]"
