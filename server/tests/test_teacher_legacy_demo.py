from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from server.app.app_runtime.main import app
from server.app.api.teacher import teacher_legacy
from server.app.auth import AuthUser, get_current_user
from server.tests.route_helpers import assert_route


def _teacher_user() -> AuthUser:
    return AuthUser(
        id="teacher-legacy-demo-user",
        username="teacher",
        role="teacher",
        display_name="Legacy Demo Teacher",
        status="active",
        must_change_password=False,
    )


def test_teacher_legacy_demo_routes_are_registered_and_get_only() -> None:
    routes = [
        "/api/teacher/legacy/teacher-demo/overview",
        "/api/teacher/legacy/teacher-demo/video-resources",
        "/api/teacher/legacy/teacher-demo/question-resources",
        "/api/teacher/legacy/teacher-demo/classes",
        "/api/teacher/legacy/teacher-demo/classes/{class_id}/analytics",
        "/api/teacher/legacy/teacher-demo/classes/{class_id}/weak-points",
        "/api/teacher/legacy/teacher-demo/evaluation-system",
    ]
    for route in routes:
        assert_route(route, "GET")

    teacher_demo_paths = {
        path: methods
        for path, methods in app.openapi()["paths"].items()
        if path.startswith("/api/teacher/legacy/teacher-demo")
    }
    assert set(teacher_demo_paths) == set(routes)
    assert {method for methods in teacher_demo_paths.values() for method in methods} == {"get"}


def test_teacher_legacy_demo_requires_teacher_session() -> None:
    with TestClient(app) as client:
        response = client.get("/api/teacher/legacy/teacher-demo/overview")

    assert response.status_code in {401, 403}


def test_teacher_legacy_demo_payloads_are_old_facing_and_read_only(monkeypatch) -> None:
    monkeypatch.setattr(
        teacher_legacy,
        "teacher_legacy_overview",
        lambda _user: {
            "metrics": [{"key": "video_points", "label": "实验视频点位", "value": 2, "unit": "个", "description": "点位"}],
            "loop": [{"title": "实验视频学习", "description": "先学习再测评"}],
            "resource_summary": {"video_point_total": 2},
        },
    )
    monkeypatch.setattr(
        teacher_legacy,
        "teacher_legacy_video_resources",
        lambda q="": {
            "total": 1,
            "items": [
                {
                    "node_id": "point-1",
                    "chapter_id": "chapter-1",
                    "title": "氯水漂白性实验",
                    "summary": "观察现象。",
                    "catalog_path": ["第13章", "氯的氧化性"],
                    "media_count": 1,
                    "published_media_count": 1,
                    "question_count": 4,
                    "published_question_count": 4,
                    "has_video": True,
                    "is_recommended": True,
                    "resource_status": "已绑定视频",
                }
            ],
        },
    )
    monkeypatch.setattr(
        teacher_legacy,
        "teacher_legacy_question_resources",
        lambda: {
            "total": 1,
            "totals": {"question_count": 4, "published_count": 4},
            "items": [
                {
                    "node_id": "point-1",
                    "chapter_id": "chapter-1",
                    "node_kind": "point",
                    "title": "氯水漂白性实验",
                    "status": "published",
                    "breadcrumb_titles": ["第13章", "氯的氧化性"],
                    "experiment_id": "exp-1",
                    "question_count": 4,
                    "published_count": 4,
                    "draft_count": 0,
                    "choice_count": 2,
                    "true_false_count": 1,
                    "fill_blank_count": 1,
                    "media_count": 1,
                    "published_media_count": 1,
                    "point_count": 1,
                }
            ],
        },
    )
    monkeypatch.setattr(
        teacher_legacy,
        "teacher_legacy_classes",
        lambda _user: {
            "classes": [
                {
                    "id": "class-1",
                    "class_name": "无机化学一班",
                    "description": "演示班",
                    "status": "active",
                    "student_count": 38,
                    "active_students": 30,
                    "completion_rate": 80,
                    "average_score": 82,
                    "missing_students": 8,
                }
            ]
        },
    )
    monkeypatch.setattr(
        teacher_legacy,
        "teacher_legacy_class_analytics",
        lambda class_id, user: {
            "class_id": class_id,
            "metrics": {"class_size": 38, "average_score": 82},
            "experiment_groups": [{"id": "group-1", "title": "卤素实验", "experiment_count": 9}],
            "students": [
                {
                    "student_id": "2026001",
                    "student_name": "李同学",
                    "average_score": 82,
                    "evidence_count": 3,
                    "attempt_count": 2,
                    "status": "已有记录",
                }
            ],
        },
    )
    monkeypatch.setattr(
        teacher_legacy,
        "teacher_legacy_class_weak_points",
        lambda class_id, user: {
            "items": [],
            "point_items": [
                {
                    "point_node_id": "point-1",
                    "point_key": "point-1",
                    "point_title": "氯水漂白性实验",
                    "experiment_id": "exp-1",
                    "experiment_title": "氯水漂白性实验",
                    "attempt_count": 10,
                    "incorrect_count": 6,
                    "incorrect_rate": 60,
                    "representative_questions": [{"question_id": "q1", "stem": "如何判断氧化性？"}],
                }
            ],
            "total": 0,
            "point_total": 1,
        },
    )
    monkeypatch.setattr(
        teacher_legacy,
        "teacher_legacy_evaluation_system",
        lambda: {
            "evaluated_objects": ["实验点位掌握度"],
            "evidence_sources": ["实验视频学习记录"],
            "update_mechanism": "测评结果更新掌握度。",
            "score_bands": [{"label": "达标", "min_score": 70, "max_score": 100, "description": "主要知识点已掌握。"}],
            "outputs": ["学生学习报告"],
        },
    )

    app.dependency_overrides[get_current_user] = _teacher_user
    try:
        with TestClient(app) as client:
            payloads: list[dict[str, Any]] = [
                client.get("/api/teacher/legacy/teacher-demo/overview").json(),
                client.get("/api/teacher/legacy/teacher-demo/video-resources").json(),
                client.get("/api/teacher/legacy/teacher-demo/question-resources").json(),
                client.get("/api/teacher/legacy/teacher-demo/classes").json(),
                client.get("/api/teacher/legacy/teacher-demo/classes/class-1/analytics").json(),
                client.get("/api/teacher/legacy/teacher-demo/classes/class-1/weak-points").json(),
                client.get("/api/teacher/legacy/teacher-demo/evaluation-system").json(),
            ]
    finally:
        app.dependency_overrides.clear()

    text = repr(payloads)
    for forbidden in ["Atom", "RAG", "Agent", "chunk", "embedding", "rerank", "Qwen", "BGE", "OpenAI", "provider", "retrieval"]:
        assert forbidden not in text
    assert payloads[1]["items"][0]["is_recommended"] is True
    assert "recommended_order" not in payloads[1]["items"][0]


def test_mainline_teacher_write_routes_remain_outside_legacy_demo_namespace() -> None:
    assert_route("/api/teacher/question-banks/workbench-sessions", "POST")
    assert_route("/api/teacher/question-banks/questions", "POST")
    assert_route("/api/teacher/classes/{class_id}/smart-assessment-strategy", "PUT")
    assert_route("/api/teacher/legacy/video-points/{node_id}/recommendation", "PUT")
