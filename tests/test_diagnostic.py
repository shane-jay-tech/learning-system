import json

import pytest

from core.diagnostic import (
    DIAGNOSTIC_QUESTIONS,
    evaluate_diagnostic,
    get_diagnostic_result,
    save_diagnostic_result,
)
from core.progress import ProgressDAO


@pytest.fixture
def dao(tmp_path):
    db = ProgressDAO(str(tmp_path / "diagnostic.db"))
    yield db
    db.close()


def _correct(*question_ids):
    wanted = set(question_ids)
    return {q["id"]: q["answer"] for q in DIAGNOSTIC_QUESTIONS if q["id"] in wanted}


def test_zero_base_for_empty_or_single_correct_answer():
    assert evaluate_diagnostic({})["recommendation_key"] == "zero_base"
    result = evaluate_diagnostic(_correct("d1_python_read"))
    assert result["recommendation_key"] == "zero_base"
    assert result["total_correct"] == 1
    assert result["total_questions"] == len(DIAGNOSTIC_QUESTIONS)


def test_python_foundation_recommendation():
    result = evaluate_diagnostic(_correct("d1_python_read", "d2_loop"))
    assert result["recommendation_key"] == "has_python"
    assert result["skills"]["python_basics"] == 2


def test_data_recommendation_requires_sql_and_data():
    answers = _correct("d3_sql", "d4_dataframe")
    result = evaluate_diagnostic(answers)
    assert result["recommendation_key"] == "data_oriented"


def test_all_good_takes_precedence_at_four_correct():
    answers = _correct("d1_python_read", "d2_loop", "d3_sql", "d4_dataframe")
    result = evaluate_diagnostic(answers)
    assert result["recommendation_key"] == "all_good"
    assert result["total_correct"] == 4


def test_wrong_types_missing_and_extra_answers_do_not_score():
    answers = {"d1_python_read": "1", "unknown": 0, "d3_sql": None}
    result = evaluate_diagnostic(answers)
    assert result["total_correct"] == 0
    assert result["recommendation_key"] == "zero_base"


def test_diagnostic_result_round_trip(dao):
    result = evaluate_diagnostic(_correct("d1_python_read", "d2_loop"))
    save_diagnostic_result(dao, result)

    assert get_diagnostic_result(dao) == result
    assert dao.get_meta("diagnostic_recommendation") == "has_python"
    assert json.loads(dao.get_meta("diagnostic_result"))["total_correct"] == 2


@pytest.mark.parametrize("raw", ["{not json", "[] trailing", "null"])
def test_invalid_saved_result_is_treated_as_missing(dao, raw):
    dao.set_meta("diagnostic_result", raw)
    assert get_diagnostic_result(dao) is None
