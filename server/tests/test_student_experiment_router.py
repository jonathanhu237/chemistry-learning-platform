from __future__ import annotations

from server.app.domains.assessments.student_experiment import _attempt_diagnostic_metadata, _normalize_answer
from server.tests.route_helpers import assert_route


def test_student_experiment_submit_route_is_registered_once() -> None:
    assert_route("/api/experiment-questions/submit", "POST")


def test_attempt_diagnostic_metadata_prefers_question_point_node_ids() -> None:
    metadata = _attempt_diagnostic_metadata(
        {
            "question_type": "single_choice",
            "primary_point_node_ids": ["cat-point-column"],
            "metadata": {
                "primary_point_node_ids": ["cat-point-metadata"],
                "primary_point_keys": ["legacy-point"],
                "option_links": [
                    {
                        "label": "A",
                        "point_node_id": "cat-point-column",
                        "point_key": "legacy-point",
                        "role": "correct_evidence",
                    }
                ],
            },
        },
        "A",
        True,
    )

    assert metadata["point_node_id"] == "cat-point-column"
    assert metadata["primary_point_node_ids"] == ["cat-point-column"]
    assert metadata["selected_option_link"]["point_node_id"] == "cat-point-column"


def test_student_true_false_answer_normalization_preserves_cn_aliases() -> None:
    assert _normalize_answer("true_false", "对") == {"value": True}
    assert _normalize_answer("true_false", "正确") == {"value": True}
    assert _normalize_answer("true_false", "错") == {"value": False}
    assert _normalize_answer("true_false", "错误") == {"value": False}
