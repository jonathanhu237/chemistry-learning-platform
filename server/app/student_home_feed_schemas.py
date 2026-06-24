from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from server.app.student_video_library_schemas import StudentVideoLibraryRouteTarget


StudentHomeVideoFeedStatus = Literal["ok", "empty"]
StudentHomeVideoFeedReason = Literal["catalog", "recommended", "recent", "weakness"]


class StudentHomeVideoMedia(BaseModel):
    media_id: str
    title: str = ""
    mime_type: str | None = None
    stream_path: str
    thumbnail_path: str | None = None
    duration_seconds: float | None = None


class StudentHomeVideoFeedItem(BaseModel):
    id: str
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
    target: StudentVideoLibraryRouteTarget
    reason: StudentHomeVideoFeedReason = "catalog"


class StudentHomeVideoFeedResponse(BaseModel):
    status: StudentHomeVideoFeedStatus = "ok"
    message: str = ""
    items: list[StudentHomeVideoFeedItem] = Field(default_factory=list)

