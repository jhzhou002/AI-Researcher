"""
期刊/会议分区映射工具
包含常见AI领域会议和期刊的分区信息
"""

VENUE_MAPPING = {
    # 计算机视觉
    "cvpr": "CCF-A",
    "iccv": "CCF-A",
    "eccv": "CCF-B",
    "ieee transactions on pattern analysis and machine intelligence": "CCF-A",
    "tpami": "CCF-A",
    
    # 机器学习/AI
    "neurips": "CCF-A",
    "nips": "CCF-A",
    "icml": "CCF-A",
    "iclr": "CCF-A",
    "aaai": "CCF-A",
    "ijcai": "CCF-A",
    "journal of machine learning research": "CCF-A",
    "jmlr": "CCF-A",
    
    # NLP
    "acl": "CCF-A",
    "emnlp": "CCF-B",
    "naacl": "CCF-B",
    "coling": "CCF-B",
    "computational linguistics": "CCF-A",
    
    # 综合/其他
    "nature": "Nature",
    "science": "Science",
    "cell": "Cell",
    "pnas": "Q1",
    "nature communications": "Q1",
    "science advances": "Q1",
    "ieee access": "Q2",
    "arxiv": "Preprint",
    "corr": "Preprint"
}

def get_venue_partition(venue_name: str) -> str:
    """
    获取期刊/会议的分区
    
    Args:
        venue_name: 期刊/会议名称
        
    Returns:
        分区信息 (e.g., "CCF-A", "Q1", "Preprint")，如果是未知则返回None
    """
    if not venue_name:
        return None
        
    normalized_name = venue_name.lower().strip()
    
    # 精确匹配
    if normalized_name in VENUE_MAPPING:
        return VENUE_MAPPING[normalized_name]
    
    # 包含匹配 (稍微宽松一点)
    for key, value in VENUE_MAPPING.items():
        if key in normalized_name:
            # 只有当key长度足够长时才进行包含匹配，避免误判
            if len(key) > 4: 
                return value
                
    return None
