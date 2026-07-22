from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from server.app.student_video_save_schemas import StudentVideoPersonalState


StudentHomeVideoFeedStatus = Literal["ok", "empty"]
StudentHomeVideoFeedReason = Literal["catalog", "recommended"]


class StudentHomeVideoRouteTarget(BaseModel):
    kind: Literal["point_detail"] = "point_detail"
    route: str
    node_id: str
    placement_node_id: str
    canonical_point_id: str
    source_node_id: str
    chapter_id: str | None = None
    catalog_path: list[str] = Field(default_factory=list)
    point_title: str
    context_title: str
    context_summary: str = ""


class StudentHomeVideoSubtitleTrack(BaseModel):
    id: str
    kind: str = "subtitles"
    language_code: str = "und"
    label: str = ""
    is_default: bool = False
    stream_path: str


class StudentHomeVideoMedia(BaseModel):
    media_id: str
    title: str = ""
    mime_type: str | None = None
    stream_path: str
    thumbnail_path: str | None = None
    duration_seconds: float | None = None
    subtitle_tracks: list[StudentHomeVideoSubtitleTrack] = Field(default_factory=list)


class StudentHomeVideoFeedItem(BaseModel):
    id: str
    instance_id: str
    node_id: str
    placement_node_id: str
    canonical_point_id: str
    chapter_id: str
    title: str
    summary: str = ""
    snippet: str = ""
    catalog_path: list[str] = Field(default_factory=list)
    badges: list[str] = Field(default_factory=list)
    video: StudentHomeVideoMedia
    target: StudentHomeVideoRouteTarget
    personal_state: StudentVideoPersonalState = Field(default_factory=StudentVideoPersonalState)
    reason: StudentHomeVideoFeedReason = "catalog"


class StudentHomeVideoFeedResponse(BaseModel):
    status: StudentHomeVideoFeedStatus = "ok"
    message: str = ""
    query: str = ""
    next_cursor: str | None = None
    has_more: bool = False
    batch_size: int = 0
    pool_size: int = 0
    items: list[StudentHomeVideoFeedItem] = Field(default_factory=list)
