from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from server.app.student_learning_schemas import StudentLearningPageResponse


class CatalogNodeCreateRequest(BaseModel):
    chapter_id: str = Field(min_length=1)
    parent_id: str | None = None
    after_node_id: str | None = None
    node_kind: str = Field(default="directory", pattern="^(directory|point)$")
    title: str = Field(min_length=1, max_length=200)
    summary: str | None = None
    teacher_note: str | None = None
    canonical_point_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogNodeCopyRequest(BaseModel):
    chapter_id: str | None = None
    parent_id: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    include_subtree: bool = True


class CatalogNodeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = None
    node_kind: str | None = Field(default=None, pattern="^(directory|point)$")
    teacher_note: str | None = None
    metadata: dict[str, Any] | None = None


class CatalogNodeMoveRequest(BaseModel):
    parent_id: str | None = None
    display_order: int | None = None


class CatalogNodeReorderItem(BaseModel):
    node_id: str = Field(min_length=1)
    display_order: int


class CatalogNodeReorderRequest(BaseModel):
    items: list[CatalogNodeReorderItem] = Field(default_factory=list)


class CatalogNodeStatusRequest(BaseModel):
    action: str = Field(pattern="^(archive|restore|publish|unpublish)$")
    include_subtree: bool = False


class CatalogPreviewTokenResponse(BaseModel):
    preview_url: str
    token: str
    expires_at: str


class CatalogReactionEquationInput(BaseModel):
    raw_text: str = Field(default="", max_length=500)
    row_order: int | None = None
    label: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogReactionEquationNormalized(BaseModel):
    id: str | None = None
    node_id: str | None = None
    canonical_point_id: str | None = None
    row_order: int = 0
    raw_text: str
    equation_core: str = ""
    annotation_text: str = ""
    annotation_formulae: list[str] = Field(default_factory=list)
    annotation_aliases: list[str] = Field(default_factory=list)
    condition_tags: list[str] = Field(default_factory=list)
    canonical_display: str = ""
    canonical_mhchem: str | None = None
    plain_search_text: str = ""
    formulae: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    reactants: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    participants: dict[str, Any] = Field(default_factory=dict)
    reaction_features: list[str] = Field(default_factory=list)
    validation_status: str = Field(default="warning", pattern="^(valid|warning|invalid)$")
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    parser_version: str = "basic-v1"
    migrated_from_principle_equation: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    suggested_display: str | None = None
    suggested_mhchem: str | None = None
    suggestion_reason: str | None = None
    corrections: list[str] = Field(default_factory=list)


class CatalogEquationPreviewRequest(BaseModel):
    equations: list[CatalogReactionEquationInput] = Field(default_factory=list)
    multiline_text: str | None = Field(default=None, max_length=5000)


class CatalogEquationPreviewResponse(BaseModel):
    ok: bool
    equations: list[CatalogReactionEquationNormalized] = Field(default_factory=list)


class CatalogEquationAssistRequest(BaseModel):
    mode: str = Field(default="suggest", pattern="^(suggest|fix|generate|balance)$")
    multiline_text: str | None = Field(default=None, max_length=5000)
    equations: list[CatalogReactionEquationInput] = Field(default_factory=list)
    point_title: str | None = Field(default=None, max_length=200)
    catalog_path_text: str | None = None
    phenomenon_explanation: str | None = None
    safety_note: str | None = None


class CatalogEquationAssistDraft(BaseModel):
    draft_text: str
    source: str = "ai"
    rationale: str = ""
    row_order: int | None = None
    replacement_text: str | None = None
    canonical_display: str = ""
    canonical_mhchem: str | None = None
    annotation_text: str = ""
    annotation_formulae: list[str] = Field(default_factory=list)
    condition_tags: list[str] = Field(default_factory=list)
    validation_status: str = Field(default="warning", pattern="^(valid|warning|invalid)$")
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    formulae: list[str] = Field(default_factory=list)
    supplemental: bool = False


class CatalogEquationAssistResponse(BaseModel):
    available: bool
    reason: str | None = None
    drafts: list[CatalogEquationAssistDraft] = Field(default_factory=list)


