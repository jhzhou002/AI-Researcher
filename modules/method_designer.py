"""
方法设计生成器 - 重构版（适配Celery和llm_manager）
"""
import json
from typing import Optional
from models import ResearchIdea, MethodDesign
from utils import logger
import config
import uuid


class MethodDesigner:
    """方法设计生成器"""
    
    def __init__(self, llm_manager):
        """
        初始化生成器
        
        Args:
            llm_manager: LLM管理器实例
        """
        self.llm_manager = llm_manager
    
    def design_method(
        self,
        idea: ResearchIdea,
        llm_name: Optional[str] = None
    ) -> MethodDesign:
        """
        为研究想法设计方法
        
        Args:
            idea: 研究想法
            llm_name: 使用的LLM名称
        
        Returns:
            方法设计结果
        """
        # 构建提示词
        prompt = f"""基于以下研究想法，设计详细的研究方法：

**研究想法标题**: {idea.title}
**研究动机**: {idea.motivation}
**研究假设**: {idea.hypothesis}
**预期贡献**: {idea.contributions}

请设计包含以下内容的研究方法（JSON格式）:
{{
    "algorithm_framework": "算法框架的详细描述，包含核心思路",
    "key_modules": [
        {{
            "name": "模块名称",
            "description": "模块功能描述",
            "implementation": "实现要点"
        }}
    ],
    "data_requirements": "所需数据和预处理方法",
    "evaluation_metrics": ["评估指标1", "评估指标2"],
    "expected_challenges": ["可能遇到的挑战1", "挑战2"],
    "innovation_points": ["创新点1", "创新点2"]
}}"""
        
        try:
            # 调用LLM设计方法
            response = self.llm_manager.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位资深的AI研究员，擅长设计创新的研究方法。请严格按照JSON格式输出。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                llm_name=llm_name,
                temperature=0.6,
                json_mode=True
            )
            
            # 解析响应
            result_json = json.loads(response.content)
            
            # 创建MethodDesign对象
            method = MethodDesign(
                id=str(uuid.uuid4()),
                idea_id=idea.id,
                algorithm_framework=result_json.get("algorithm_framework", ""),
                key_modules=result_json.get("key_modules", []),
                data_requirements=result_json.get("data_requirements", ""),
                evaluation_metrics=result_json.get("evaluation_metrics", []),
                expected_challenges=result_json.get("expected_challenges", []),
                innovation_points=result_json.get("innovation_points", [])
            )
            
            logger.info(f"Method design completed for idea: {idea.title[:50]}")
            
            return method
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return MethodDesign(
                id=str(uuid.uuid4()),
                idea_id=idea.id,
                algorithm_framework="Failed to generate (JSON parse error)",
                key_modules=[],
                data_requirements="",
                evaluation_metrics=[],
                expected_challenges=["Generation failed"],
                innovation_points=[]
            )
        
        except Exception as e:
            logger.error(f"Method design failed: {e}")
            raise
