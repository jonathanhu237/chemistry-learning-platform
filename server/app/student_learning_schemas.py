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


class StudentLearningReferenceMedia(BaseModel):
    id: str
    usage: str
    asset_type: str
    source_url: str
    license: str
    attribution: str
    alt_text: str
    local_path: str | None = None
    element_symbols: list[str] = Field(default_factory=list)
    property_keys: list[str] = Field(default_factory=list)


class StudentLearningHero(BaseModel):
    eyebrow: str = ""
    title: str
    summary: str = ""


class StudentLearningElementBadge(BaseModel):
    symbol: str
    name: str
    atomic_number: int | None = None
    card_focus: str | None = None
    card_relevance: str | None = None
    card_tags: list[str] = Field(default_factory=list)
    relative_atomic_mass: str | None = None
    group: str | None = None
    period: int | None = None
    block: str | None = None
    state_at_20c: str | None = None
    density: str | None = None
    rsc_url: str | None = None
    fact_source: str | None = None
    state: str | None = None
    group_label: str | None = None
    electron_configuration: str | None = None
    common_valence: str | None = None
    redox_tendency: str | None = None
    note: str | None = None


class StudentLearningPropertyCard(BaseModel):
    key: str
    label: str
    value: str
    description: str = ""


class StudentLearningPropertySection(BaseModel):
    key: str
    title: str
    subtitle: str = ""
    summary: str = ""
    formula: str = ""
    tone: str = "green"


class StudentLearningProfileSummary(BaseModel):
    profile_id: str
    chapter_id: str
    title: str
    subtitle: str = ""
    family_number: str = ""
    family_name: str = ""
    element_symbols: list[str] = Field(default_factory=list)


class StudentLearningProfile(BaseModel):
    profile_id: str
    chapter_id: str
    title: str
    subtitle: str = ""
    family_number: str = ""
    family_name: str = ""
    hero: StudentLearningHero
    default_element_symbol: str | None = None
    element_symbols: list[str] = Field(default_factory=list)
    elements: list[StudentLearningElementBadge] = Field(default_factory=list)
    property_cards: list[StudentLearningPropertyCard] = Field(default_factory=list)
    family_common_properties: list[StudentLearningPropertyCard] = Field(default_factory=list)
    property_sections: list[StudentLearningPropertySection] = Field(default_factory=list)
    reference_media: list[StudentLearningReferenceMedia] = Field(default_factory=list)


class StudentLearningRecommendedPoint(BaseModel):
    node_id: str
    chapter_id: str
    title: str
    summary: str = ""
    catalog_path: list[str] = Field(default_factory=list)
    reason: str = "建议学习"
    mastery_score: float | None = None
    has_video: bool = False


class StudentLearningPageResponse(BaseModel):
    recommended_profile_id: str | None = None
    profiles: list[StudentLearningProfileSummary] = Field(default_factory=list)
    active_profile: StudentLearningProfile | None = None
    recommended_points: list[StudentLearningRecommendedPoint] = Field(default_factory=list)
