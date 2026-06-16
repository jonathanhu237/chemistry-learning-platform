from __future__ import annotations

import json

import server.app.experiment_admin as experiment_admin_module
from scripts.point_aware_question_bank import prepare_import_rows
from server.app.experiment_admin import (
    PointAwareSuggestionRequest,
    _local_point_aware_suggestions,
    _record_workbench_generation_failure,
    _validate_question_payload,
    _workbench_candidate_validation_errors,
    _workbench_context,
    _question_snapshot,
    _with_point_aware_metadata,
)
from server.app.services.student_experiment_service import _attempt_diagnostic_metadata


def test_prepare_import_rows_preserves_point_metadata(tmp_path):
    inventory_path = tmp_path / "inventory.json"
    artifact_path = tmp_path / "bank.json"
    inventory_path.write_text(
        json.dumps(
            {
                "experiments": [
                    {
                        "experiment_id": "EXP_TEST",
                        "code": "T-1",
                        "title": "测试实验",
                        "chapter_bindings": [{"chapter_id": "CH13"}],
                        "video_points": [
                            {
                                "point_key": "point-1",
                                "point_title": "观察颜色变化",
                                "source": "formal_experiment.video_candidates",
                            }
                        ],
                        "canonical_chunk_ids": ["chunk-1"],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    artifact_path.write_text(
        json.dumps(
            {
                "metadata": {"artifact_type": "point_aware_question_bank", "version": "test-v1"},
                "experiments": [
                    {
                        "experiment_id": "EXP_TEST",
                        "experiment_code": "T-1",
                        "experiment_title": "测试实验",
                        "video_points": [{"point_key": "point-1", "point_title": "观察颜色变化"}],
                        "questions": [
                            {
                                "question_id": "Q1",
                                "question_type": "single_choice",
                                "stem": "下列哪一项符合观察点位？",
                                "options": [
                                    {"label": "A", "text": "观察颜色变化"},
                                    {"label": "B", "text": "记录仪器编号"},
                                ],
                                "answer": {"value": "A"},
                                "explanation": "该点位要求观察颜色变化。",
                                "difficulty": "basic",
                                "review_decision": "keep",
                                "quality_flags": ["reviewed"],
                                "primary_point_keys": ["point-1"],
                                "coverage_tags": ["phenomenon_observation"],
                                "option_links": [
                                    {"label": "A", "point_key": "point-1", "role": "correct_evidence"},
                                    {"label": "B", "point_key": None, "role": "unrelated_distractor"},
                                ],
                                "source_audit": {
                                    "canonical_chunk_ids": ["chunk-1"],
                                    "supporting_theory_chunk_ids": [],
                                    "evidence_sufficient": True,
                                    "reviewer_note": "人工审查通过。",
                                },
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    rows, validation_report, prepare_report = prepare_import_rows(artifact_path, inventory_path)

    assert validation_report["valid"] is True
    assert prepare_report["prepared_question_count"] == 1
    assert rows[0]["metadata"]["primary_point_keys"] == ["point-1"]
    assert rows[0]["metadata"]["primary_points"] == [{"point_key": "point-1", "point_title": "观察颜色变化"}]
    assert rows[0]["related_chapter_ids"] == ["CH13"]
    assert rows[0]["source_chunk_ids"] == ["chunk-1"]


def test_attempt_diagnostic_metadata_captures_selected_option_link():
    question = {
        "question_type": "single_choice",
        "metadata": {
            "point_aware_question_bank": True,
            "primary_point_keys": ["point-1"],
            "primary_points": [{"point_key": "point-1", "point_title": "观察颜色变化"}],
            "coverage_tags": ["phenomenon_observation"],
            "option_links": [
                {"label": "A", "point_key": "point-1", "role": "correct_evidence"},
                {"label": "B", "point_key": None, "role": "unrelated_distractor"},
            ],
        },
    }

    metadata = _attempt_diagnostic_metadata(question, "B", False)

    assert metadata["point_aware_question_bank"] is True
    assert metadata["primary_point_keys"] == ["point-1"]
    assert metadata["selected_option_label"] == "B"
    assert metadata["diagnostic_role"] == "unrelated_distractor"


def test_validate_question_payload_preserves_point_metadata():
    normalized, errors = _validate_question_payload(
        {
            "question_type": "single_choice",
            "stem": "Which option is supported?",
            "options": [{"label": "A", "text": "Supported"}, {"label": "B", "text": "Unsupported"}],
            "answer": {"value": "A"},
            "metadata": {
                "point_aware_question_bank": True,
                "primary_point_keys": ["point-1"],
                "option_links": [{"label": "A", "role": "correct_evidence", "point_key": "point-1"}],
            },
        }
    )

    assert errors == []
    assert normalized is not None
    assert normalized["metadata"]["point_aware_question_bank"] is True
    assert normalized["metadata"]["primary_point_keys"] == ["point-1"]
    assert normalized["metadata"]["option_links"][0]["role"] == "correct_evidence"


def test_local_point_aware_repair_suggestion_keeps_lineage_and_metadata():
    request = PointAwareSuggestionRequest(
        intent="repair_question",
        experiment_id="EXP_TEST",
        prompt="Repair this question",
        question_id="00000000-0000-0000-0000-000000000001",
        question_types=["single_choice"],
        count=1,
    )
    experiment = {"id": "EXP_TEST", "code": "T-1", "title": "Test experiment"}
    point = {"point_key": "point-1", "point_title": "Observe color change"}
    target_question = {
        "id": request.question_id,
        "question_type": "single_choice",
        "stem": "Original stem",
        "options": [{"label": "A", "text": "Correct"}, {"label": "B", "text": "Wrong"}],
        "answer": {"value": "A"},
        "explanation": "Original explanation",
        "related_chapter_ids": ["CH13"],
        "metadata": {
            "point_aware_question_bank": True,
            "primary_point_keys": ["point-1"],
            "primary_points": [point],
            "option_links": [{"label": "A", "role": "correct_evidence", "point_key": "point-1"}],
            "source_audit": {
                "canonical_chunk_ids": ["chunk-1"],
                "supporting_theory_chunk_ids": [],
                "evidence_sufficient": True,
            },
        },
    }

    rows = _local_point_aware_suggestions(
        request=request,
        experiment=experiment,
        point=point,
        target_question=target_question,
    )
    payload = _with_point_aware_metadata(
        row=rows[0],
        request=request,
        experiment=experiment,
        point=point,
        source_refs=[],
        target_question=target_question,
        index=0,
    )
    normalized, errors = _validate_question_payload(payload)

    assert errors == []
    assert normalized is not None
    metadata = normalized["metadata"]
    assert metadata["suggestion_intent"] == "repair_question"
    assert metadata["primary_point_keys"] == ["point-1"]
    assert metadata["review_lineage"]["original_question_id"] == request.question_id
    assert metadata["source_audit"]["canonical_chunk_ids"] == ["chunk-1"]


def test_workbench_context_keeps_original_question_snapshot():
    experiment = {"id": "EXP_TEST", "code": "T-1", "title": "Test experiment", "summary": "Summary"}
    point = {"point_key": "point-1", "point_title": "Observe color change"}
    question = {
        "id": "00000000-0000-0000-0000-000000000001",
        "experiment_id": "EXP_TEST",
        "question_type": "single_choice",
        "stem": "Original stem",
        "options": [{"label": "A", "text": "Correct"}],
        "answer": {"value": "A"},
        "explanation": "Original explanation",
        "metadata": {
            "primary_point_keys": ["point-1"],
            "option_links": [{"label": "A", "role": "correct_evidence", "point_key": "point-1"}],
        },
    }

    context = _workbench_context(
        mode="repair",
        experiment=experiment,
        point=point,
        target_question=question,
        source_refs=[{"chunk_id": "chunk-1"}],
        coverage={"question_count": 3},
    )

    assert context["mode"] == "repair"
    assert context["selected_point"] == point
    assert context["original_question"]["stem"] == "Original stem"
    assert context["original_question"]["metadata"]["option_links"][0]["role"] == "correct_evidence"
    assert context["coverage"]["question_count"] == 3


def test_question_snapshot_is_limited_to_teacher_repair_context_fields():
    question = {
        "id": "00000000-0000-0000-0000-000000000001",
        "stem": "Original stem",
        "answer": {"value": "A"},
        "metadata": {"primary_point_keys": ["point-1"]},
        "created_by": "private-user-id",
    }

    snapshot = _question_snapshot(question)

    assert snapshot["stem"] == "Original stem"
    assert snapshot["metadata"]["primary_point_keys"] == ["point-1"]
    assert "created_by" not in snapshot


def test_workbench_candidate_validation_requires_lineage_and_publish_metadata():
    payload = {
        "question_type": "single_choice",
        "stem": "Candidate stem",
        "options": [{"label": "A", "text": "Correct"}, {"label": "B", "text": "Wrong"}],
        "answer": {"value": "A"},
        "metadata": {
            "primary_point_keys": ["point-1"],
            "source_audit": {"canonical_chunk_ids": ["chunk-1"], "evidence_sufficient": True},
            "option_links": [{"label": "A", "role": "correct_evidence", "point_key": "point-1"}],
            "review_lineage": {
                "workbench_session_id": "session-1",
                "workbench_turn_id": "turn-1",
            },
        },
    }

    assert _workbench_candidate_validation_errors(payload, session_id="session-1", turn_id="turn-1") == []

    missing_lineage = {**payload, "metadata": {**payload["metadata"], "review_lineage": {}}}

    assert "workbench lineage is required" in _workbench_candidate_validation_errors(
        missing_lineage,
        session_id="session-1",
        turn_id="turn-1",
    )


def test_workbench_generation_failure_preserves_prompt_turn(monkeypatch):
    inserted_turns: list[dict[str, object]] = []

    def fake_insert_workbench_turn(session, **kwargs):
        inserted_turns.append(kwargs)
        return {"id": "assistant-turn-1", **kwargs}

    class FakeSession:
        def __init__(self):
            self.statements: list[tuple[str, dict[str, object]]] = []

        def execute(self, statement, params):
            self.statements.append((str(statement), params))

    monkeypatch.setattr(experiment_admin_module, "_insert_workbench_turn", fake_insert_workbench_turn)
    session = FakeSession()

    assistant_turn = _record_workbench_generation_failure(
        session,
        session_id="session-1",
        user_turn={"id": "user-turn-1", "content": "请把这个题修清楚"},
        exc=TimeoutError("provider timed out"),
    )

    assert assistant_turn["role"] == "assistant"
    assert inserted_turns[0]["error_state"] == {"message": "provider timed out", "type": "TimeoutError"}
    assert inserted_turns[0]["metadata"] == {"user_turn_id": "user-turn-1"}
    assert inserted_turns[0]["content"].startswith("AI 建议生成失败")
    assert session.statements[0][1] == {"id": "session-1"}
