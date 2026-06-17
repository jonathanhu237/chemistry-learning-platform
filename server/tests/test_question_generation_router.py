from __future__ import annotations

from server.tests.route_helpers import assert_route


def test_question_generation_route_is_registered_once() -> None:
    assert_route("/api/admin/question-banks/generate", "POST")
