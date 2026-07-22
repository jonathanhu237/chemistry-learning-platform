from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import server.app.domains.questions.workbench as question_workbench_service
from server.app.app_runtime.main import app
from server.app.auth import AuthUser, get_current_user
from server.app.domains.questions.bank import catalog_experiment_id_for_root
from server.app.infrastructure.database import get_session_factory


@dataclass(frozen=True)
class QuestionWorkbenchGenerationE2EFixture:
    client: TestClient
    test_id: str
    user_id: str
    chapter_id: str
    root_node_id: str
    point_node_id: str
    canonical_point_id: str
    chunk_id: str
    experiment_id: str


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _test_user(user_id: str, test_id: str) -> AuthUser:
    return AuthUser(
        id=user_id,
        username=f"{test_id}-teacher",
        role="teacher",
        display_name="Question Workbench E2E Teacher",
        status="active",
        must_change_password=False,
    )


def _cleanup_question_workbench_fixture(test_id: str, *, chapter_id: str, user_id: str, root_node_id: str, doc_id: str) -> None:
    session = get_session_factory()()
    try:
        session.execute(
            text("DELETE FROM formal_experiments WHERE metadata->>'e2e_test_id' = :test_id"),
            {"test_id": test_id},
        )
        session.execute(
            text("DELETE FROM source_chunks WHERE metadata->>'e2e_test_id' = :test_id"),
            {"test_id": test_id},
        )
        session.execute(text("DELETE FROM source_documents WHERE id = :doc_id"), {"doc_id": doc_id})
        session.execute(text("DELETE FROM experiment_catalog_nodes WHERE id = :root_node_id"), {"root_node_id": root_node_id})
        session.execute(
            text("DELETE FROM experiment_catalog_points WHERE metadata->>'e2e_test_id' = :test_id"),
            {"test_id": test_id},
        )
        session.execute(text("DELETE FROM chapters WHERE id = :chapter_id"), {"chapter_id": chapter_id})
        session.execute(text("DELETE FROM app_users WHERE id = CAST(:user_id AS uuid)"), {"user_id": user_id})
        session.commit()
    finally:
        session.close()


