"""
文献阅读引擎 - 重构版（适配Celery和llm_manager）
"""
import json
from typing import Optional
from models import PaperAnalysis
from utils import logger
import config


class PaperReadingEngine:
    """文献阅读引擎，使用llm_manager进行论文分析"""
    
    def __init__(self, llm_manager):
        """
        初始化阅读引擎
        
        Args:
            llm_manager: LLM管理器实例
        """
        self.llm_manager = llm_manager
    
    def analyze_paper(
        self,
        title: str,
        abstract: str,
        full_text: str = "",
        llm_name: Optional[str] = None
    ) -> PaperAnalysis:
        """
        分析单篇论文
        
        Args:
            title: 论文标题
            abstract: 论文摘要
            full_text: 论文全文（可选）
            llm_name: 使用的LLM名称（默认使用系统配置）
        
        Returns:
            论文分析结果
        """
        # 构建提示词
        prompt = config.PROMPTS["paper_analysis"].format(
            title=title,
            authors="",  # 在DB模型中单独存储
            abstract=abstract
        )
        
        # 如果有全文，可以添加更多上下文
        if full_text:
            prompt += f"\n\n**Full Text Excerpt**:\n{full_text[:2000]}..."  # 限制长度
        
        try:
            # 使用llm_manager调用LLM
            response = self.llm_manager.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的学术研究分析专家。请严格按照JSON格式输出。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                llm_name=llm_name,
                temperature=0.3,
                json_mode=True
            )
            
            # 解析响应
            result_json = json.loads(response.content)
            
            # 创建PaperAnalysis对象
            # 处理实验结果，确保为列表
            exp_result = result_json.get("experiment_conclusions", [])
            if not exp_result and result_json.get("experiment_result"):
                exp_result = [result_json.get("experiment_result")]
            elif isinstance(exp_result, str):
                exp_result = [exp_result]
                
            analysis = PaperAnalysis(
                paper_id="",  # 由调用者设置
                core_problem=result_json.get("core_problem", ""),
                key_method=result_json.get("key_method", ""),
                technical_approach=result_json.get("technical_route", "") or result_json.get("technical_approach", ""),
                experiment_conclusions=exp_result,
                limitations=result_json.get("limitations", []),
                contributions=result_json.get("contributions", [])
            )
            
            logger.info(f"Successfully analyzed paper: {title[:50]}...")
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # 返回一个基本的分析结果
            return PaperAnalysis(
                paper_id="",
                core_problem="Failed to analyze (JSON parse error)",
                key_method="",
                technical_route="",
                experiment_result="",
                limitations="Analysis failed",
                contributions=""
            )
        
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
