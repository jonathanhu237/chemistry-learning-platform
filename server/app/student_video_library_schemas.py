from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


VideoLibraryResultType = Literal[
    "video_point",
    "experiment",
    "chapter_experiment",
    "knowledge_point",
    "ai_prompt",
]
VideoLibraryTargetKind = Literal["point_detail", "chapter_detail", "ai_chat"]
VideoLibraryStatus = Literal["ok", "fallback", "disabled", "empty", "error"]
VideoLibraryBackend = Literal["local", "elasticsearch", "disabled"]
VideoLibraryBrowseChipKind = Literal["phenomenon", "reagent", "chapter", "element_family", "knowledge"]


class StudentVideoLibrarySearchRequest(BaseModel):
    query: str = ""
    limit: int = Field(default=24, ge=1, le=50)
    domain: Literal["experiment_video"] = "experiment_video"


class StudentVideoLibraryRouteTarget(BaseModel):
    kind: VideoLibraryTargetKind
    route: str
    node_id: str | None = None
    placement_node_id: str | None = None
    canonical_point_id: str | None = None
    source_node_id: str | None = None
    profile_id: str | None = None
    chapter_id: str | None = None
    catalog_path: list[str] = Field(default_factory=list)
    property_key: str | None = None
    property_title: str | None = None
    element_symbol: str | None = None
    point_title: str | None = None
    context_title: str | None = None
    context_summary: str | None = None
    prompt: str | None = None


class StudentVideoLibraryResultItem(BaseModel):
    id: str
    type: VideoLibraryResultType
    title: str
    subtitle: str = ""
    snippet: str = ""
    score: float = 0
    badges: list[str] = Field(default_factory=list)
    action_label: str = ""
    target: StudentVideoLibraryRouteTarget | None = None
    disabled_reason: str | None = None


class StudentVideoLibraryResultGroup(BaseModel):
    key: str
    title: str
    summary: str = ""
    items: list[StudentVideoLibraryResultItem] = Field(default_factory=list)


class StudentVideoLibraryBrowseChip(BaseModel):
    kind: VideoLibraryBrowseChipKind
    label: str
    query: str
    profile_id: str | None = None
    chapter_id: str | None = None
    element_symbol: str | None = None


class StudentVideoLibraryBrowseState(BaseModel):
    recommended: list[StudentVideoLibraryResultItem] = Field(default_factory=list)
    recent: list[StudentVideoLibraryResultItem] = Field(default_factory=list)
    chips: list[StudentVideoLibraryBrowseChip] = Field(default_factory=list)


class StudentVideoLibrarySearchResponse(BaseModel):
    query: str = ""
    status: VideoLibraryStatus = "ok"
    backend: VideoLibraryBackend = "local"
    message: str = ""
    total: int = 0
    groups: list[StudentVideoLibraryResultGroup] = Field(default_factory=list)
    browse: StudentVideoLibraryBrowseState = Field(default_factory=StudentVideoLibraryBrowseState)
