"""Tests for rubric dimension scoring — structured storage, parse, degradation."""
import json
import pytest
from unittest.mock import patch
from core.progress import ProgressDAO
from core.ai_review import grade_open_answer, _extract_json


@pytest.fixture
def dao(tmp_path):
    db = tmp_path / "test.db"
    d = ProgressDAO(str(db))
    yield d
    d.close()


class TestRubricStorage:
    def test_record_and_retrieve(self, dao):
        dimensions = [
            {"name": "清晰度", "score": 80, "comment": "表述清楚"},
            {"name": "完整性", "score": 70, "comment": "遗漏边界"},
        ]
        dao.record_rubric_scores("agent_dev", "spec_1", 1, dimensions)
        history = dao.rubric_history("agent_dev", "spec_1")
        assert len(history) == 1
        dims = history[0]["dimensions"]
        assert len(dims) == 2
        dim_names = {d["dimension"] for d in dims}
        assert "清晰度" in dim_names
        scores = {d["dimension"]: d["score"] for d in dims}
        assert scores["清晰度"] == 80

    def test_multiple_attempts(self, dao):
        d1 = [{"name": "A", "score": 60, "comment": "ok"}]
        d2 = [{"name": "A", "score": 85, "comment": "better"}]
        dao.record_rubric_scores("python", "p1", 1, d1)
        dao.record_rubric_scores("python", "p1", 2, d2)
        history = dao.rubric_history("python", "p1")
        assert len(history) == 2

    def test_empty_dimensions_no_op(self, dao):
        dao.record_rubric_scores("python", "p1", 1, [])
        history = dao.rubric_history("python", "p1")
        assert history == []

    def test_dimension_averages(self, dao):
        dao.record_rubric_scores("agent_dev", "p1", 1, [
            {"name": "清晰度", "score": 80, "comment": ""},
            {"name": "完整性", "score": 60, "comment": ""},
        ])
        dao.record_rubric_scores("agent_dev", "p2", 2, [
            {"name": "清晰度", "score": 90, "comment": ""},
            {"name": "完整性", "score": 70, "comment": ""},
        ])
        avgs = dao.dimension_averages()
        assert avgs["清晰度"] == 85.0
        assert avgs["完整性"] == 65.0


class TestJsonExtraction:
    def test_valid_json(self):
        text = '{"passed": true, "score": 85, "feedback": "good", "dimensions": []}'
        result = _extract_json(text)
        assert result["passed"] is True
        assert result["score"] == 85

    def test_with_code_fence(self):
        text = '```json\n{"passed": false, "score": 40, "feedback": "bad", "dimensions": []}\n```'
        result = _extract_json(text)
        assert result["passed"] is False

    def test_with_surrounding_text(self):
        text = 'Here is my evaluation:\n{"passed": true, "score": 90, "feedback": "nice", "dimensions": []}\nDone.'
        result = _extract_json(text)
        assert result["score"] == 90

    def test_invalid_json_returns_none(self):
        text = "This is not JSON at all"
        result = _extract_json(text)
        assert result is None

    def test_missing_fields_still_parses(self):
        text = '{"passed": true}'
        result = _extract_json(text)
        assert result is not None
        assert result["passed"] is True


class TestGradeOpenAnswerDegradation:
    def test_llm_unavailable_returns_graceful(self):
        problem = {"statement": "Write a spec", "rubric": "Cover goals"}
        with patch("core.ai_review._call", return_value=""):
            result = grade_open_answer("agent_dev", problem, "my answer")
            assert result["llm_ok"] is False
            assert result["passed"] is False
            assert "不可用" in result["feedback"]

    def test_non_json_response_degrades_to_text(self):
        problem = {"statement": "Q", "rubric": "R"}
        with patch("core.ai_review._call", return_value="学生通过了考核，表现不错"):
            result = grade_open_answer("agent_dev", problem, "answer")
            assert result["llm_ok"] is True
            assert result["passed"] is True
            assert result["score"] is None
            assert "通过" in result["feedback"]

    def test_non_json_with_negation(self):
        problem = {"statement": "Q", "rubric": "R"}
        with patch("core.ai_review._call", return_value="学生未通过本次评审"):
            result = grade_open_answer("agent_dev", problem, "answer")
            assert result["passed"] is False

    def test_valid_json_response(self):
        problem = {"statement": "Q", "rubric": "R"}
        response = json.dumps({
            "passed": True, "score": 82,
            "feedback": "做得好",
            "dimensions": [
                {"name": "清晰度", "score": 85, "comment": "ok"},
                {"name": "完整性", "score": 79, "comment": "minor gap"},
            ]
        })
        with patch("core.ai_review._call", return_value=response):
            result = grade_open_answer("agent_dev", problem, "answer")
            assert result["llm_ok"] is True
            assert result["passed"] is True
            assert result["score"] == 82
            assert len(result["dimensions"]) == 2
            assert result["dimensions"][0]["name"] == "清晰度"

    def test_score_out_of_range_still_parses(self):
        problem = {"statement": "Q", "rubric": "R"}
        response = json.dumps({
            "passed": True, "score": 150,
            "feedback": "overscored",
            "dimensions": []
        })
        with patch("core.ai_review._call", return_value=response):
            result = grade_open_answer("agent_dev", problem, "answer")
            assert result["score"] == 100  # clamped to 0-100 at schema validation
