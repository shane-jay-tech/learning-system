"""is_degraded_feedback 直接钉桩首测（l1010-44，l930-19 落地复查腿）。

该函数是 judge.py:401 生产调用（llm_degraded 可观测位）与 l1006-04/l1004-08
C 案①「文案即标记」契约的判定源，此前仅被 offline_fallback 文案间接覆盖。
本件把四态行为钉死：断线文案真／普通点评假／空串假／None 假。
"""
import core.ai_review as ai_review


def test_offline_fallback_text_is_true():
    text = "AI 点评暂时不可用（网络或服务异常），请稍后再试。判题本身不受影响。"
    assert ai_review.is_degraded_feedback(text) is True


def test_normal_feedback_is_false():
    assert ai_review.is_degraded_feedback("整体思路正确，第二处循环边界写反了，建议用 <= 而非 <。") is False


def test_empty_string_is_false():
    assert ai_review.is_degraded_feedback("") is False


def test_none_is_false():
    assert ai_review.is_degraded_feedback(None) is False
