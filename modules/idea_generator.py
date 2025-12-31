"""
研究想法生成器 - 重构版（适配Celery和llm_manager）
"""
import json
from typing import List, Optional
from models import ResearchLandscape, ResearchIdea
from utils import logger
import config
import uuid


class ResearchIdeaGenerator:
    """研究想法生成器"""
    
    def __init__(self, llm_manager):
        """
        初始化生成器
        
        Args:
            llm_manager: LLM管理器实例
        """
        self.llm_manager = llm_manager
    
    def generate_ideas(
        self,
        landscape: ResearchLandscape,
        num_ideas: int = 5,
        llm_name: Optional[str] = None
    ) -> List[ResearchIdea]:
        """
        生成研究想法
        
        Args:
            landscape: 研究脉络分析结果
            num_ideas: 生成想法数量
            llm_name: 使用的LLM名称
        
        Returns:
            研究想法列表
        """
        # 构建提示词
        # 构建Prompt上下文
        landscape_summary = {
            "unsolved_problems": landscape.unsolved_problems,
            "clusters": landscape.clusters[:5]  # 限制数量
        }
        
        # 构建提示词
        prompt = config.PROMPTS["idea_generation"].format(
            landscape=json.dumps(landscape_summary, ensure_ascii=False, indent=2),
            num_ideas=num_ideas
        )
        
        try:
            # 调用LLM生成想法
            response = self.llm_manager.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位富有创造力的科研专家，擅长从现有研究中发现创新机会。请严格按照JSON格式输出。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                llm_name=llm_name,
                temperature=0.7,  # 稍高温度以增加创造性
                json_mode=True
            )
            
            # 解析响应
            result_json = json.loads(response.content)
            
            # 创建ResearchIdea对象列表
            ideas = []
            if isinstance(result_json, list):
                ideas_data = result_json
            else:
                ideas_data = result_json.get("ideas", [])
            
            for i, idea_data in enumerate(ideas_data[:num_ideas]):
                idea = ResearchIdea(
                    idea_id=str(uuid.uuid4()),
                    title=idea_data.get("title", f"Research Idea {i+1}"),
                    motivation=idea_data.get("motivation", ""),
                    core_hypothesis=idea_data.get("hypothesis", ""),
                    expected_contribution=idea_data.get("contributions", ""),
                    difference_from_existing=idea_data.get("difference_from_existing", ""),
                    novelty_score=float(idea_data.get("novelty_score", 0.5)),  # 0-1
                    feasibility_score=float(idea_data.get("feasibility_score", 0.5))  # 0-1
                )
                ideas.append(idea)
            
            logger.info(f"Generated {len(ideas)} research ideas")
            
            return ideas
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # 返回一个基本想法
            return [
                ResearchIdea(
                    idea_id=str(uuid.uuid4()),
                    title="Failed to generate ideas",
                    motivation="JSON parse error",
                    core_hypothesis="",
                    expected_contribution="",
                    difference_from_existing="",
                    novelty_score=0.0,
                    feasibility_score=0.0
                )
            ]
        
        except Exception as e:
            logger.error(f"Idea generation failed: {e}")
            raise
