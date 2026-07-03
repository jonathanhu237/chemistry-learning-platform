from __future__ import annotations

import asyncio
import inspect
from contextlib import contextmanager
from datetime import datetime, timezone

from server.app.domains.student_legacy import reports as legacy_reports
from server.app.domains.student_legacy.reports import (
    _legacy_detail_from_session_row,
    _legacy_summary_from_session_row,
    legacy_assessment_report_detail_from_report,
)
from server.app.domains.student_legacy import video_points
from server.app.domains.student_legacy.video_points import legacy_student_video_points
from server.app.student_assessment_report_schemas import AssessmentReportGeneratedText, StudentAssessmentReport
from server.tests.route_helpers import assert_route


def _rows() -> list[dict[str, object]]:
    return [
        {
            "node_id": "point-recommended-no-video",
            "chapter_id": "chapter-halogen",
            "chapter_title": "Chapter 13",
            "node_title": "Recommended point without video",
            "summary": "Recommended but no playable media.",
            "point_title": "Recommended point without video",
            "principle_equation": "",
            "principle_text": "",
            "phenomenon_explanation": "",
            "safety_note": "",
            "catalog_path": ["Chapter 13", "No video"],
            "media_count": 0,
            "thumbnail_path": None,
            "is_recommended": True,
            "recommended_order": 0,
        },
        {
            "node_id": "point-recommended-video",
            "chapter_id": "chapter-halogen",
            "chapter_title": "Chapter 13",
            "node_title": "Recommended point with video",
            "summary": "Recommended and playable.",
            "point_title": "Recommended point with video",
            "principle_equation": "",
            "principle_text": "",
            "phenomenon_explanation": "",
            "safety_note": "",
            "catalog_path": ["Chapter 13", "With video"],
            "media_count": 2,
            "preview_media_id": "media-2",
            "thumbnail_media_id": "media-2",
            "is_recommended": True,
            "recommended_order": 0,
        },
        {
            "node_id": "point-1",
            "chapter_id": "chapter-halogen",
            "chapter_title": "第13章 卤族元素",
            "node_title": "氯水漂白性实验",
            "summary": "观察氯水漂白现象。",
            "point_title": "氯水漂白性实验",
            "principle_equation": "Cl2 + H2O -> HCl + HClO",
            "principle_text": "",
            "phenomenon_explanation": "试纸逐渐褪色。",
            "safety_note": "注意通风。",
            "catalog_path": ["第13章 卤族元素", "氯的氧化性", "氯水漂白性实验"],
            "media_count": 1,
            "preview_media_id": "media-1",
            "thumbnail_media_id": "media-1",
        },
        {
            "node_id": "point-no-video",
            "chapter_id": "chapter-halogen",
            "chapter_title": "第13章 卤族元素",
            "node_title": "KI水溶液中碘离子检验",
            "summary": "观察KI与氯水反应后的颜色变化。",
            "point_title": "KI水溶液中碘离子检验",
            "principle_equation": "Cl2 + 2I- -> 2Cl- + I2",
            "principle_text": "",
            "phenomenon_explanation": "加入淀粉后出现蓝色。",
            "safety_note": "",
            "catalog_path": ["第13章 卤族元素", "卤素离子的还原性", "KI水溶液中碘离子检验"],
            "media_count": 0,
            "thumbnail_path": None,
        },
    ]


@contextmanager
def _fake_db_session():
    yield object()


def test_student_legacy_video_points_route_is_registered() -> None:
    assert_route("/api/student/legacy/video-points", "GET")
    assert_route("/api/student/legacy/reports", "GET")
    assert_route("/api/student/legacy/reports/{report_id}", "GET")
    assert_route("/api/student/legacy/smart-assessment/submit", "POST")
    assert_route("/api/teacher/legacy/video-points", "GET")
    assert_route("/api/teacher/legacy/video-points/{node_id}/recommendation", "PUT")


def test_legacy_video_point_query_uses_point_content_primary_key() -> None:
    source = inspect.getsource(video_points._legacy_video_point_rows)

    assert "pc.id" not in source
    assert "pc.node_id" in source


def test_legacy_video_point_query_does_not_count_placeholder_videos() -> None:
    source = inspect.getsource(video_points._legacy_video_point_rows)

    assert "placeholder_video" in source
    assert "no-video-placeholder.mp4" in source


def test_legacy_video_points_include_no_video_points_and_filter_query(monkeypatch) -> None:
    monkeypatch.setattr(video_points, "db_session", _fake_db_session)
    monkeypatch.setattr(video_points, "_ensure_recommendation_table", lambda _session: None)
    monkeypatch.setattr(video_points, "_legacy_video_point_rows", lambda _session: _rows())

    all_points = legacy_student_video_points(query="", limit=10)

    assert all_points.total == 4
    assert [item.node_id for item in all_points.items] == [
        "point-recommended-video",
        "point-1",
        "point-recommended-no-video",
        "point-no-video",
    ]
    assert all_points.items[0].published_media_count == 2
    assert all_points.items[0].preview_stream_path == "/api/student/media/assets/media-2/stream"
    assert all_points.items[0].thumbnail_path == "/api/student/media/assets/media-2/thumbnail"
    assert all_points.items[0].is_recommended is True
    assert all_points.items[2].published_media_count == 0
    assert all_points.items[2].is_recommended is True

    filtered = legacy_student_video_points(query="KI 蓝色", limit=10)

    assert filtered.total == 1
    assert filtered.items[0].node_id == "point-no-video"
    assert filtered.items[0].thumbnail_path is None


