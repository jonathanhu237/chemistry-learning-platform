from __future__ import annotations

from typing import Any

from server.app import data_loader
from server.app.recommendation import generate_recommendations
from server.app.repositories import RepositoryProvider, get_repositories


def build_report(student_id: str, repositories: RepositoryProvider | None = None) -> dict[str, Any]:
    repositories = repositories or get_repositories()
    events = [event for event in repositories.learning.load_events() if event.get("student_id") == student_id]
    mastery = repositories.learning.load_mastery().get(student_id, {})
    kp_lookup = data_loader.by_id(repositories.content.knowledge_points(), "knowledge_point_id")

    learned_chapters = sorted({event.get("chapter_id") for event in events if event.get("chapter_id")})
    learned_experiments = sorted({event.get("experiment_id") for event in events if event.get("experiment_id")})
    learned_kps = sorted({event.get("knowledge_point_id") for event in events if event.get("knowledge_point_id")})
    tests = [event for event in events if event.get("event_type") == "test_submit"]
    ai_count = sum(1 for event in events if event.get("event_type") in {"ask_ai", "ask_agent"})

    mastery_changes = []
    for kp_id, state in mastery.items():
        point = kp_lookup.get(kp_id, {})
        mastery_changes.append(
            {
                "knowledge_point_id": kp_id,
                "title": point.get("content", kp_id),
                "chapter_id": point.get("chapter_id"),
                "mastery_score": state.get("mastery_score"),
                "history": state.get("history", [])[-8:],
            }
        )
    mastery_changes.sort(key=lambda item: item.get("mastery_score") or 0)
    low_points = [item for item in mastery_changes if (item.get("mastery_score") or 0) < 50][:8]

    return {
        "student_id": student_id,
        "student_name": next((item.get("student_name") or item.get("display_name") for item in repositories.learning.load_students() if item.get("student_id") == student_id or item.get("id") == student_id), ""),
        "learned_chapters": learned_chapters,
        "learned_knowledge_points": learned_kps,
        "learned_experiments": learned_experiments,
        "test_records": [
            {
                "chapter_id": event.get("chapter_id"),
                "test_type": event.get("metadata", {}).get("test_type"),
                "score": event.get("metadata", {}).get("score"),
                "correct_count": event.get("metadata", {}).get("correct_count"),
                "total_count": event.get("metadata", {}).get("total_count"),
                "created_at": event.get("created_at"),
            }
            for event in tests
        ],
        "ai_question_count": ai_count,
        "mastery_changes": mastery_changes[:20],
        "low_mastery_knowledge_points": low_points,
        "next_recommendations": generate_recommendations(student_id, learned_chapters[-1] if learned_chapters else None),
        "summary": {
            "learned_chapter_count": len(learned_chapters),
            "learned_experiment_count": len(learned_experiments),
            "test_count": len(tests),
            "ai_question_count": ai_count,
        },
    }
