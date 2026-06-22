from __future__ import annotations

from pydantic import BaseModel, Field


class StudentAppFeatureFlags(BaseModel):
    ai_assistant_enabled: bool = True
    feedback_enabled: bool = True
    student_ai_assistant_enabled: bool = True
    rag_access_enabled: bool = True


class StudentAppConfigResponse(BaseModel):
    features: StudentAppFeatureFlags
    preview_mode: bool = False
    preview_policy: dict | None = None


class StudentFeedbackSubmitRequest(BaseModel):
    feedback_type: str = Field(default="other", min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    chapter_id: str | None = Field(default=None, max_length=128)
    unit_id: str | None = Field(default=None, max_length=128)
    knowledge_point_id: str | None = Field(default=None, max_length=128)
    experiment_id: str | None = Field(default=None, max_length=128)
    point_node_id: str | None = Field(default=None, max_length=128)
    catalog_path: list[str] = Field(default_factory=list)
    page_path: str | None = Field(default=None, max_length=500)
    metadata: dict = Field(default_factory=dict)
