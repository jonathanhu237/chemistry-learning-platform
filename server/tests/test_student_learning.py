from __future__ import annotations

from server.app.services.student_learning_service import (
    _areas_for_groups,
    _build_parent_groups,
    _choose_recommendation,
)
from server.tests.route_helpers import assert_route


def _experiment(
    experiment_id: str,
    *,
    code: str,
    title: str,
    parent_code: str,
    parent_title: str,
    chapter_id: str,
    display_order: int,
    questions: int = 0,
) -> dict[str, object]:
    return {
        "id": experiment_id,
        "code": code,
        "title": title,
        "summary": f"{title} summary",
        "status": "published",
        "display_order": display_order,
        "metadata": {
            "parent_code": parent_code,
            "parent_title": parent_title,
            "module_display_title": "模块",
            "video_candidates": ["观察点"],
        },
        "chapter_bindings": [{"chapter_id": chapter_id, "coverage_type": "primary", "sort_order": 1}],
        "media_resources": [],
        "published_question_count": questions,
    }


def test_student_learning_routes_are_registered() -> None:
    assert_route("/api/student/learning-home", "GET")
    assert_route("/api/student/experiment-groups/{parent_code}", "GET")
    assert_route("/api/student/experiments/{experiment_id}", "GET")


def test_parent_groups_follow_experiment_parent_titles_and_hide_empty_f_area() -> None:
    groups = _build_parent_groups(
        [
            _experiment(
                "EXP_19_1_01",
                code="19-1-01",
                title="氯、溴、碘的置换次序",
                parent_code="19-1",
                parent_title="实验 19-1 卤素",
                chapter_id="CH13",
                display_order=1,
                questions=4,
            ),
            _experiment(
                "EXP_20_2_01",
                code="20-2-01",
                title="氢氧化物的酸碱性",
                parent_code="20-2",
                parent_title="实验 20-2 d 区元素化合物的性质（一）",
                chapter_id="CH20",
                display_order=20,
                questions=2,
            ),
            _experiment(
                "EXP_21_1_01",
                code="21-1-01",
                title="镧系性质",
                parent_code="21-1",
                parent_title="实验 21-1 镧系",
                chapter_id="CH21",
                display_order=99,
            ),
        ]
    )

    assert [group.parent_code for group in groups] == ["19-1", "20-2"]
    assert groups[0].area_id == "p"
    assert groups[0].parent_title == "实验 19-1 卤素"

    areas = {area.area_id: area for area in _areas_for_groups(groups)}
    assert areas["f"].enabled is False
    assert areas["p"].question_count == 4


def test_recommendation_falls_back_when_pretest_area_has_no_experiments() -> None:
    groups = _build_parent_groups(
        [
            _experiment(
                "EXP_19_1_01",
                code="19-1-01",
                title="氯、溴、碘的置换次序",
                parent_code="19-1",
                parent_title="实验 19-1 卤素",
                chapter_id="CH13",
                display_order=1,
            ),
            _experiment(
                "EXP_18_1_01",
                code="19-6-01",
                title="焰色反应",
                parent_code="19-6",
                parent_title="实验 19-6 碱金属和碱土金属",
                chapter_id="CH18",
                display_order=18,
            ),
        ]
    )

    assert _choose_recommendation(groups=groups, pretest_area_id="f", mastery_chapter_id=None) == ("p", "19-1")
    assert _choose_recommendation(groups=groups, pretest_area_id="s", mastery_chapter_id="CH18") == ("s", "19-6")
