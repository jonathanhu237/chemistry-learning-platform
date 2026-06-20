from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from server.app.domains.platform.settings import SmartAssessmentSettings


SmartAssessmentStatus = Literal["in_progress", "completed"]


class PublicSmartAssessmentQuestion(BaseModel):
    id: str
    experiment_id: str
    experiment_title: str
    question_type: Literal["single_choice", "true_false", "fill_blank"]
    stem: str
    options: list[Any] = Field(default_factory=list)
    related_chapter_ids: list[str] = Field(default_factory=list)
    related_knowledge_point_ids: list[str] = Field(default_factory=list)


class SmartAssessmentExperimentSummary(BaseModel):
    id: str
    code: str
    title: str
    parent_code: str | None = None
    parent_title: str | None = None
    mastery_score: float | None = None
    evidence_count: int = 0
    source: Literal["measured", "untested"] = "untested"
    draw_tickets: float | None = None
    question_count: int = 0
    reason: str | None = None


class SmartAssessmentCompositionSummary(BaseModel):
    total_questions: int
    target_question_count: int
    untested_question_count: int = 0
    measured_question_count: int = 0
    untested_ratio_percent: int = 0
    weak_tendency_percent: int = 0
    max_questions_per_experiment: int = 1
    warnings: dict[str, Any] = Field(default_factory=dict)


class StudentSmartAssessmentResponse(BaseModel):
    status: SmartAssessmentStatus
    session_id: str
    strategy: SmartAssessmentSettings
    composition: SmartAssessmentCompositionSummary
    experiments: list[SmartAssessmentExperimentSummary] = Field(default_factory=list)
    questions: list[PublicSmartAssessmentQuestion] = Field(default_factory=list)


class StudentSmartAssessmentAnswer(BaseModel):
    question_id: str = Field(min_length=1)
    answer: Any


class StudentSmartAssessmentSubmitRequest(BaseModel):
    session_id: str = Field(min_length=1)
    answers: list[StudentSmartAssessmentAnswer] = Field(min_length=1)


class StudentSmartAssessmentWrongAnswer(BaseModel):
    question_id: str
    experiment_id: str
    experiment_title: str
    question_type: str
    stem: str
    options: list[Any] = Field(default_factory=list)
    submitted_answer: Any = None
    correct_answer: Any = None
    explanation: str | None = None


class StudentSmartAssessmentMasteryChange(BaseModel):
    knowledge_point_id: str
    experiment_id: str | None = None
    experiment_title: str | None = None
    content: str | None = None
    before_score: float
    after_score: float
    delta: float


class StudentSmartAssessmentReport(BaseModel):
    session_id: str
    strategy: SmartAssessmentSettings
    composition: SmartAssessmentCompositionSummary
    experiments: list[SmartAssessmentExperimentSummary] = Field(default_factory=list)
    correct_count: int
    total_count: int
    score: float
    correct_rate: float
    mastery_before_average: float | None = None
    mastery_after_average: float | None = None
    mastery_delta: float | None = None
    mastery_changes: list[StudentSmartAssessmentMasteryChange] = Field(default_factory=list)
    wrong_answers: list[StudentSmartAssessmentWrongAnswer] = Field(default_factory=list)
    next_recommendation: str


class StudentSmartAssessmentSubmitResponse(BaseModel):
    status: Literal["completed"]
    report: StudentSmartAssessmentReport


class SmartAssessmentStrategyResponse(BaseModel):
    strategy: SmartAssessmentSettings
    inherited_strategy: SmartAssessmentSettings
    source: Literal["system_default", "class"] = "system_default"
    has_override: bool = False
    can_edit: bool = False
