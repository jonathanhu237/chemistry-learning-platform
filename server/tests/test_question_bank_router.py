from __future__ import annotations

from server.tests.route_helpers import assert_route


def test_question_bank_overview_routes_are_registered_once() -> None:
    assert_route("/api/admin/question-banks/chapters", "GET")
    assert_route("/api/admin/question-banks/chapter-questions", "GET")
    assert_route("/api/admin/question-banks/assistant/preview", "POST")
    assert_route("/api/admin/question-banks", "GET")


def test_question_bank_question_routes_are_registered_once() -> None:
    assert_route("/api/admin/question-banks/questions", "GET")
    assert_route("/api/admin/question-banks/questions", "POST")
    assert_route("/api/admin/question-banks/questions/{question_id}", "PATCH")
    assert_route("/api/admin/question-banks/questions/{question_id}/publish", "POST")
    assert_route("/api/admin/question-banks/questions/{question_id}/disable", "POST")


def test_question_bank_import_export_routes_are_registered_once() -> None:
    assert_route("/api/admin/question-banks/import", "POST")
    assert_route("/api/admin/question-banks/export", "GET")
