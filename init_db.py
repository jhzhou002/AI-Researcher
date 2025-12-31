"""
数据库初始化脚本 - MySQL版本
"""
from sqlalchemy import create_engine, text
from backend.db.models import Base
import sys


def create_database():
    """创建数据库（如果不存在）"""
    # 连接到MySQL服务器（不指定数据库）
    admin_url = "mysql+pymysql://remote:Zhjh0704.@49.235.74.98:3306"
    
    try:
        engine = create_engine(admin_url)
        with engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(text(
                "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='ai_researcher'"
            ))
            
            if not result.fetchone():
                # 创建数据库
                conn.execute(text("CREATE DATABASE ai_researcher CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                print("✅ Database 'ai_researcher' created successfully!")
            else:
                print("ℹ️  Database 'ai_researcher' already exists")
        
        engine.dispose()
        return True
    
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False


def create_tables():
    """创建所有表"""
    # 连接到ai_researcher数据库
    db_url = "mysql+pymysql://remote:Zhjh0704.@49.235.74.98:3306/ai_researcher"
    
    try:
        engine = create_engine(db_url)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print("✅ All tables created successfully!")
        
        # 列出创建的表
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        
        engine.dispose()
        return True
    
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("AI-Researcher Database Initialization")
    print("=" * 60)
    print()
    
    # 步骤1：创建数据库
    print("Step 1: Creating database...")
    if not create_database():
        print("\n❌ Failed to create database. Exiting.")
        sys.exit(1)
    
    print()
    
    # 步骤2：创建表
    print("Step 2: Creating tables...")
    if not create_tables():
        print("\n❌ Failed to create tables. Exiting.")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ Database initialization completed successfully!")
    print("=" * 60)
    print()
    print("Database URL: mysql+pymysql://remote:***@49.235.74.98:3306/ai_researcher")
    print()


if __name__ == "__main__":
    main()
