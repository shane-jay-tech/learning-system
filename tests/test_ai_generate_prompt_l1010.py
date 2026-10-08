"""core/ai_generate _trim + _build_user_prompt 首测（l1010-41）。

与 ai_review._trim 钉桩面（test_ai_review_strategy.py 六用例）互补的分叉防护：
两个同构 trim_text 薄包装任一侧独立漂移时本件给红灯。_build_user_prompt 做
四段拼装形状测（语言/难度/标题 200/描述 1500/期望输出 500，超长截断，缺字段回落）。
不与 tests/test_ai_generate.py 既有 6 例（_strip_fences/_parse_json/generate_variant）重复。
纯函数面：零 LLM、零子进程。
"""
import core.ai_generate as ai_generate


class TestTrim:
    def test_default_limit_is_2000(self):
        cut = ai_generate._trim("x" * 2001)
        assert cut != "x" * 2001
        assert cut.startswith("x" * 2000)
        assert "已截断" in cut

    def test_exact_boundary_passthrough(self):
        assert ai_generate._trim("x" * 2000) == "x" * 2000

    def test_same_semantics_as_trim_text(self):
        from core.utils import trim_text
        long_s = "y" * 2600
        assert ai_generate._trim(long_s) == trim_text(long_s, 2000)

    def test_custom_n(self):
        # 底层 trim_text 语义：超限截断并附标记；短串原样；空串空返
        assert ai_generate._trim("abcdef", 4) == "abcd" + "\n[... 已截断（>4 字符）]"
        assert ai_generate._trim("abc", 4) == "abc"
        assert ai_generate._trim("", 10) == ""


class TestBuildUserPrompt:
    def test_four_sections_present(self):
        original = {"difficulty": 3, "title": "两数之和", "statement": "求和", "expected_output": "3"}
        prompt = ai_generate._build_user_prompt("python", original)
        assert "语言：python" in prompt
        assert "原题难度：3/5" in prompt
        assert "原题标题：两数之和" in prompt
        assert "原题描述：" in prompt and "求和" in prompt
        assert "原题期望输出：3" in prompt

    def test_statement_truncated_to_1500(self):
        original = {"difficulty": 1, "title": "t", "statement": "s" * 1600, "expected_output": ""}
        prompt = ai_generate._build_user_prompt("python", original)
        assert ("s" * 1501) not in prompt   # 超长段被截断
        assert ("s" * 1500) in prompt       # 截断保留量

    def test_missing_fields_fall_back_empty(self):
        prompt = ai_generate._build_user_prompt("r", {})
        assert "原题难度：1/5" in prompt     # difficulty 缺省 1
        assert "原题标题：" in prompt        # title 回落空串
        assert "原题期望输出：" in prompt    # expected_output 回落空串
