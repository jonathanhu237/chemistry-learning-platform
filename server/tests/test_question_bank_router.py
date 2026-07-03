from __future__ import annotations

from server.tests.route_helpers import assert_route


def test_question_bank_overview_routes_are_registered_once() -> None:
    assert_route("/api/teacher/question-banks/chapters", "GET")
    assert_route("/api/teacher/question-banks/chapter-questions", "GET")
    assert_route("/api/teacher/question-banks/assistant/preview", "POST")
    assert_route("/api/teacher/question-banks", "GET")
    assert_route("/api/teacher/question-banks/catalog", "GET")
    assert_route("/api/teacher/question-banks/catalog/evidence-refresh", "POST")


def test_question_bank_question_routes_are_registered_once() -> None:
    assert_route("/api/teacher/question-banks/questions", "GET")
    assert_route("/api/teacher/question-banks/questions", "POST")
    assert_route("/api/teacher/question-banks/questions/{question_id}", "PATCH")
    assert_route("/api/teacher/question-banks/questions/{question_id}/publish", "POST")
    assert_route("/api/teacher/question-banks/questions/{question_id}/disable", "POST")
    assert_route("/api/teacher/question-banks/questions/{question_id}/revoke-to-draft", "POST")


def test_question_bank_import_export_routes_are_registered_once() -> None:
    assert_route("/api/teacher/question-banks/import", "POST")
    assert_route("/api/teacher/question-banks/export", "GET")
