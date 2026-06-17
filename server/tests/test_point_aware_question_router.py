from __future__ import annotations

from server.tests.route_helpers import assert_route


def test_point_aware_suggestion_route_stays_registered() -> None:
    assert_route("/api/admin/question-banks/point-aware-suggestions", "POST")
