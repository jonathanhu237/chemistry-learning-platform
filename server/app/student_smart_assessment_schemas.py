from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from server.app.domains.platform.settings import CustomAssessmentSettings, SmartAssessmentSettings
from server.app.student_assessment_report_schemas import StudentAssessmentReport


SmartAssessmentStatus = Literal["in_progress", "completed"]
AssessmentMode = Literal["smart", "custom", "point"]


class PublicSmartAssessmentQuestion(BaseModel):
    id: str
    experiment_id: str
    experiment_title: str
    point_node_ids: list[str] = Field(default_factory=list)
    canonical_point_ids: list[str] = Field(default_factory=list)
    question_type: Literal["single_choice", "true_false", "fill_blank"]
    stem: str
    options: list[Any] = Field(default_factory=list)
    related_chapter_ids: list[str] = Field(default_factory=list)
    related_knowledge_point_ids: list[str] = Field(default_factory=list)


class SmartAssessmentPointSummary(BaseModel):
    id: str
    title: str
    experiment_id: str | None = None
    experiment_title: str | None = None
    canonical_point_id: str | None = None
    mastery_score: float | None = None
    before_score: float | None = None
    after_score: float | None = None
    evidence_count: int = 0
    source: Literal["measured", "untested", "custom", "point"] = "untested"
    draw_tickets: float | None = None
    question_count: int = 0
    reason: str | None = None


class SmartAssessmentExperimentSummary(BaseModel):
    id: str
    code: str
    title: str
    parent_code: str | None = None
    parent_title: str | None = None
    mastery_score: float | None = None
    evidence_count: int = 0
    source: Literal["measured", "untested", "custom", "point"] = "untested"
    draw_tickets: float | None = None
    question_count: int = 0
    measured_point_count: int = 0
    total_point_count: int = 0
    weak_point_count: int = 0
    reason: str | None = None
    points: list[SmartAssessmentPointSummary] = Field(default_factory=list)


class SmartAssessmentCompositionSummary(BaseModel):
    total_questions: int
    target_question_count: int
    requested_question_count: int | None = None
    selected_point_count: int = 0
    candidate_point_count: int = 0
    untested_question_count: int = 0
    measured_question_count: int = 0
    custom_question_count: int = 0
    untested_ratio_percent: int = 0
    weak_tendency_percent: int = 0
    max_questions_per_experiment: int = 1
    warnings: dict[str, Any] = Field(default_factory=dict)


class StudentSmartAssessmentResponse(BaseModel):
    status: SmartAssessmentStatus
    session_id: str
    assessment_mode: AssessmentMode = "smart"
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
    point_node_ids: list[str] = Field(default_factory=list)
    canonical_point_ids: list[str] = Field(default_factory=list)
    question_type: str
    stem: str
    options: list[Any] = Field(default_factory=list)
    submitted_answer: Any = None
    correct_answer: Any = None
    explanation: str | None = None


class StudentSmartAssessmentMasteryChange(BaseModel):
    knowledge_point_id: str
    point_node_id: str | None = None
    point_title: str | None = None
    experiment_id: str | None = None
    experiment_title: str | None = None
    canonical_point_id: str | None = None
    content: str | None = None
    before_score: float
    after_score: float
    delta: float


class StudentSmartAssessmentReport(BaseModel):
    session_id: str
    assessment_mode: AssessmentMode = "smart"
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
    assessment_report: StudentAssessmentReport | None = None


class StudentAssessmentStatusResponse(BaseModel):
    has_completed_smart_baseline: bool = False
    has_open_assessment: bool = False
    open_session_id: str | None = None
    open_assessment_mode: AssessmentMode | None = None
    smart_baseline_prompt_dismissed: bool = False


class StudentPointAssessmentStartRequest(BaseModel):
    point_node_id: str = Field(min_length=1)


class SmartAssessmentStrategyResponse(BaseModel):
    strategy: SmartAssessmentSettings
    inherited_strategy: SmartAssessmentSettings
    source: Literal["system_default", "class"] = "system_default"
    has_override: bool = False
    can_edit: bool = False


class CustomAssessmentExperimentOption(BaseModel):
    id: str
    code: str
    title: str
    parent_code: str | None = None
    parent_title: str | None = None
    question_count: int = 0


class CustomAssessmentOptionsSettings(BaseModel):
    enabled: bool = True
    question_count_options: list[int] = Field(default_factory=list)
    default_question_count: int = 10
    max_question_count: int = 20
    max_questions_per_experiment: int = 3


class StudentCustomAssessmentOptionsResponse(BaseModel):
    settings: CustomAssessmentOptionsSettings
    experiments: list[CustomAssessmentExperimentOption] = Field(default_factory=list)


class StudentCustomAssessmentStartRequest(BaseModel):
    experiment_ids: list[str] = Field(min_length=1)
    question_count: int


class CustomAssessmentSettingsResponse(BaseModel):
    settings: CustomAssessmentSettings
    inherited_settings: CustomAssessmentSettings
    source: Literal["system_default", "class"] = "system_default"
    has_override: bool = False
    can_edit: bool = False


class SmartAssessmentClassPreviewExperiment(BaseModel):
    id: str
    title: str
    candidate_point_count: int = 0
    untested_point_count: int = 0
    measured_point_count: int = 0
    average_mastery_score: float | None = None
    estimated_draw_tickets: float = 0
    estimated_question_count: float = 0


class SmartAssessmentClassPreviewResponse(BaseModel):
    strategy: SmartAssessmentSettings
    source: Literal["system_default", "class"] = "system_default"
    has_override: bool = False
    class_student_count: int = 0
    candidate_point_count: int = 0
    measured_point_count: int = 0
    untested_point_count: int = 0
    target_question_count: int = 0
    untested_target_count: int = 0
    measured_target_count: int = 0
    experiments: list[SmartAssessmentClassPreviewExperiment] = Field(default_factory=list)
    warnings: dict[str, Any] = Field(default_factory=dict)
