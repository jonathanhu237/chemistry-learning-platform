from __future__ import annotations

from server.tests.route_helpers import assert_route


def test_question_workbench_routes_stay_registered() -> None:
    assert_route("/api/teacher/question-banks/workbench-sessions", "POST")
    assert_route("/api/teacher/question-banks/workbench-sessions/{session_id}", "GET")
    assert_route("/api/teacher/question-banks/workbench-sessions/{session_id}/evidence-cache/clear", "POST")
    assert_route("/api/teacher/question-banks/workbench-sessions/{session_id}/messages", "POST")
    assert_route("/api/teacher/question-banks/workbench-sessions/{session_id}/messages/stream", "POST")
    assert_route("/api/teacher/question-banks/workbench-candidates/{candidate_id}/reject", "POST")
    assert_route("/api/teacher/question-banks/workbench-candidates/{candidate_id}/publish", "POST")
