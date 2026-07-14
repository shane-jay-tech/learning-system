"""Golden answer regression test for AI scoring schema.

Validates that grade_open_answer returns structurally valid results
for the golden set (does NOT call LLM — tests schema validation logic only).
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GOLDEN_FILE = ROOT / "tests" / "fixtures" / "rubric_golden" / "golden_set.yaml"


def _load_golden():
    with open(GOLDEN_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


GOLDEN = _load_golden()


def _fake_response(passed: bool, score: int, dims=2):
    """Generate a fake LLM JSON response."""
    dimensions = [
        {"name": f"dim_{i}", "score": score - i * 5, "comment": f"comment {i}"}
        for i in range(dims)
    ]
    return json.dumps({
        "passed": passed,
        "score": score,
        "feedback": "test feedback",
        "dimensions": dimensions,
    })


class TestGoldenSchemaValidation:
    """Test that golden set has at least 20 entries with proper structure."""

    def test_golden_set_has_minimum_entries(self):
        assert len(GOLDEN) >= 20

    def test_golden_entries_have_required_fields(self):
        for entry in GOLDEN:
            assert "id" in entry
            assert "problem_id" in entry
            assert "lang" in entry
            assert "answer" in entry
            assert "expected" in entry
            exp = entry["expected"]
            assert "score_min" in exp
            assert "score_max" in exp
            assert "passed" in exp

    def test_score_ranges_are_valid(self):
        for entry in GOLDEN:
            exp = entry["expected"]
            assert 0 <= exp["score_min"] <= 100
            assert 0 <= exp["score_max"] <= 100
            assert exp["score_min"] <= exp["score_max"]


class TestSchemaValidationLogic:
    """Test that score clamping and consistency checks work correctly."""

    def test_score_clamped_to_100(self):
        from core.ai_review import grade_open_answer
        response = json.dumps({"passed": True, "score": 150, "feedback": "ok", "dimensions": []})
        with patch("core.ai_review._call", return_value=response):
            result = grade_open_answer("python", {"statement": "Q"}, "A")
            assert result["score"] == 100

    def test_score_clamped_to_0(self):
        from core.ai_review import grade_open_answer
        response = json.dumps({"passed": False, "score": -10, "feedback": "bad", "dimensions": []})
        with patch("core.ai_review._call", return_value=response):
            result = grade_open_answer("python", {"statement": "Q"}, "A")
            assert result["score"] == 0

    def test_high_score_forces_passed(self):
        from core.ai_review import grade_open_answer
        response = json.dumps({"passed": False, "score": 85, "feedback": "ok", "dimensions": []})
        with patch("core.ai_review._call", return_value=response):
            result = grade_open_answer("python", {"statement": "Q"}, "A")
            assert result["passed"] is True

    def test_low_score_forces_failed(self):
        from core.ai_review import grade_open_answer
        response = json.dumps({"passed": True, "score": 30, "feedback": "ok", "dimensions": []})
        with patch("core.ai_review._call", return_value=response):
            result = grade_open_answer("python", {"statement": "Q"}, "A")
            assert result["passed"] is False

    def test_empty_dimension_name_filtered(self):
        from core.ai_review import grade_open_answer
        response = json.dumps({
            "passed": True, "score": 80, "feedback": "ok",
            "dimensions": [
                {"name": "clarity", "score": 80, "comment": "good"},
                {"name": "", "score": 50, "comment": "empty name"},
                {"name": "logic", "score": 70, "comment": "ok"},
            ]
        })
        with patch("core.ai_review._call", return_value=response):
            result = grade_open_answer("python", {"statement": "Q"}, "A")
            assert len(result["dimensions"]) == 2
            names = {d["name"] for d in result["dimensions"]}
            assert "clarity" in names
            assert "logic" in names

    def test_dimension_score_clamped(self):
        from core.ai_review import grade_open_answer
        response = json.dumps({
            "passed": True, "score": 80, "feedback": "ok",
            "dimensions": [{"name": "x", "score": 200, "comment": "over"}]
        })
        with patch("core.ai_review._call", return_value=response):
            result = grade_open_answer("python", {"statement": "Q"}, "A")
            assert result["dimensions"][0]["score"] == 100

    def test_prompt_version_and_model_returned(self):
        from core.ai_review import grade_open_answer, PROMPT_VERSIONS
        response = json.dumps({"passed": True, "score": 80, "feedback": "ok", "dimensions": []})
        with patch("core.ai_review._call", return_value=response):
            result = grade_open_answer("python", {"statement": "Q", "rubric": "R"}, "A")
            assert result["prompt_version"] == PROMPT_VERSIONS["open_scoring"]
            assert result["model"] is not None
