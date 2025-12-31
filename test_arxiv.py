"""
测试ArXiv搜索功能
"""
import sys
sys.path.insert(0, '.')

from models import ResearchIntent, JournalLevel, PaperType, ResearchField
from modules.multi_source_search import search_multi_source

# 创建一个简单的研究意图
intent = ResearchIntent(
    keywords="large language model agent",
    year_start=2023,
    year_end=2024,
    journal_level=JournalLevel.ANY,
    paper_type=PaperType.ANY,
    field=ResearchField.ANY
)

print(f"搜索关键词: {intent.keywords}")
print(f"年份范围: {intent.year_start} - {intent.year_end}")
print("\n开始搜索...")

try:
    results = search_multi_source(intent, max_results_per_source=5, sources=["arxiv"])
    
    print(f"\n搜索结果:")
    for source, papers in results.items():
        print(f"\n{source}: 找到 {len(papers)} 篇论文")
        for i, paper in enumerate(papers[:3], 1):
            print(f"  {i}. {paper.title[:80]}...")
            print(f"     发表: {paper.published}, ArXiv ID: {paper.arxiv_id}")
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
