from __future__ import annotations

from server.app.domains.questions.duplicate_risk import (
    DUPLICATE_RISK_KEY,
    apply_duplicate_risk_metadata,
    build_duplicate_risk,
    duplicate_point_node_ids,
    _embedding_client,
)
from server.app.infrastructure.settings import Settings


def _payload(*, stem: str, answer: str = "Br2", point_node_id: str = "cat-md-ch13-point-1") -> dict:
    return {
        "question_type": "single_choice",
        "stem": stem,
        "options": [
            {"label": "A", "text": "Br2"},
            {"label": "B", "text": "Cl2"},
            {"label": "C", "text": "I2"},
        ],
        "answer": {"value": answer},
        "explanation": "氯气氧化溴离子，生成溴单质。",
        "source_placement_node_ids": [point_node_id],
        "metadata": {"source_placement_node_ids": [point_node_id]},
    }


def test_duplicate_risk_marks_same_point_similar_question_as_non_blocking() -> None:
    payload = _payload(stem="Cl2 与 KBr 溶液反应后主要生成什么？")
    comparison = [
        {
            "kind": "published",
            "owner_kind": "question",
            "owner_id": "11111111-1111-1111-1111-111111111111",
            "payload": _payload(stem="Cl2 与 KBr 溶液反应后主要生成什么？"),
        }
    ]

    risk = build_duplicate_risk(payload, comparison_rows=comparison)

    assert risk["has_risk"] is True
    assert risk["blocking"] is False
    assert risk["matches"][0]["owner_kind"] == "question"
    assert risk["matches"][0]["reason"] == "题干高度一致"


def test_duplicate_risk_metadata_is_teacher_visible_and_preserves_payload() -> None:
    payload = _payload(stem="Cl2 与 KBr 溶液反应后主要生成什么？")
    risk = build_duplicate_risk(
        payload,
        comparison_rows=[
            {
                "kind": "draft",
                "owner_kind": "draft",
                "owner_id": "22222222-2222-2222-2222-222222222222",
                "payload": _payload(stem="Cl2 与 KBr 溶液反应后主要生成什么？"),
            }
        ],
    )

    updated = apply_duplicate_risk_metadata({**payload, "status": "draft"}, risk)

    assert updated["status"] == "draft"
    assert updated["metadata"][DUPLICATE_RISK_KEY]["has_risk"] is True
    assert updated["metadata"][DUPLICATE_RISK_KEY]["blocking"] is False
    assert updated["metadata"][DUPLICATE_RISK_KEY]["matches"][0]["owner_kind"] == "draft"


def test_duplicate_risk_ignores_unrelated_text_when_no_similarity() -> None:
    risk = build_duplicate_risk(
        _payload(stem="Cl2 与 KBr 溶液反应后主要生成什么？"),
        comparison_rows=[
            {
                "kind": "published",
                "owner_kind": "question",
                "owner_id": "33333333-3333-3333-3333-333333333333",
                "payload": _payload(stem="pH 试纸遇酸性溶液会出现什么颜色变化？", answer="红色"),
            }
        ],
    )

    assert risk["has_risk"] is False
    assert risk["matches"] == []


def test_duplicate_point_node_ids_prefers_payload_and_metadata_sources() -> None:
    payload = {
        "source_placement_node_ids": ["point-a"],
        "metadata": {
            "source_placement_node_ids": ["point-b", "point-a"],
            "source_audit": {"target_point_node_ids": ["point-c"]},
            "evidence_lineage": {"target_point_node_ids": ["point-d"]},
        },
    }

    assert duplicate_point_node_ids(payload) == ["point-a", "point-b", "point-c", "point-d"]


def test_embedding_client_uses_backend_textbook_rag_configuration(monkeypatch) -> None:
    monkeypatch.setattr(
        "server.app.domains.questions.duplicate_risk.effective_textbook_rag_settings",
        lambda: {
            "embedding": {
                "base_url": "https://dashscope.example.test/compatible-mode/v1",
                "api_key": "configured-key",
                "model": "qwen3-embedding",
            },
            "embedding_dimension": 1024,
            "timeout_seconds": 3.5,
        },
    )

    client = _embedding_client(Settings())

    assert client is not None
    assert client.base_url == "https://dashscope.example.test/compatible-mode/v1"
    assert client.api_key == "configured-key"
    assert client.model == "qwen3-embedding"
    assert client.dimensions == 1024
    assert client.timeout_seconds == 3.5
