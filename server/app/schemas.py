from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RagAskRequest(BaseModel):
    student_id: str | None = None
    question: str = Field(min_length=1)
    chapter_id: str | None = None
    experiment_id: str | None = None
    point_key: str | None = None
    knowledge_point_ids: list[str] = Field(default_factory=list)


class RagSourceAsset(BaseModel):
    path: str
    file_name: str
    kind: str = "figure"
    caption: str | None = None


class RagSource(BaseModel):
    chunk_id: str
    source_file: str | None = None
    page_number: int | None = None
    text_preview: str
    content_type: str | None = None
    caption: str | None = None
    section_path: list[str] = Field(default_factory=list)
    assets: list[RagSourceAsset] = Field(default_factory=list)


class RagAskResponse(BaseModel):
    answer: str
    sources: list[RagSource]
    mode: str
    review_required: bool = True


class AgentChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class AgentAskRequest(BaseModel):
    student_id: str | None = None
    user_id: str | None = None
    user_role: str = "student"
    question: str = Field(min_length=1)
    chapter_id: str | None = None
    experiment_id: str | None = None
    point_key: str | None = None
    knowledge_point_ids: list[str] = Field(default_factory=list)
    allow_progress_lookup: bool = True
    allow_rag_lookup: bool = True
    assessment_review: bool = False
    conversation_history: list[AgentChatMessage] = Field(default_factory=list, max_length=20)
    max_answer_chars: int | None = Field(default=None, ge=0, le=20000)


class AgentAskResponse(BaseModel):
    answer: str
    sources: list[RagSource] = Field(default_factory=list)
    mode: str
    classification: dict = Field(default_factory=dict)
    tool_calls: list[dict] = Field(default_factory=list)
    guardrail_decisions: list[dict] = Field(default_factory=list)
    rag_trace: dict = Field(default_factory=dict)
    review_required: bool = True


class MasteryEvent(BaseModel):
    event_type: str
    difficulty: str = "basic"
    correct: bool | None = None


class MasteryState(BaseModel):
    state_prob: list[float]
    mastery_score: float


class TestAnswer(BaseModel):
    question_id: str
    answer: str


class TestSubmitRequest(BaseModel):
    student_id: str
    chapter_id: str
    test_type: str = Field(pattern="^(pretest|posttest)$")
    answers: list[TestAnswer]


class StudentEventRequest(BaseModel):
    student_id: str
    event_type: str
    chapter_id: str | None = None
    unit_id: str | None = None
    knowledge_point_id: str | None = None
    experiment_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class FeedbackSubmitRequest(BaseModel):
    student_id: str = Field(min_length=1, max_length=128)
    feedback_type: str = Field(default="other", min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    class_id: str | None = Field(default=None, max_length=128)
    chapter_id: str | None = Field(default=None, max_length=128)
    unit_id: str | None = Field(default=None, max_length=128)
    knowledge_point_id: str | None = Field(default=None, max_length=128)
    experiment_id: str | None = Field(default=None, max_length=128)
    page_path: str | None = Field(default=None, max_length=500)
    metadata: dict = Field(default_factory=dict)


class FeedbackUpdateRequest(BaseModel):
    status: str | None = Field(default=None, pattern="^(open|in_progress|resolved|archived)$")
    internal_note: str | None = Field(default=None, max_length=4000)


class FeedbackAttachmentItem(BaseModel):
    id: str
    feedback_id: str
    original_file_name: str | None = None
    mime_type: str
    file_size_bytes: int
    created_at: datetime | None = None


class FeedbackItem(BaseModel):
    id: str
    student_id: str
    class_id: str | None = None
    student_name_snapshot: str | None = None
    class_name_snapshot: str | None = None
    feedback_type: str
    content: str
    status: str
    chapter_id: str | None = None
    unit_id: str | None = None
    knowledge_point_id: str | None = None
    experiment_id: str | None = None
    page_path: str | None = None
    source_event_id: int | None = None
    handler_user_id: str | None = None
    handler_display_name: str | None = None
    internal_note: str | None = None
    metadata: dict = Field(default_factory=dict)
    attachment_count: int = 0
    attachments: list[FeedbackAttachmentItem] = Field(default_factory=list)
    resolved_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FeedbackSubmitResponse(BaseModel):
    id: str
    status: str
    attachment_count: int = 0


class FeedbackSummaryResponse(BaseModel):
    total_count: int = 0
    open_count: int = 0
    in_progress_count: int = 0
    resolved_count: int = 0
    archived_count: int = 0
    recent_count: int = 0


class FeedbackListResponse(BaseModel):
    items: list[FeedbackItem]
    total: int