def _insert_question_workbench_fixture(test_id: str) -> QuestionWorkbenchGenerationE2EFixture:
    session = get_session_factory()()
    user_id = str(uuid4())
    chapter_id = f"E2E_QGEN_{test_id}"
    root_node_id = f"cat-e2e-{test_id}-root"
    point_node_id = f"cat-e2e-{test_id}-point"
    canonical_point_id = f"cat-e2e-{test_id}-canonical"
    doc_id = f"DOC-E2E-{test_id}"
    chunk_id = f"chunk-e2e-{test_id}"
    experiment_id = catalog_experiment_id_for_root(root_node_id)
    metadata = {"e2e_test_id": test_id}
    try:
        session.execute(text("SELECT 1"))
        session.execute(
            text(
                """
                INSERT INTO app_users (id, username, role, display_name, password_hash, status, metadata)
                VALUES (
                  CAST(:user_id AS uuid), :username, 'teacher', 'Question Workbench E2E Teacher',
                  'test-only', 'active', CAST(:metadata AS jsonb)
                )
                """
            ),
            {"user_id": user_id, "username": f"{test_id}-teacher", "metadata": _json(metadata)},
        )
        session.execute(
            text(
                """
                INSERT INTO chapters (id, chapter_number, chapter_title, element_area)
                VALUES (:chapter_id, 99002, :chapter_title, 'E2E')
                """
            ),
            {"chapter_id": chapter_id, "chapter_title": f"E2E Question Generation {test_id}"},
        )
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_points (
                  id, title, summary, status, metadata, published_at, created_by, updated_by
                )
                VALUES (
                  :canonical_point_id, 'KBr + FeCl3', 'E2E canonical point', 'published',
                  CAST(:metadata AS jsonb), now(), CAST(:user_id AS uuid), CAST(:user_id AS uuid)
                )
                """
            ),
            {"canonical_point_id": canonical_point_id, "metadata": _json(metadata), "user_id": user_id},
        )
        for node in [
            {
                "id": root_node_id,
                "parent_id": None,
                "node_kind": "directory",
                "title": "卤素离子的还原性",
                "canonical_point_id": None,
                "display_order": 1,
            },
            {
                "id": point_node_id,
                "parent_id": root_node_id,
                "node_kind": "point",
                "title": "KBr + FeCl3",
                "canonical_point_id": canonical_point_id,
                "display_order": 1,
            },
        ]:
            session.execute(
                text(
                    """
                    INSERT INTO experiment_catalog_nodes (
                      id, chapter_id, parent_id, node_kind, title, summary, status, display_order,
                      canonical_point_id, metadata, published_at, created_by, updated_by
                    )
                    VALUES (
                      :id, :chapter_id, :parent_id, :node_kind, :title, '', 'published', :display_order,
                      :canonical_point_id, CAST(:metadata AS jsonb), now(), CAST(:user_id AS uuid), CAST(:user_id AS uuid)
                    )
                    """
                ),
                {
                    **node,
                    "chapter_id": chapter_id,
                    "metadata": _json(metadata),
                    "user_id": user_id,
                },
            )
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_content (
                  node_id, canonical_point_id, point_title, teacher_note, principle_mode, principle_text,
                  phenomenon_explanation, safety_note, content_status, published_at, created_by, updated_by, metadata
                )
                VALUES (
                  :node_id, :canonical_point_id, 'KBr + FeCl3', '', 'text',
                  'FeCl3 能氧化 I-，但不能氧化 Br-，用于比较卤素离子还原性。',
                  '加入 FeCl3 后，KI 体系出现碘的颜色，KBr 体系无明显溴生成。',
                  'FeCl3 溶液避免接触皮肤，含碘废液集中回收。',
                  'published', now(), CAST(:user_id AS uuid), CAST(:user_id AS uuid), CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "node_id": point_node_id,
                "canonical_point_id": canonical_point_id,
                "user_id": user_id,
                "metadata": _json(metadata),
            },
        )
        session.execute(
            text(
                """
                INSERT INTO source_documents (
                  id, title, file_name, path, type, document_kind, processing_status,
                  metadata, logical_textbook_key, version_number, version_label,
                  publication_status, published_at, updated_at
                )
                VALUES (
                  :doc_id, 'E2E textbook', 'E2E textbook', '/tmp/e2e-textbook.md', 'markdown',
                  'canonical_textbook', 'imported', CAST(:metadata AS jsonb),
                  :doc_id, 1, 'e2e-v1', 'published', now(), now()
                )
                """
            ),
            {"doc_id": doc_id, "metadata": _json(metadata)},
        )
        evidence_text = "#### 卤素离子的还原性 利用 KBr、KI、FeCl3 溶液反应比较 Br- 与 I- 的还原性。"
        session.execute(
            text(
                """
                INSERT INTO source_chunks (
                  id, document_id, chapter_id, page_number, section_title, chunk_index,
                  text, markdown, tags, metadata, review_required, content_status, published_at, updated_at
                )
                VALUES (
                  :chunk_id, :doc_id, :chapter_id, 139, '实验 19-1 / 卤素离子的还原性', 1,
                  :text, :markdown, ARRAY['e2e', 'textbook'], CAST(:metadata AS jsonb),
                  false, 'published', now(), now()
                )
                """
            ),
            {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "chapter_id": chapter_id,
                "text": evidence_text,
                "markdown": evidence_text,
                "metadata": _json({**metadata, "book_title": "无机化学实验（第四版）", "page_start": 139}),
            },
        )
        source_ref = {
            "chunk_id": chunk_id,
            "evidence_role": "principle",
            "section": "principle",
            "rank": 1,
            "text": evidence_text,
            "text_preview": evidence_text,
            "source_file": "无机化学实验（第四版）",
            "book_title": "无机化学实验（第四版）",
            "page_number": 139,
            "section_title": "实验 19-1 / 卤素离子的还原性",
            "source_boundary": "qwen_es_textbook_rag",
        }
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_evidence_state (
                  node_id, canonical_point_id, source_placement_node_id, evidence_status, source_mode,
                  trigger_policy, selected_chunk_ids, source_refs, diagnostics, refreshed_at,
                  last_attempted_at, content_fingerprint, config_fingerprint, updated_at
                )
                VALUES (
                  :node_id, :canonical_point_id, :source_placement_node_id, 'succeeded', 'qwen_es_textbook_rag',
                  'stale_until_manual_refresh', :selected_chunk_ids, CAST(:source_refs AS jsonb),
                  CAST(:diagnostics AS jsonb), now(), now(), :content_fingerprint, :config_fingerprint, now()
                )
                """
            ),
            {
                "node_id": point_node_id,
                "canonical_point_id": canonical_point_id,
                "source_placement_node_id": point_node_id,
                "selected_chunk_ids": [chunk_id],
                "source_refs": _json([source_ref]),
                "diagnostics": _json({"e2e_test_id": test_id, "evidence_status": "fresh"}),
                "content_fingerprint": hashlib.sha256(f"{test_id}:content".encode()).hexdigest(),
                "config_fingerprint": hashlib.sha256(f"{test_id}:config".encode()).hexdigest(),
            },
        )
        for role in ("principle", "phenomenon", "safety"):
            session.execute(
                text(
                    """
                    INSERT INTO experiment_catalog_point_evidence_bindings (
                      node_id, canonical_point_id, source_placement_node_id, chunk_id, evidence_role,
                      selection_status, freshness_status, rank, score, rerank_score,
                      source_metadata, diagnostics, content_fingerprint, config_fingerprint, updated_at
                    )
                    VALUES (
                      :node_id, :canonical_point_id, :source_placement_node_id, :chunk_id, :role,
                      'selected', 'fresh', :rank, 1.0, 0.99,
                      CAST(:source_metadata AS jsonb), CAST(:diagnostics AS jsonb),
                      :content_fingerprint, :config_fingerprint, now()
                    )
                    """
                ),
                {
                    "node_id": point_node_id,
                    "canonical_point_id": canonical_point_id,
                    "source_placement_node_id": point_node_id,
                    "chunk_id": chunk_id,
                    "role": role,
                    "rank": {"principle": 1, "phenomenon": 2, "safety": 3}[role],
                    "source_metadata": _json({**source_ref, "evidence_role": role, "section": role}),
                    "diagnostics": _json({"e2e_test_id": test_id, "section": role}),
                    "content_fingerprint": hashlib.sha256(f"{test_id}:content".encode()).hexdigest(),
                    "config_fingerprint": hashlib.sha256(f"{test_id}:config".encode()).hexdigest(),
                },
            )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        session.close()
        _cleanup_question_workbench_fixture(
            test_id,
            chapter_id=chapter_id,
            user_id=user_id,
            root_node_id=root_node_id,
            doc_id=doc_id,
        )
        pytest.skip(f"question workbench e2e requires a migrated test database: {exc.__class__.__name__}")
    finally:
        if session.is_active:
            session.close()
    return QuestionWorkbenchGenerationE2EFixture(
        client=None,  # type: ignore[arg-type]
        test_id=test_id,
        user_id=user_id,
        chapter_id=chapter_id,
        root_node_id=root_node_id,
        point_node_id=point_node_id,
        canonical_point_id=canonical_point_id,
        chunk_id=chunk_id,
        experiment_id=experiment_id,
    )


