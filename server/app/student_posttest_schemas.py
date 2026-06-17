from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


PosttestStatus = Literal["in_progress", "completed"]


class PublicPosttestQuestion(BaseModel):
    id: str
    experiment_id: str
    experiment_title: str
    question_type: Literal["single_choice", "true_false", "fill_blank"]
    stem: str
    options: list[Any] = Field(default_factory=list)
    related_chapter_ids: list[str] = Field(default_factory=list)
    related_knowledge_point_ids: list[str] = Field(default_factory=list)


class PosttestExperimentSummary(BaseModel):
    id: str
    code: str
    title: str
    parent_code: str | None = None
    parent_title: str | None = None


class StudentPosttestResponse(BaseModel):
    status: PosttestStatus
    session_id: str
    experiments: list[PosttestExperimentSummary] = Field(default_factory=list)
    questions: list[PublicPosttestQuestion] = Field(default_factory=list)


class StudentPosttestAnswer(BaseModel):
    question_id: str = Field(min_length=1)
    answer: Any


class StudentPosttestSubmitRequest(BaseModel):
    session_id: str = Field(min_length=1)
    answers: list[StudentPosttestAnswer] = Field(min_length=1)


class StudentPosttestWrongAnswer(BaseModel):
    question_id: str
    experiment_id: str
    experiment_title: str
    question_type: str
    stem: str
    options: list[Any] = Field(default_factory=list)
    submitted_answer: Any = None
    correct_answer: Any = None
    explanation: str | None = None


class StudentPosttestMasteryChange(BaseModel):
    knowledge_point_id: str
    experiment_id: str | None = None
    experiment_title: str | None = None
    content: str | None = None
    before_score: float
    after_score: float
    delta: float


class StudentPosttestReport(BaseModel):
    session_id: str
    experiments: list[PosttestExperimentSummary] = Field(default_factory=list)
    correct_count: int
    total_count: int
    score: float
    correct_rate: float
    mastery_before_average: float | None = None
    mastery_after_average: float | None = None
    mastery_delta: float | None = None
    mastery_changes: list[StudentPosttestMasteryChange] = Field(default_factory=list)
    wrong_answers: list[StudentPosttestWrongAnswer] = Field(default_factory=list)
    next_recommendation: str


class StudentPosttestSubmitResponse(BaseModel):
    status: Literal["completed"]
    report: StudentPosttestReport
