from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    experiment_id: str = Field(min_length=1)
    primary_point_node_ids: list[str] = Field(default_factory=list)
    primary_canonical_point_ids: list[str] = Field(default_factory=list)
    source_placement_node_ids: list[str] = Field(default_factory=list)
    question_type: str = Field(pattern="^(single_choice|true_false|fill_blank)$")
    stem: str = Field(min_length=1)
    options: list[Any] = Field(default_factory=list)
    answer: Any
    explanation: str | None = None
    difficulty: str | None = "basic"
    related_chapter_ids: list[str] = Field(default_factory=list)
    related_knowledge_point_ids: list[str] = Field(default_factory=list)
    source_chunk_ids: list[str] = Field(default_factory=list)
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="draft", pattern="^(draft|published|disabled|archived)$")
    bank_kind: str = Field(default="manual", pattern="^(default|generated|manual)$")


class QuestionUpdateRequest(BaseModel):
    primary_point_node_ids: list[str] | None = None
    primary_canonical_point_ids: list[str] | None = None
    source_placement_node_ids: list[str] | None = None
    stem: str | None = Field(default=None, min_length=1)
    options: list[Any] | None = None
    answer: Any | None = None
    explanation: str | None = None
    difficulty: str | None = None
    related_chapter_ids: list[str] | None = None
    related_knowledge_point_ids: list[str] | None = None
    source_chunk_ids: list[str] | None = None
    source_refs: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None
    status: str | None = Field(default=None, pattern="^(draft|published|disabled|archived)$")


class GenerationRequest(BaseModel):
    experiment_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1, max_length=2000)
    question_types: list[str] = Field(default_factory=lambda: ["single_choice", "true_false", "fill_blank"])
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str | None = "basic"
    chapter_ids: list[str] = Field(default_factory=list)
    knowledge_point_ids: list[str] = Field(default_factory=list)
    target_point_node_ids: list[str] = Field(default_factory=list)


class QuestionBankAssistantRequest(BaseModel):
    intent: str = Field(default="add_questions", pattern="^(add_questions|repair_question|coverage_check|disable_question)$")
    prompt: str = Field(min_length=1, max_length=2000)
    chapter_id: str | None = None
    experiment_id: str | None = None
    question_id: str | None = None
    question_types: list[str] = Field(default_factory=lambda: ["single_choice", "true_false", "fill_blank"])
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str | None = "basic"


class PointAwareSuggestionRequest(BaseModel):
    intent: str = Field(default="add_questions", pattern="^(add_questions|repair_question)$")
    experiment_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1, max_length=2000)
    question_id: str | None = None
    point_node_id: str | None = None
    point_node_ids: list[str] = Field(default_factory=list)
    point_key: str | None = None
    point_keys: list[str] = Field(default_factory=list)
    question_types: list[str] = Field(default_factory=lambda: ["single_choice", "true_false"])
    count: int = Field(default=3, ge=1, le=20)
    difficulty: str | None = "basic"


class WorkbenchSessionRequest(BaseModel):
    mode: str = Field(pattern="^(repair|create)$")
    experiment_id: str = Field(min_length=1)
    question_id: str | None = None
    point_node_id: str | None = None
    point_node_ids: list[str] = Field(default_factory=list)
    point_key: str | None = None
    point_keys: list[str] = Field(default_factory=list)


class WorkbenchMessageRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    question_types: list[str] = Field(default_factory=lambda: ["single_choice", "true_false"])
    count: int = Field(default=1, ge=1, le=20)
    difficulty: str | None = "basic"


class DraftUpdateRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    status: str | None = Field(default=None, pattern="^(draft|published|rejected)$")


class ExperimentAnswer(BaseModel):
    question_id: str = Field(min_length=1)
    answer: Any


class ExperimentQuestionSubmitRequest(BaseModel):
    student_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    attempt_kind: str = "practice"
    answers: list[ExperimentAnswer]
