from __future__ import annotations

from server.app.services.student_experiment_service import _normalize_answer
from server.tests.route_helpers import assert_route


def test_student_experiment_submit_route_is_registered_once() -> None:
    assert_route("/api/experiment-questions/submit", "POST")


def test_student_true_false_answer_normalization_preserves_cn_aliases() -> None:
    assert _normalize_answer("true_false", "对") == {"value": True}
    assert _normalize_answer("true_false", "正确") == {"value": True}
    assert _normalize_answer("true_false", "错") == {"value": False}
    assert _normalize_answer("true_false", "错误") == {"value": False}