class CatalogPointContentRequest(BaseModel):
    point_title: str = Field(min_length=1, max_length=200)
    teacher_note: str | None = None
    principle_mode: str = Field(default="text", pattern="^(equation|text)$")
    principle_equation: str | None = None
    principle_text: str | None = None
    reaction_equations: list[CatalogReactionEquationInput] = Field(default_factory=list)
    phenomenon_explanation: str | None = None
    safety_note: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogPointPublicationRequest(BaseModel):
    action: str = Field(pattern="^(publish|unpublish|archive)$")


class CatalogPointMediaBindRequest(BaseModel):
    media_asset_id: str = Field(min_length=1)
    title: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogPointRelatedLinkRequest(BaseModel):
    target_node_id: str = Field(min_length=1)
    relation_type: str = Field(default="manual", pattern="^(manual|default_override|generated_default)$")
    hidden: bool = False
    sort_order: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogPointRelatedLinksRequest(BaseModel):
    links: list[CatalogPointRelatedLinkRequest] = Field(default_factory=list)


class CatalogBreadcrumb(BaseModel):
    node_id: str
    title: str
    node_kind: str
    chapter_id: str


class CatalogNodeCard(BaseModel):
    node_id: str
    placement_node_id: str | None = None
    canonical_point_id: str | None = None
    canonical_point_title: str | None = None
    canonical_point_status: str | None = None
    chapter_id: str
    parent_id: str | None = None
    node_kind: str
    title: str
    summary: str = ""
    status: str
    display_order: int = 0
    teacher_note: str | None = Field(default=None, exclude=True)
    actions: list[str] = Field(default_factory=list)
    has_children: bool = False
    descendant_point_count: int = 0
    has_point_content: bool = False
    media_count: int = 0
    published_media_count: int = 0
    active_placement_count: int = 0
    validation: dict[str, Any] = Field(default_factory=dict)
    index_state: dict[str, Any] | None = None


class StudentCatalogChapterResponse(BaseModel):
    chapter_id: str
    chapter_title: str
    nodes: list[CatalogNodeCard] = Field(default_factory=list)


class StudentCatalogNodeResponse(BaseModel):
    node: CatalogNodeCard
    breadcrumbs: list[CatalogBreadcrumb] = Field(default_factory=list)
    children: list[CatalogNodeCard] = Field(default_factory=list)


class StudentPointVideo(BaseModel):
    media_id: str
    title: str
    mime_type: str | None = None
    stream_path: str | None = None
    thumbnail_path: str | None = None


class StudentRelatedPoint(BaseModel):
    node_id: str
    placement_node_id: str | None = None
    canonical_point_id: str | None = None
    title: str
    relation_type: str | None = None
    source_node_id: str | None = None


class StudentPointAssessmentContext(BaseModel):
    point_node_id: str
    placement_node_id: str
    canonical_point_id: str
    chapter_id: str
    source_node_id: str | None = None
    catalog_path: list[CatalogBreadcrumb] = Field(default_factory=list)


class StudentPointDetailResponse(BaseModel):
    node_id: str
    canonical_node_id: str
    source_node_id: str | None = None
    placement_node_id: str
    canonical_point_id: str
    chapter_id: str
    title: str
    summary: str = ""
    breadcrumbs: list[CatalogBreadcrumb] = Field(default_factory=list)
    principle_mode: str = "text"
    principle_equation: str | None = None
    principle_text: str | None = None
    reaction_equations: list[CatalogReactionEquationNormalized] = Field(default_factory=list)
    phenomenon_explanation: str | None = None
    safety_note: str | None = None
    videos: list[StudentPointVideo] = Field(default_factory=list)
    has_video: bool = False
    no_video_reason: str | None = None
    related_points: list[StudentRelatedPoint] = Field(default_factory=list)
    assessment_context: StudentPointAssessmentContext


class CatalogPreviewNodeResponse(BaseModel):
    node_kind: str = Field(pattern="^(directory|point)$")
    directory: StudentCatalogNodeResponse | None = None
    point: StudentPointDetailResponse | None = None
    learning_page: StudentLearningPageResponse | None = None
