"""
系统功能测试脚本
测试LLM接入、数据库连接和核心模块
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("AI-Researcher 系统功能测试")
print("=" * 60)
print()

# ==================== 测试1: LLM连接 ====================
print("【测试1】LLM连接测试...")
try:
    from llm_config import init_llms_from_env
    from llm import llm_manager
    
    init_llms_from_env()
    
    available_llms = llm_manager.list_llms()
    default_llm = llm_manager.get_default_llm_name()
    
    print(f"✅ LLM初始化成功")
    print(f"   可用LLM: {', '.join(available_llms)}")
    print(f"   默认LLM: {default_llm}")
    
    # 测试调用
    if available_llms:
        print(f"\n   测试调用 {default_llm}...")
        response = llm_manager.chat(
            messages=[
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": "用一句话介绍你自己"}
            ],
            temperature=0.7
        )
        print(f"   响应: {response.content[:100]}...")
        print(f"   Tokens: {response.tokens_used}, 成本: ${response.cost:.6f}")
        print("✅ LLM调用成功")
    else:
        print("⚠️  没有配置可用的LLM")
    
except Exception as e:
    print(f"❌ LLM测试失败: {e}")

print()

# ==================== 测试2: 数据库连接 ====================
print("【测试2】数据库连接测试...")
try:
    from backend.db.database import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DATABASE()"))
        db_name = result.fetchone()[0]
        print(f"✅ 数据库连接成功: {db_name}")
        
        # 检查表
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        print(f"   数据表数量: {len(tables)}")
        print(f"   表: {', '.join(tables[:5])}...")
    
except Exception as e:
    print(f"❌ 数据库测试失败: {e}")

print()

# ==================== 测试3: 核心模块导入 ====================
print("【测试3】核心模块导入测试...")
try:
    from modules import research_intent, literature_discovery, paper_reading
    from modules import landscape_analysis, idea_generation, method_design
    from modules import experiment_planning, paper_drafting
    from workflow import ResearchWorkflow
    
    print("✅ 所有核心模块导入成功")
    print("   - research_intent ✓")
    print("   - literature_discovery ✓")
    print("   - paper_reading ✓")
    print("   - landscape_analysis ✓")
    print("   - idea_generation ✓")
    print("   - method_design ✓")
    print("   - experiment_planning ✓")
    print("   - paper_drafting ✓")
    print("   - ResearchWorkflow ✓")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    import traceback
    traceback.print_exc()

print()

# ==================== 测试4: API路由 ====================
print("【测试4】API路由测试...")
try:
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # 测试根路由
    response = client.get("/")
    assert response.status_code == 200
    print("✅ 根路由响应正常")
    
    # 测试健康检查
    response = client.get("/health")
    assert response.status_code == 200
    health_data = response.json()
    print(f"✅ 健康检查通过")
    print(f"   状态: {health_data.get('status')}")
    print(f"   可用LLM: {health_data.get('llms_available')}")
    
except Exception as e:
    print(f"❌ API测试失败: {e}")

print()

# ==================== 测试5: 简单工作流测试 ====================
print("【测试5】工作流测试（仅验证创建）...")
try:
    # 注意：需要有可用的LLM API密钥才能完整测试
    if not os.getenv("DEEPSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未配置LLM API密钥，跳过工作流测试")
    else:
        from models import ResearchIntent, JournalLevel, PaperType, ResearchField
        
        # 创建研究意图
        intent = ResearchIntent(
            keywords="large language model agents",
            year_start=2023,
            year_end=2024,
            journal_level=JournalLevel.ANY,
            paper_type=PaperType.RESEARCH,
            field=ResearchField.NLP
        )
        
        print("✅ 研究意图创建成功")
        print(f"   主题: {intent.keywords}")
        print(f"   时间范围: {intent.year_start}-{intent.year_end}")
        
        # 注意：完整的文献检索需要时间，这里只验证创建
        print("   （完整工作流测试需要较长时间，已跳过）")

except Exception as e:
    print(f"⚠️  工作流测试: {e}")

print()

# ==================== 总结 ====================
print("=" * 60)
print("测试完成！")
print("=" * 60)
print()
print("📋 下一步操作建议：")
print("1. 复制 env_config.txt 内容到 .env 文件（手动创建）")
print("2. 安装缺失的依赖: pip install python-jose passlib")
print("3. 启动API服务: python run.py")
print("4. 访问 http://localhost:8000/docs 查看API文档")
print("5. 使用API创建研究项目并测试完整流程")
print()
