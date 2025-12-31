"""
工具函数库
"""
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import config


def setup_logger(name: str = "ai_researcher") -> logging.Logger:
    """设置日志系统"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # 文件处理器
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


logger = setup_logger()


def get_cache_key(data: Any) -> str:
    """生成缓存键"""
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()


def save_to_cache(key: str, data: Any, cache_type: str = "general") -> None:
    """保存到缓存"""
    if not config.CACHE_ENABLED:
        return
    
    cache_dir = config.CACHE_DIR / cache_type
    cache_dir.mkdir(exist_ok=True)
    
    cache_file = cache_dir / f"{key}.json"
    cache_data = {
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    logger.debug(f"Saved to cache: {cache_file}")


def load_from_cache(key: str, cache_type: str = "general") -> Optional[Any]:
    """从缓存加载"""
    if not config.CACHE_ENABLED:
        return None
    
    cache_file = config.CACHE_DIR / cache_type / f"{key}.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 检查是否过期
        timestamp = datetime.fromisoformat(cache_data["timestamp"])
        if datetime.now() - timestamp > timedelta(days=config.CACHE_EXPIRY_DAYS):
            logger.debug(f"Cache expired: {cache_file}")
            return None
        
        logger.debug(f"Loaded from cache: {cache_file}")
        return cache_data["data"]
    
    except Exception as e:
        logger.warning(f"Failed to load cache {cache_file}: {e}")
        return None


def save_workflow_state(state: 'WorkflowState', filename: Optional[str] = None) -> Path:
    """保存工作流状态"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_{timestamp}.json"
    
    output_file = config.OUTPUT_DIR / filename
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
    
    logger.info(f"Workflow state saved to: {output_file}")
    return output_file


def load_workflow_state(filename: str) -> Optional[Dict[str, Any]]:
    """加载工作流状态"""
    input_file = config.OUTPUT_DIR / filename
    
    if not input_file.exists():
        logger.error(f"Workflow state file not found: {input_file}")
        return None
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            state_dict = json.load(f)
        
        logger.info(f"Workflow state loaded from: {input_file}")
        return state_dict
    
    except Exception as e:
        logger.error(f"Failed to load workflow state: {e}")
        return None


def save_json(data: Any, filename: str, subdir: Optional[str] = None) -> Path:
    """保存JSON文件"""
    if subdir:
        output_dir = config.OUTPUT_DIR / subdir
        output_dir.mkdir(exist_ok=True)
    else:
        output_dir = config.OUTPUT_DIR
    
    output_file = output_dir / filename
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"JSON saved to: {output_file}")
    return output_file


def load_json(filename: str, subdir: Optional[str] = None) -> Optional[Any]:
    """加载JSON文件"""
    if subdir:
        input_dir = config.OUTPUT_DIR / subdir
    else:
        input_dir = config.OUTPUT_DIR
    
    input_file = input_dir / filename
    
    if not input_file.exists():
        logger.error(f"JSON file not found: {input_file}")
        return None
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"JSON loaded from: {input_file}")
        return data
    
    except Exception as e:
        logger.error(f"Failed to load JSON: {e}")
        return None


def truncate_text(text: str, max_length: int = 1000) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_paper_citation(paper: 'PaperMetadata') -> str:
    """格式化论文引用"""
    authors = ", ".join(paper.authors[:3])
    if len(paper.authors) > 3:
        authors += " et al."
    return f"{authors}. {paper.title}. {paper.published}"
