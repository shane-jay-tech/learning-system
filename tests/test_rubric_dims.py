"""Tests for dimension name standardization (core/rubric_dims)."""
from core.rubric_dims import canonical_dimension, canonical_label, DIMENSION_CANON


def test_registry_has_ten_stable_dimensions():
    ids = [d[0] for d in DIMENSION_CANON]
    assert len(ids) == len(set(ids)) == 10
    assert "correctness" in ids and "clarity" in ids


def test_maps_common_llm_names():
    assert canonical_dimension("内容完整性") == ("completeness", "完整性")
    assert canonical_dimension("要点覆盖是否全面") == ("completeness", "完整性")
    assert canonical_dimension("表述清晰") == ("clarity", "清晰度")
    assert canonical_dimension("边界情况没处理") == ("boundary", "边界处理")
    assert canonical_dimension("命名风格") == ("style", "代码风格")
    assert canonical_dimension("算法是否正确") == ("correctness", "正确性")
    assert canonical_dimension("安全风险") == ("safety", "安全性")
    assert canonical_dimension("有没有论证理由") == ("justification", "论证充分")


def test_unmatched_falls_back_to_other():
    dim_id, name = canonical_dimension("完全陌生的维度")
    assert dim_id == "other"
    assert name == "完全陌生的维度"


def test_empty_name():
    assert canonical_dimension("") == ("other", "")
    assert canonical_dimension(None) == ("other", "")


def test_label_maps_id_and_passthrough():
    assert canonical_label("clarity") == "清晰度"
    assert canonical_label("completeness") == "完整性"
    assert canonical_label("other") == "other"
    assert canonical_label("遗留自由文本") == "遗留自由文本"
