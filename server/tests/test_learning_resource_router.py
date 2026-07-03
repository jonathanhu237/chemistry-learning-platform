from __future__ import annotations

from server.app.domains.catalog.learning_resources import _build_learning_resource_overview
from server.tests.route_helpers import assert_route


def test_learning_resource_overview_route_is_registered_once() -> None:
    assert_route("/api/teacher/learning-resources/overview", "GET")


def test_experiment_knowledge_framework_overview_route_is_registered_once() -> None:
    assert_route("/api/teacher/experiment-knowledge-framework/overview", "GET")


def test_learning_resource_overview_groups_ch22_under_hydrogen_and_p_contexts() -> None:
    overview = _build_learning_resource_overview(
        chapters=[
            {"chapter_id": "CH22", "chapter_number": 22, "chapter_title": "第 22 章 氢和稀有气体"},
            {"chapter_id": "CH00", "chapter_number": None, "chapter_title": "通识/跨章节"},
        ],
        units=[],
        knowledge_points=[],
        experiments=[],
        questions=[],
        bindings_by_experiment={},
    )

    areas = {area["area_id"]: area for area in overview["areas"]}
    assert [area["area_id"] for area in overview["areas"]] == ["hydrogen", "p", "general"]
    assert areas["hydrogen"]["group_ids"] == ["chapter:CH22:hydrogen"]
    assert areas["p"]["group_ids"] == ["chapter:CH22:p"]
    assert areas["general"]["kind"] == "general"

    groups = {group["id"]: group for group in overview["groups"]}
    assert groups["chapter:CH22:hydrogen"]["area_id"] == "hydrogen"
    assert groups["chapter:CH22:p"]["area_id"] == "p"
    assert groups["general:CH00"]["area_id"] == "general"