@pytest.fixture()
def question_workbench_generation_e2e(monkeypatch: pytest.MonkeyPatch) -> QuestionWorkbenchGenerationE2EFixture:
    test_id = f"qgen-{uuid4().hex[:10]}"
    fixture = _insert_question_workbench_fixture(test_id)
    app.dependency_overrides[get_current_user] = lambda: _test_user(fixture.user_id, test_id)
    monkeypatch.setattr(question_workbench_service, "ai_feature_enabled", lambda name: True)
    monkeypatch.setattr(
        question_workbench_service,
        "get_settings",
        lambda: SimpleNamespace(
            agent_llm_provider="openai",
            agent_llm_base_url="https://example.invalid/v1",
            agent_llm_model="e2e-model",
            agent_llm_api_key="configured",
        ),
    )
    monkeypatch.setattr(question_workbench_service, "effective_ai_settings", lambda settings: settings)
    monkeypatch.setattr(question_workbench_service, "effective_textbook_rag_settings", lambda: {"enabled": True})
    monkeypatch.setattr(
        question_workbench_service,
        "_textbook_rag_runtime_status",
        lambda _settings, *, rag_enabled: {
            "enabled": rag_enabled,
            "status": "healthy",
            "message": "E2E textbook RAG readiness stubbed.",
            "models": {"embedding": "e2e-embedding", "rerank": "e2e-rerank"},
            "diagnostics": {"index_exists": True},
        },
    )
    monkeypatch.setattr(question_workbench_service, "_try_openai_point_aware_suggestions", lambda **kwargs: [])
    monkeypatch.setattr(
        question_workbench_service,
        "attach_duplicate_risk_for_payload",
        lambda _session, *, payload, **_kwargs: {
            **payload,
            "metadata": {
                **(payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}),
                "duplicate_risk": {
                    "has_risk": False,
                    "level": "none",
                    "blocking": False,
                    "message": "E2E duplicate check stubbed.",
                    "matches": [],
                    "method": "stub",
                    "scope": "same_point",
                },
            },
        },
    )
    try:
        with TestClient(app) as client:
            yield QuestionWorkbenchGenerationE2EFixture(
                client=client,
                test_id=fixture.test_id,
                user_id=fixture.user_id,
                chapter_id=fixture.chapter_id,
                root_node_id=fixture.root_node_id,
                point_node_id=fixture.point_node_id,
                canonical_point_id=fixture.canonical_point_id,
                chunk_id=fixture.chunk_id,
                experiment_id=fixture.experiment_id,
            )
    finally:
        app.dependency_overrides.clear()
        _cleanup_question_workbench_fixture(
            test_id,
            chapter_id=fixture.chapter_id,
            user_id=fixture.user_id,
            root_node_id=fixture.root_node_id,
            doc_id=f"DOC-E2E-{test_id}",
        )


