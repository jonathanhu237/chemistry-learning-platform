from __future__ import annotations

from server.tests.route_helpers import assert_route


def test_question_draft_routes_are_registered_once() -> None:
    assert_route("/api/admin/question-banks/drafts", "GET")
    assert_route("/api/admin/question-banks/drafts/{draft_id}", "PATCH")
    assert_route("/api/admin/question-banks/drafts/{draft_id}/publish", "POST")
    assert_route("/api/admin/question-banks/drafts/{draft_id}/reject", "POST")
