from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


AssessmentReportType = Literal["pretest", "smart", "custom", "point", "posttest"]
AssessmentReportTextSource = Literal["ai", "fallback"]
AssessmentReportPromptSource = Literal["global", "class"]


class AssessmentReportGeneratedText(BaseModel):
    text: str = ""
    source: AssessmentReportTextSource = "fallback"
    mode: str = "fallback"
    generated_at: datetime | None = None


class AssessmentReportPromptSettings(BaseModel):
    summary_prompt: str = Field(min_length=1, max_length=6000)
    mistake_prompt: str = Field(min_length=1, max_length=6000)


class AssessmentReportPromptSettingsUpdate(BaseModel):
    summary_prompt: str = Field(min_length=1, max_length=6000)
    mistake_prompt: str = Field(min_length=1, max_length=6000)


class AssessmentReportPromptSettingsResponse(BaseModel):
    settings: AssessmentReportPromptSettings
    inherited_settings: AssessmentReportPromptSettings | None = None
    source: AssessmentReportPromptSource = "global"
    has_override: bool = False
    supported_variables: list[str] = Field(default_factory=list)
    can_edit: bool = False


class StudentAssessmentReportSummary(BaseModel):
    id: str
    student_id: str
    class_id: str | None = None
    report_type: AssessmentReportType
    source_session_id: str
    title: str
    score: float
    correct_count: int
    total_count: int
    correct_rate: float
    wrong_count: int
    completed_at: datetime


class StudentAssessmentReport(StudentAssessmentReportSummary):
    summary: AssessmentReportGeneratedText
    mistake_explanation: AssessmentReportGeneratedText
    prompt_snapshot: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)


class StudentAssessmentReportListResponse(BaseModel):
    reports: list[StudentAssessmentReportSummary] = Field(default_factory=list)
