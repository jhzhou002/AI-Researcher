"""
结构化日志系统
提供统一的日志格式和配置
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import os


class StructuredFormatter(logging.Formatter):
    """结构化JSON日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 格式: [时间] LEVEL logger: message
        formatted = f"{color}[{timestamp}] {record.levelname:8s}{self.RESET} {record.name}: {record.getMessage()}"
        
        # 添加异常信息
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False
):
    """
    设置日志系统
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径（可选）
        json_format: 是否使用JSON格式
    """
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())
    
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        
        root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志器
    
    Args:
        name: 日志器名称
    
    Returns:
        Logger实例
    """
    return logging.getLogger(name)


class LogContext:
    """日志上下文管理器，添加额外数据"""
    
    def __init__(self, logger: logging.Logger, **extra_data):
        self.logger = logger
        self.extra_data = extra_data
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def _log(self, level: int, msg: str, **kwargs):
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, msg, (), None, **kwargs
        )
        record.extra_data = self.extra_data
        self.logger.handle(record)
    
    def info(self, msg: str):
        self._log(logging.INFO, msg)
    
    def error(self, msg: str):
        self._log(logging.ERROR, msg)
    
    def warning(self, msg: str):
        self._log(logging.WARNING, msg)
    
    def debug(self, msg: str):
        self._log(logging.DEBUG, msg)


# 导出
__all__ = ['setup_logging', 'get_logger', 'LogContext', 'StructuredFormatter', 'ConsoleFormatter']
