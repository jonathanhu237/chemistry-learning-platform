from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from server.app.schemas import AgentChatMessage


StudentAssistantContextType = Literal["learning_home", "experiment_group", "experiment_detail", "learning_profile", "learning_point"]


class StudentAssistantAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    context_type: StudentAssistantContextType
    context_title: str = Field(default="", max_length=200)
    context_summary: str = Field(default="", max_length=4000)
    chapter_id: str | None = None
    experiment_id: str | None = None
    point_key: str | None = None
    point_node_id: str | None = None
    source_node_id: str | None = None
    catalog_path: list[str] = Field(default_factory=list, max_length=20)
    knowledge_point_ids: list[str] = Field(default_factory=list, max_length=20)
    conversation_history: list[AgentChatMessage] = Field(default_factory=list, max_length=20)


class StudentAssistantPosttestRequest(BaseModel):
    session_id: str = Field(min_length=1)


class StudentAssistantGeneratedResponse(BaseModel):
    text: str
    source: Literal["ai", "fallback"]
    mode: str
    cached: bool = False
