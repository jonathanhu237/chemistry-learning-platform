from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from server.app.student_assessment_report_schemas import StudentAssessmentReport


PretestStatus = Literal["in_progress", "completed"]
PretestStage = Literal[1, 2]


class PublicPretestQuestion(BaseModel):
    id: str
    question_type: Literal["single_choice", "true_false", "fill_blank"]
    stem: str
    options: list[Any] = Field(default_factory=list)
    area: str
    related_chapter_ids: list[str] = Field(default_factory=list)
    related_knowledge_point_ids: list[str] = Field(default_factory=list)


class StudentPretestResponse(BaseModel):
    status: PretestStatus
    session_id: str | None = None
    stage: PretestStage | None = None
    questions: list[PublicPretestQuestion] = Field(default_factory=list)
    report: StudentAssessmentReport | None = None


class StudentPretestAnswer(BaseModel):
    question_id: str = Field(min_length=1)
    answer: Any


class StudentPretestSubmitRequest(BaseModel):
    stage: PretestStage
    answers: list[StudentPretestAnswer] = Field(min_length=1)