def _assessment_report(payload: dict[str, object]) -> StudentAssessmentReport:
    return StudentAssessmentReport(
        id="report-1",
        student_id="2026001",
        class_id="class-1",
        report_type="smart",
        source_session_id="session-1",
        title="智能测评报告",
        score=60,
        correct_count=3,
        total_count=5,
        correct_rate=0.6,
        wrong_count=len(payload.get("wrong_answers", [])) if isinstance(payload.get("wrong_answers"), list) else 0,
        completed_at=datetime(2026, 6, 26, 10, 0, tzinfo=timezone.utc),
        summary=AssessmentReportGeneratedText(
            text="本次测评显示你需要复盘卤素氧化性判断。",
            source="fallback",
            mode="legacy_local_summary",
            generated_at=datetime(2026, 6, 26, 10, 0, 1, tzinfo=timezone.utc),
        ),
        mistake_explanation=AssessmentReportGeneratedText(text="", source="fallback", mode="legacy_local_explanation"),
        prompt_snapshot={"source": "legacy_local"},
        payload=payload,
    )


def test_legacy_report_detail_uses_stored_question_explanations() -> None:
    detail = legacy_assessment_report_detail_from_report(
        _assessment_report(
            {
                "experiments": [{"title": "氯水漂白性实验"}],
                "next_recommendation": "先复盘错题解析，再回看相关实验视频。",
                "wrong_answers": [
                    {
                        "question_id": "q1",
                        "stem": "新制氯水具有氧化性。",
                        "experiment_title": "氯水漂白性实验",
                        "question_type": "true_false",
                        "submitted_answer": False,
                        "correct_answer": True,
                        "explanation": "新制氯水中含有氯气和次氯酸，能体现氧化性。",
                    }
                ],
            }
        )
    )

    assert detail.ai_summary.text == "本次测评显示你需要复盘卤素氧化性判断。"
    assert detail.covered_experiments == ["氯水漂白性实验"]
    assert detail.wrong_questions[0].submitted_answer == "错误"
    assert detail.wrong_questions[0].correct_answer == "正确"
    assert detail.wrong_questions[0].explanation_source == "stored"
    assert "次氯酸" in detail.wrong_questions[0].explanation
    assert "TKE" not in detail.model_dump_json()
    assert "mastery_score" not in detail.model_dump_json()


def test_legacy_report_detail_exposes_ai_mistake_explanation_without_internal_mode() -> None:
    report = _assessment_report(
        {
            "wrong_answers": [
                {
                    "question_id": "q-ai",
                    "stem": "新制氯水具有氧化性。",
                    "experiment_title": "氯水漂白性实验",
                    "submitted_answer": False,
                    "correct_answer": True,
                }
            ]
        }
    )
    report.mistake_explanation = AssessmentReportGeneratedText(
        text="AI解析：本题要把氯水中的氯气、次氯酸与氧化性现象对应起来。",
        source="ai",
        mode="openai_agents_sdk",
        generated_at=datetime(2026, 6, 26, 10, 0, 2, tzinfo=timezone.utc),
    )

    detail = legacy_assessment_report_detail_from_report(report)

    assert detail.mistake_explanation is not None
    assert detail.mistake_explanation.source == "ai"
    assert detail.mistake_explanation.mode == "ai_generated"
    assert "次氯酸" in detail.mistake_explanation.text
    assert "openai" not in detail.model_dump_json().lower()
    assert "agent" not in detail.model_dump_json().lower()


def test_legacy_report_detail_does_not_hydrate_on_read(monkeypatch) -> None:
    payload = {
        "session_id": "session-1",
        "assessment_mode": "smart",
        "strategy": {"enabled": True},
        "composition": {},
        "experiments": [],
        "correct_count": 0,
        "total_count": 1,
        "score": 0,
        "correct_rate": 0,
        "wrong_answers": [
            {
                "question_id": "q-hydrate",
                "stem": "新制氯水具有氧化性。",
                "experiment_title": "氯水漂白性实验",
                "submitted_answer": False,
                "correct_answer": True,
            }
        ],
        "next_recommendation": "复盘错题。",
    }
    fallback_report = _assessment_report(payload)

    monkeypatch.setattr(legacy_reports, "get_student_assessment_report", lambda _report_id, _user: fallback_report)

    async def fake_create(payload_arg, _user, *, session_id=None):
        raise AssertionError("legacy report detail must not generate AI content while reading")

    monkeypatch.setattr(legacy_reports, "_create_report_from_smart_payload", fake_create)

    detail = asyncio.run(legacy_reports.legacy_assessment_report_detail("report-1", object()))

    assert detail.ai_summary.source == "fallback"
    assert detail.mistake_explanation is not None
    assert detail.mistake_explanation.source == "fallback"
    assert "本次错题可按以下思路复盘" in detail.mistake_explanation.text


