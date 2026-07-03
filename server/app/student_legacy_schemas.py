from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LegacyStudentVideoPointItem(BaseModel):
    id: str
    node_id: str
    chapter_id: str | None = None
    title: str
    summary: str = ""
    snippet: str = ""
    catalog_path: list[str] = Field(default_factory=list)
    media_count: int = 0
    published_media_count: int = 0
    preview_stream_path: str | None = None
    thumbnail_path: str | None = None
    is_recommended: bool = False
    recommended_order: int | None = None


class LegacyStudentVideoPointResponse(BaseModel):
    status: Literal["ok", "empty"] = "ok"
    query: str = ""
    total: int = 0
    items: list[LegacyStudentVideoPointItem] = Field(default_factory=list)


class LegacyRecommendationUpdateRequest(BaseModel):
    recommended: bool = True
    sort_order: int = 0


class LegacyReportGeneratedText(BaseModel):
    text: str = ""
    source: Literal["ai", "fallback"] = "fallback"
    mode: str = "legacy_fallback"
    generated_at: datetime | None = None


class LegacyAssessmentReportSummary(BaseModel):
    id: str
    title: str
    report_type: str = "smart"
    source_session_id: str
    score: float = 0
    correct_count: int = 0
    total_count: int = 0
    correct_rate: float = 0
    wrong_count: int = 0
    completed_at: datetime


class LegacyWrongQuestionExplanation(BaseModel):
    question_id: str
    stem: str
    experiment_title: str = ""
    question_type: str = ""
    submitted_answer: str = "未作答"
    correct_answer: str = "未提供"
    explanation: str = ""
    explanation_source: Literal["stored", "fallback"] = "fallback"
    options: list[str] = Field(default_factory=list)


class LegacyAssessmentReportDetail(LegacyAssessmentReportSummary):
    ai_summary: LegacyReportGeneratedText
    mistake_explanation: LegacyReportGeneratedText | None = None
    next_steps: str = ""
    covered_experiments: list[str] = Field(default_factory=list)
    wrong_questions: list[LegacyWrongQuestionExplanation] = Field(default_factory=list)


class LegacyAssessmentReportListResponse(BaseModel):
    reports: list[LegacyAssessmentReportSummary] = Field(default_factory=list)
