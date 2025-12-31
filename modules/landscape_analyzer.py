"""
研究脉络分析器 - 重构版（适配Celery和llm_manager）
"""
import json
from typing import List, Optional
from models import PaperAnalysis, ResearchLandscape
from utils import logger
import config


class ResearchLandscapeAnalyzer:
    """研究脉络分析器"""
    
    def __init__(self, llm_manager):
        """
        初始化分析器
        
        Args:
            llm_manager: LLM管理器实例
        """
        self.llm_manager = llm_manager
    
    def analyze_landscape(
        self,
        analyses: List[PaperAnalysis],
        llm_name: Optional[str] = None
    ) -> ResearchLandscape:
        """
        分析研究脉络
        
        Args:
            analyses: 文献分析结果列表
            llm_name: 使用的LLM名称
        
        Returns:
            研究脉络分析结果
        """
        if not analyses:
            raise ValueError("No paper analyses provided")
        
        # 构建分析摘要
        analyses_summary = []
        for i, analysis in enumerate(analyses[:20]):  # 限制数量避免token过多
            analyses_summary.append({
                "index": i + 1,
                "core_problem": analysis.core_problem,
                "key_method": analysis.key_method,
                "limitations": analysis.limitations
            })
        
        # 构建提示词
        prompt = config.PROMPTS["landscape_analysis"].format(
            papers_analysis=json.dumps(analyses_summary, ensure_ascii=False, indent=2)
        )
        
        try:
            # 调用LLM分析
            response = self.llm_manager.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位资深的科研领域专家，擅长从大量文献中提炼研究趋势和识别研究空白。请严格按照JSON格式输出。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                llm_name=llm_name,
                temperature=0.5,
                json_mode=True
            )
            
            # 解析响应
            result_json = json.loads(response.content)
            
            # 创建ResearchLandscape对象
            landscape = ResearchLandscape(
                clusters=result_json.get("clusters", []),
                solved_problems=result_json.get("solved_problems", []),
                partially_solved=result_json.get("partially_solved", []) or result_json.get("partially_solved_problems", []),
                unsolved_problems=result_json.get("unsolved_problems", []),
                technical_evolution=result_json.get("technical_evolution", {}) or result_json.get("tech_evolution", {})
            )
            
            logger.info(f"Landscape analysis completed: {len(landscape.clusters)} clusters, {len(landscape.unsolved_problems)} unsolved problems")
            
            return landscape
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # 返回一个基本结果
            return ResearchLandscape(
                clusters=[],
                solved_problems=[],
                partially_solved_problems=[],
                unsolved_problems=["Failed to analyze landscape"],
                tech_evolution=[]
            )
        
        except Exception as e:
            logger.error(f"Landscape analysis failed: {e}")
            raise
