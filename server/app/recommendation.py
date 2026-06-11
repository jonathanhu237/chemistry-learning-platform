from __future__ import annotations

from typing import Any

from server.app import data_loader
from server.app.mastery import DEFAULT_STATE_PROB, mastery_score


def _kp_score(student_mastery: dict[str, Any], kp_id: str) -> float:
    state = student_mastery.get(kp_id)
    if not state:
        return mastery_score(DEFAULT_STATE_PROB)
    return float(state.get("mastery_score", mastery_score(state.get("state_prob", DEFAULT_STATE_PROB))))


def generate_recommendations(student_id: str, chapter_id: str | None = None) -> list[dict[str, Any]]:
    mastery = data_loader.load_mastery().get(student_id, {})
    points = data_loader.knowledge_points()
    if chapter_id:
        points = [point for point in points if point.get("chapter_id") == chapter_id]

    scored = sorted(((_kp_score(mastery, point["knowledge_point_id"]), point) for point in points), key=lambda item: item[0])
    weak_points = [point for score, point in scored if score < 50][:6]
    if not weak_points:
        weak_points = [point for _, point in scored[:3]]

    visible_experiments = [item for item in data_loader.experiments() if item.get("student_visible")]
    cards = {card["experiment_id"]: card for card in data_loader.learning_cards()}
    recommendations: list[dict[str, Any]] = []

    for point in weak_points:
        kp_id = point["knowledge_point_id"]
        related_experiments = [
            experiment
            for experiment in visible_experiments
            if experiment.get("chapter_id") == point.get("chapter_id")
            and kp_id in (experiment.get("related_knowledge_point_ids") or [])
        ][:2]

        recommendations.append(
            {
                "type": "knowledge_point",
                "id": kp_id,
                "title": point["content"],
                "chapter_id": point["chapter_id"],
                "reason": "课前测试中该知识点答错" if mastery else "该知识点建议先完成基础学习",
                "mastery_score": _kp_score(mastery, kp_id),
            }
        )

        for experiment in related_experiments:
            recommendations.append(
                {
                    "type": "experiment",
                    "id": experiment["id"],
                    "title": experiment["normalized_name"],
                    "chapter_id": experiment["chapter_id"],
                    "reason": "该知识点关联实验可帮助理解现象",
                    "quality_score": experiment["quality_score"],
                }
            )
            if experiment["id"] in cards:
                recommendations.append(
                    {
                        "type": "learning_card",
                        "id": cards[experiment["id"]]["id"],
                        "experiment_id": experiment["id"],
                        "title": cards[experiment["id"]]["title"],
                        "chapter_id": experiment["chapter_id"],
                        "reason": "当前没有实验视频，建议先阅读图文学习卡片",
                    }
                )

    if chapter_id:
        chapter_questions = [question for question in data_loader.questions() if question.get("chapter_id") == chapter_id]
        if len(chapter_questions) < 8:
            recommendations.append(
                {
                    "type": "review",
                    "id": f"{chapter_id}_knowledge_review",
                    "chapter_id": chapter_id,
                    "title": "复习本章核心知识点",
                    "reason": "该章节题量较少，优先复习知识点而不是强行测试",
                }
            )
        else:
            recommendations.append(
                {
                    "type": "posttest",
                    "id": f"{chapter_id}_posttest",
                    "chapter_id": chapter_id,
                    "title": "完成课后测试",
                    "reason": "该章节尚未完成课后测试",
                }
            )

    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for item in recommendations:
        key = (item["type"], item["id"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:12]
