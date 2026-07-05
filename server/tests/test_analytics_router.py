from __future__ import annotations

from server.app.domains.analytics.read_models import _attempt_primary_points, _experiment_group_info
from server.tests.route_helpers import assert_route


def test_class_dashboard_route_is_registered_once() -> None:
    assert_route("/api/teacher/analytics/classes/{class_id}/dashboard", "GET")


def test_student_report_route_is_registered_once() -> None:
    assert_route("/api/teacher/analytics/classes/{class_id}/students/{student_id}", "GET")


def test_class_weak_points_route_is_registered_once() -> None:
    assert_route("/api/teacher/analytics/classes/{class_id}/weak-points", "GET")


def test_class_export_route_is_registered_once() -> None:
    assert_route("/api/teacher/analytics/classes/{class_id}/export", "GET")


def test_experiment_group_info_uses_element_family_chapter() -> None:
    group = _experiment_group_info(
        {
            "id": "exp-ch13-bleach",
            "code": "EXP13",
            "metadata": {"parent_code": "CAT-CH13-f99cb352", "parent_title": "CAT-CH13-f99cb352"},
            "chapter_bindings": [{"chapter_id": "CH13", "chapter_title": "第 13 章 卤族元素"}],
        }
    )

    assert group == {
        "id": "CH13",
        "code": "CH13",
        "title": "卤族元素",
        "raw_title": "第 13 章 卤族元素",
    }


def test_experiment_group_info_falls_back_from_catalog_code_to_family() -> None:
    group = _experiment_group_info(
        {
            "id": "exp-ch14-h2o2",
            "code": "EXP14",
            "metadata": {"parent_code": "CAT-CH14-b62492d6", "parent_title": "CAT-CH14-b62492d6"},
            "chapter_bindings": [],
        }
    )

    assert group["id"] == "CH14"
    assert group["title"] == "氧族元素"


def test_experiment_group_info_uses_catalog_chapter_metadata() -> None:
    group = _experiment_group_info(
        {
            "id": "catalog-exp-f99cb352071bd2135071d30a",
            "code": "CAT-CH13-f99cb352",
            "title": "卤素单质在不同溶剂中的溶解性",
            "metadata": {
                "catalog_chapter_id": "CH13",
                "catalog_root_title": "卤素单质在不同溶剂中的溶解性",
            },
            "chapter_bindings": [],
        }
    )

    assert group == {
        "id": "CH13",
        "code": "CH13",
        "title": "卤族元素",
        "raw_title": "卤素单质在不同溶剂中的溶解性",
    }


def test_attempt_primary_points_prefers_stable_node_identity() -> None:
    points = _attempt_primary_points(
        {
            "point_node_id": "cat-point-fallback",
            "metadata": {
                "primary_points": [{"point_key": "legacy-point", "point_title": "Legacy title"}],
                "primary_point_node_ids": ["cat-point-1"],
            },
            "question_metadata": {"primary_point_keys": ["legacy-point"]},
        }
    )

    assert points == [
        {
            "point_key": "legacy-point",
            "point_title": "Legacy title",
            "point_node_id": "cat-point-1",
        }
    ]


def test_attempt_primary_points_falls_back_to_attempt_point_node_id() -> None:
    points = _attempt_primary_points({"point_node_id": "cat-point-fallback", "metadata": {}, "question_metadata": {}})

    assert points == [
        {
            "point_node_id": "cat-point-fallback",
            "point_title": "cat-point-fallback",
            "point_key": "",
        }
    ]