def test_question_workbench_generates_draft_from_prebound_catalog_evidence(
    question_workbench_generation_e2e: QuestionWorkbenchGenerationE2EFixture,
) -> None:
    fixture = question_workbench_generation_e2e
    session_response = fixture.client.post(
        "/api/admin/question-banks/workbench-sessions",
        json={
            "mode": "create",
            "experiment_id": "ignored-when-point-node-is-selected",
            "point_node_id": fixture.point_node_id,
        },
    )

    assert session_response.status_code == 200, session_response.text
    session_payload = session_response.json()
    session_id = session_payload["id"]
    assert session_payload["point_node_ids"] == [fixture.point_node_id]
    assert session_payload["context_snapshot"]["evidence_package"]["evidence_contract"] == "catalog_node_evidence"
    assert session_payload["context_snapshot"]["source_refs"][0]["chunk_id"] == fixture.chunk_id

    message_response = fixture.client.post(
        f"/api/admin/question-banks/workbench-sessions/{session_id}/messages",
        json={
            "prompt": "围绕 FeCl3 比较 Br- 与 I- 还原性出一道单选题。",
            "question_types": ["single_choice"],
            "count": 1,
            "difficulty": "basic",
        },
    )

    assert message_response.status_code == 200, message_response.text
    payload = message_response.json()
    assert len(payload["turns"]) == 2
    assert len(payload["candidates"]) == 1
    candidate = payload["candidates"][0]
    assert candidate["draft_status"] == "draft"
    assert candidate["validation_errors"] == []
    question = candidate["payload"]
    assert question["question_type"] == "single_choice"
    assert fixture.point_node_id in question["source_placement_node_ids"]
    assert fixture.canonical_point_id in question["primary_canonical_point_ids"]
    assert fixture.chunk_id in question["source_chunk_ids"]
    assert question["source_refs"][0]["chunk_id"] == fixture.chunk_id
    metadata = question["metadata"]
    assert metadata["source_audit"]["evidence_contract"] == "catalog_node_evidence"
    assert metadata["source_audit"]["evidence_sufficient"] is True
    assert metadata["evidence_lineage"]["evidence_contract"] == "catalog_node_evidence"
    assert metadata["review_lineage"]["workbench_session_id"] == session_id
    assert metadata["duplicate_risk"]["has_risk"] is False
