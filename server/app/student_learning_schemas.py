from __future__ import annotations

from pydantic import BaseModel, Field


class StudentLearningArea(BaseModel):
    area_id: str
    area_name: str
    enabled: bool = True
    parent_codes: list[str] = Field(default_factory=list)
    experiment_count: int = 0
    published_video_count: int = 0
    question_count: int = 0


class StudentExperimentGroupSummary(BaseModel):
    parent_code: str
    parent_title: str
    area_id: str
    area_name: str
    chapter_ids: list[str] = Field(default_factory=list)
    experiment_count: int = 0
    published_video_count: int = 0
    question_count: int = 0
    recommended: bool = False


class StudentLearningHomeResponse(BaseModel):
    recommended_area_id: str | None = None
    recommended_parent_code: str | None = None
    areas: list[StudentLearningArea] = Field(default_factory=list)
    groups: list[StudentExperimentGroupSummary] = Field(default_factory=list)


class StudentVideoResource(BaseModel):
    media_id: str
    title: str
    point_key: str | None = None
    point_title: str | None = None
    mime_type: str | None = None
    stream_path: str | None = None
    thumbnail_path: str | None = None


class StudentExperimentPointSummary(BaseModel):
    id: str
    code: str
    title: str
    summary: str | None = None
    parent_code: str
    parent_title: str
    module_title: str | None = None
    chapter_ids: list[str] = Field(default_factory=list)
    video_candidate_count: int = 0
    published_video_count: int = 0
    question_count: int = 0


class StudentExperimentGroupResponse(BaseModel):
    parent_code: str
    parent_title: str
    area_id: str
    area_name: str
    experiments: list[StudentExperimentPointSummary] = Field(default_factory=list)


class StudentExperimentDetailResponse(StudentExperimentPointSummary):
    video_candidates: list[str] = Field(default_factory=list)
    videos: list[StudentVideoResource] = Field(default_factory=list)
