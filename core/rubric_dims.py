"""能力维度标准化：LLM 自由文本维度名 → 规范 dimension_id。

开放题评分时 LLM 会产出各种维度名（"清晰度""内容完整性""表达是否清楚"…），
自由文本无法跨题比较趋势。这里用关键词映射收敛到 10 个规范维度，
dashboard 能力趋势才真正可读、可追踪。
"""
from typing import Tuple

# (dimension_id, 规范名, 关键词列表)
DIMENSION_CANON = [
    ("correctness", "正确性", ["正确", "答案", "结果", "逻辑", "算法", "准确"]),
    ("completeness", "完整性", ["完整", "遗漏", "覆盖", "全面", "要点", "要素", "齐全"]),
    ("clarity", "清晰度", ["清晰", "表达", "表述", "结构", "条理", "易读"]),
    ("boundary", "边界处理", ["边界", "异常", "错误处理", "极端", "特殊情况", "edge", "例外"]),
    ("style", "代码风格", ["风格", "命名", "可读", "规范", "简洁", "注释", "习惯"]),
    ("efficiency", "效率", ["效率", "性能", "复杂度", "优化", "冗余"]),
    ("safety", "安全性", ["安全", "风险", "漏洞", "隐私", "敏感"]),
    ("analysis", "分析深度", ["分析", "深度", "洞察", "思考", "理解"]),
    ("justification", "论证充分", ["论证", "理由", "依据", "解释", "说明", "后果", "影响"]),
    ("format", "格式规范", ["格式", "排版", "规范"]),
]

def canonical_dimension(name: str) -> Tuple[str, str]:
    """返回 (dimension_id, 规范名)。未命中返回 ("other", 原名)。"""
    name = (name or "").strip()
    if not name:
        return "other", name
    for dim_id, canon, keywords in DIMENSION_CANON:
        for kw in keywords:
            if kw in name:
                return dim_id, canon
    return "other", name


def canonical_label(key: str) -> str:
    """维度 key（dimension_id 或遗留的自由文本 name）→ 展示名。"""
    for dim_id, canon, _ in DIMENSION_CANON:
        if key == dim_id:
            return canon
    return key  # 遗留自由文本 / other 时原样展示