def test_legacy_report_detail_reuses_report_by_source_session(monkeypatch) -> None:
    payload = {
        "session_id": "session-1",
        "assessment_mode": "smart",
        "experiments": [{"title": "氯水漂白性实验"}],
        "correct_count": 4,
        "total_count": 5,
        "score": 80,
        "correct_rate": 0.8,
        "wrong_answers": [],
    }
    stored_report = _assessment_report(payload)
    stored_report.id = "report-from-session"
    stored_report.source_session_id = "session-1"
    stored_report.summary = AssessmentReportGeneratedText(text="AI学情总结。", source="ai", mode="openai_chat_fallback")

    def raise_not_found(_report_id, _user):
        raise legacy_reports.DomainHTTPException(
            status_code=legacy_reports.domain_status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    monkeypatch.setattr(legacy_reports, "get_student_assessment_report", raise_not_found)
    monkeypatch.setattr(legacy_reports, "_legacy_current_report_by_source_session", lambda _report_id, _user: stored_report)
    monkeypatch.setattr(
        legacy_reports,
        "_legacy_completed_session_row",
        lambda _report_id, _user: (_ for _ in ()).throw(AssertionError("session fallback should not be reached")),
    )

    detail = asyncio.run(legacy_reports.legacy_assessment_report_detail("session-1", object()))

    assert detail.id == "report-from-session"
    assert detail.source_session_id == "session-1"
    assert detail.ai_summary.source == "ai"
    assert detail.ai_summary.mode == "ai_generated"


def test_legacy_report_detail_falls_back_when_question_explanation_is_missing() -> None:
    detail = legacy_assessment_report_detail_from_report(
        _assessment_report(
            {
                "wrong_answers": [
                    {
                        "question_id": "q2",
                        "stem": "氯水中起漂白作用的主要物质是____。",
                        "experiment_title": "氯水漂白性实验",
                        "question_type": "fill_blank",
                        "submitted_answer": "Cl2",
                        "correct_answer": "HClO",
                    }
                ]
            }
        )
    )

    assert detail.wrong_questions[0].explanation_source == "fallback"
    assert "你的作答为Cl2" in detail.wrong_questions[0].explanation
    assert "参考答案为HClO" in detail.wrong_questions[0].explanation


def test_legacy_report_detail_sanitizes_current_report_implementation_terms() -> None:
    report = _assessment_report(
        {
            "next_recommendation": "TKE shows the Agent should retrieve chunks.",
            "wrong_answers": [
                {
                    "question_id": "q3",
                    "stem": "溴水能氧化碘离子。",
                    "experiment_title": "卤素置换实验",
                    "submitted_answer": "错误",
                    "correct_answer": "正确",
                    "explanation": "Agent/RAG retrieved this answer from embeddings.",
                }
            ],
        }
    )
    report.summary.text = "TKE mastery_score is low."

    detail = legacy_assessment_report_detail_from_report(report)
    dumped = detail.model_dump_json()

    assert "TKE" not in dumped
    assert "Agent" not in dumped
    assert "RAG" not in dumped
    assert "mastery_score" not in dumped
    assert detail.ai_summary.source == "fallback"
    assert detail.wrong_questions[0].explanation_source == "fallback"


def test_legacy_report_can_be_shaped_from_completed_smart_session_report() -> None:
    row = {
        "id": "2f2e03a0-2f67-4f5e-95d0-5c1ff2d4aa41",
        "assessment_mode": "smart",
        "score": 40,
        "correct_count": 4,
        "total_count": 10,
        "completed_at": datetime(2026, 6, 26, 12, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 26, 12, 1, tzinfo=timezone.utc),
        "report": {
            "session_id": "2f2e03a0-2f67-4f5e-95d0-5c1ff2d4aa41",
            "assessment_mode": "smart",
            "score": 40,
            "correct_count": 4,
            "total_count": 10,
            "correct_rate": 0.4,
            "experiments": [{"title": "氯水漂白性实验"}],
            "wrong_answers": [
                {
                    "question_id": "q-session",
                    "stem": "氯水中起漂白作用的主要物质是____。",
                    "experiment_title": "氯水漂白性实验",
                    "submitted_answer": "Cl2",
                    "correct_answer": "HClO",
                    "explanation": "次氯酸具有漂白性。",
                }
            ],
            "next_recommendation": "先复盘错题解析，再回看相关视频。",
        },
    }

    summary = _legacy_summary_from_session_row(row)
    detail = _legacy_detail_from_session_row(row)

    assert summary.id == "2f2e03a0-2f67-4f5e-95d0-5c1ff2d4aa41"
    assert summary.source_session_id == summary.id
    assert summary.wrong_count == 1
    assert detail.wrong_questions[0].explanation == "次氯酸具有漂白性。"
    assert detail.ai_summary.text
