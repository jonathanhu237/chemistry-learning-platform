from __future__ import annotations

from server.app.domains.analytics.read_models import (
    _attempt_primary_points,
    _build_experiment_groups,
    _experiment_group_info,
)
from server.tests.route_helpers import assert_route


def test_class_dashboard_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/dashboard", "GET")


def test_student_report_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/students/{student_id}", "GET")


def test_class_weak_points_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/weak-points", "GET")


def test_class_export_route_is_registered_once() -> None:
    assert_route("/api/admin/analytics/classes/{class_id}/export", "GET")


def test_experiment_group_info_uses_primary_chapter_element_family() -> None:
    group = _experiment_group_info(
        {
            "id": "exp-ch13-bleach",
            "code": "EXP13",
            "metadata": {"parent_code": "CAT-CH14-old"},
            "chapter_bindings": [
                {
                    "chapter_id": "CH14",
                    "chapter_title": "第 14 章 氧族元素",
                    "coverage_type": "partial",
                },
                {
                    "chapter_id": "CH13",
                    "chapter_title": "第 13 章 卤族元素",
                    "coverage_type": "primary",
                },
            ],
        }
    )

    assert group == {
        "id": "CH13",
        "code": "CH13",
        "title": "卤族元素",
        "raw_title": "第 13 章 卤族元素",
    }


def test_experiment_group_info_falls_back_from_catalog_code_to_element_family() -> None:
    group = _experiment_group_info(
        {
            "id": "exp-ch20-metal",
            "code": "EXP20",
            "metadata": {"parent_code": "CAT-CH20-f99cb352", "parent_title": "旧目录标题"},
            "chapter_bindings": [],
        }
    )

    assert group["id"] == "CH20"
    assert group["title"] == "d 区过渡金属元素"


def test_experiment_group_info_uses_catalog_chapter_metadata_without_binding() -> None:
    group = _experiment_group_info(
        {
            "id": "catalog-backed-experiment",
            "metadata": {
                "catalog_chapter_id": "CH18",
                "catalog_root_title": "CAT-CH18-root",
            },
            "chapter_bindings": [],
        }
    )

    assert group == {
        "id": "CH18",
        "code": "CH18",
        "title": "碱金属和碱土金属",
        "raw_title": "CAT-CH18-root",
    }


def test_unknown_catalog_chapter_stays_unmapped_instead_of_using_a_stale_binding() -> None:
    group = _experiment_group_info(
        {
            "id": "catalog-backed-new-chapter",
            "metadata": {
                "catalog_chapter_id": "CH23",
                "catalog_root_title": "第 23 章 新内容",
            },
            "chapter_bindings": [
                {
                    "chapter_id": "CH13",
                    "chapter_title": "历史绑定",
                    "coverage_type": "primary",
                }
            ],
        }
    )

    assert group == {
        "id": "unmapped",
        "code": "unmapped",
        "title": "未映射元素族",
        "raw_title": "第 23 章 新内容",
    }


def test_unknown_chapters_share_explicit_unmapped_element_family() -> None:
    experiments = [
        {
            "id": "exp-new-chapter",
            "code": "EXP99",
            "metadata": {},
            "chapter_bindings": [{"chapter_id": "CH23", "chapter_title": "第 23 章 新内容"}],
        },
        {
            "id": "exp-no-chapter",
            "code": "EXP-X",
            "metadata": {"parent_title": "临时目录"},
            "chapter_bindings": [],
        },
    ]

    assert _build_experiment_groups(experiments) == [
        {
            "id": "unmapped",
            "code": "unmapped",
            "title": "未映射元素族",
            "raw_title": "第 23 章 新内容",
            "experiment_ids": ["exp-new-chapter", "exp-no-chapter"],
            "experiment_count": 2,
        }
    ]


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
