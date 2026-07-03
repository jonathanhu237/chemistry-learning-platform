from __future__ import annotations

import inspect

from server.app.domains.questions import drafts
from server.tests.route_helpers import assert_route


def test_question_draft_routes_are_registered_once() -> None:
    assert_route("/api/teacher/question-banks/drafts", "GET")
    assert_route("/api/teacher/question-banks/drafts/{draft_id}", "PATCH")
    assert_route("/api/teacher/question-banks/drafts/{draft_id}/publish", "POST")
    assert_route("/api/teacher/question-banks/drafts/{draft_id}/reject", "POST")


def test_question_draft_list_only_returns_pending_drafts() -> None:
    source = inspect.getsource(drafts.list_question_drafts)

    assert "d.status = 'draft'" in source
