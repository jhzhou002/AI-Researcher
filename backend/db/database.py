"""
数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://remote:Zhjh0704.@49.235.74.98:3306/ai_researcher"
)

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # 对于异步任务，使用NullPool避免连接池问题
    echo=os.getenv("SQL_ECHO", "False").lower() == "true"
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（用于依赖注入）
    
    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    from backend.db.models import Base
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def drop_db():
    """删除所有表（慎用！）"""
    from backend.db.models import Base
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")
