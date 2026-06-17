from __future__ import annotations

import json
import hashlib
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from server.app.auth import AuthUser
from server.app.config import ROOT, get_settings
from server.app.database import db_session
from server.app.mastery import DEFAULT_EXPERIMENT_MASTERY_SCORE
from server.app.media import is_student_visible_media
from server.app.normalization import CHAPTER_AREA_MAP
from server.app.student_learning_schemas import (
    StudentExperimentDetailResponse,
    StudentExperimentGroupResponse,
    StudentExperimentGroupSummary,
    StudentExperimentPointSummary,
    StudentLearningElementBadge,
    StudentLearningArea,
    StudentLearningHero,
    StudentLearningHomeResponse,
    StudentLearningPageResponse,
    StudentLearningChapterExperimentGroup,
    StudentLearningPointCard,
    StudentLearningPointGroup,
    StudentLearningProfile,
    StudentLearningProfileSummary,
    StudentLearningPropertyCard,
    StudentLearningPropertySection,
    StudentLearningReferenceMedia,
    StudentVideoResource,
)

AREA_ORDER = ["p", "s", "ds", "d", "f"]
AREA_NAMES = {
    "p": "p区",
    "s": "s区",
    "ds": "ds区",
    "d": "d区",
    "f": "f区",
}
PRETEST_AREA_IDS = {
    "p区": "p",
    "s区": "s",
    "ds区": "ds",
    "d区": "d",
    "f区": "f",
}
DEFAULT_RECOMMENDED_AREA_ID = "p"
PROFILE_SEED_PATH = ROOT / "data" / "seed" / "student_learning" / "element_profiles.json"
REQUIRED_PROFILE_CARD_KEYS = {
    "atomic_number",
    "electron_configuration",
    "group",
    "common_valence",
    "elemental_state",
    "redox",
}
REQUIRED_ELEMENT_FACT_KEYS = {
    "atomic_number",
    "electron_configuration",
    "group_label",
    "common_valence",
    "state",
    "redox_tendency",
}
REFERENCE_MEDIA_REQUIRED_KEYS = {
    "id",
    "usage",
    "asset_type",
    "source_url",
    "license",
    "attribution",
    "alt_text",
}


@dataclass(frozen=True)
class ParentGroup:
    parent_code: str
    parent_title: str
    area_id: str
    area_name: str
    chapter_ids: tuple[str, ...]
    display_order: int
    experiments: tuple[dict[str, Any], ...]


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _candidate_point_key(index: int, title: str) -> str:
    digest = hashlib.sha1(title.strip().encode("utf-8")).hexdigest()[:8]
    return f"candidate-{index + 1}-{digest}"


def _student_id(user: AuthUser) -> str:
    return str(user.student_id or user.username).strip().upper()


def _chapter_area_id(chapter_id: str | None) -> str | None:
    if not chapter_id:
        return None
    chapter = CHAPTER_AREA_MAP.get(str(chapter_id))
    return str(chapter["area_id"]) if chapter else None


def _chapter_area_name(area_id: str) -> str:
    return AREA_NAMES.get(area_id, area_id)


def _metadata(experiment: dict[str, Any]) -> dict[str, Any]:
    value = experiment.get("metadata")
    return value if isinstance(value, dict) else {}


def _chapter_bindings(experiment: dict[str, Any]) -> list[dict[str, Any]]:
    value = experiment.get("chapter_bindings") or []
    return [item for item in value if isinstance(item, dict)]


def _parent_code(experiment: dict[str, Any]) -> str:
    metadata = _metadata(experiment)
    return str(metadata.get("parent_code") or experiment.get("code") or experiment.get("id"))


def _parent_title(experiment: dict[str, Any]) -> str:
    metadata = _metadata(experiment)
    return str(metadata.get("parent_title") or experiment.get("title") or _parent_code(experiment))


def _module_title(experiment: dict[str, Any]) -> str | None:
    metadata = _metadata(experiment)
    value = metadata.get("module_display_title") or metadata.get("module_title")
    return str(value) if value else None


def _video_candidates(experiment: dict[str, Any]) -> list[str]:
    raw = _metadata(experiment).get("video_candidates") or []
    if not isinstance(raw, list):
        return []
    candidates: list[str] = []
    seen: set[str] = set()
    for item in raw:
        title = str(item or "").strip()
        if title and title not in seen:
            candidates.append(title)
            seen.add(title)
    return candidates


@lru_cache(maxsize=1)
def _student_learning_seed() -> dict[str, Any]:
    return json.loads(PROFILE_SEED_PATH.read_text(encoding="utf-8-sig"))


def _learning_profiles() -> list[dict[str, Any]]:
    data = _student_learning_seed()
    profiles = [item for item in data.get("profiles") or [] if isinstance(item, dict)]
    return sorted(profiles, key=lambda item: (int(item.get("display_order") or 999), str(item.get("profile_id") or "")))


def validate_student_learning_profiles() -> dict[str, Any]:
    data = _student_learning_seed()
    profiles = [item for item in data.get("profiles") or [] if isinstance(item, dict)]
    errors: list[str] = []
    enabled_count = 0
    for index, profile in enumerate(profiles):
        if not profile.get("enabled", True):
            continue
        enabled_count += 1
        prefix = str(profile.get("profile_id") or f"profile[{index}]")
        for key in [
            "profile_id",
            "chapter_id",
            "title",
            "hero",
            "property_cards",
            "family_common_properties",
            "property_sections",
            "elements",
        ]:
            if not profile.get(key):
                errors.append(f"{prefix}: missing {key}")
        card_keys = {
            str(card.get("key") or "")
            for card in profile.get("property_cards") or []
            if isinstance(card, dict)
        }
        missing_cards = sorted(REQUIRED_PROFILE_CARD_KEYS - card_keys)
        if missing_cards:
            errors.append(f"{prefix}: missing property cards {', '.join(missing_cards)}")
        for section in profile.get("property_sections") or []:
            if not isinstance(section, dict):
                errors.append(f"{prefix}: property section is not an object")
                continue
            if not section.get("key") or not section.get("title"):
                errors.append(f"{prefix}: property section missing key/title")
        for element in profile.get("elements") or []:
            if not isinstance(element, dict):
                errors.append(f"{prefix}: element is not an object")
                continue
            symbol = str(element.get("symbol") or "<missing>")
            missing_facts = sorted(key for key in REQUIRED_ELEMENT_FACT_KEYS if element.get(key) in (None, ""))
            if missing_facts:
                errors.append(f"{prefix}: element {symbol} missing facts {', '.join(missing_facts)}")
        for media in profile.get("reference_media") or []:
            if not isinstance(media, dict):
                errors.append(f"{prefix}: reference media is not an object")
                continue
            missing_media = sorted(key for key in REFERENCE_MEDIA_REQUIRED_KEYS if not media.get(key))
            if missing_media:
                errors.append(f"{prefix}: reference media missing {', '.join(missing_media)}")
    return {
        "ok": not errors,
        "errors": errors,
        "profile_count": len(profiles),
        "enabled_profile_count": enabled_count,
        "version": data.get("version"),
    }


def _profile_summary(profile: dict[str, Any]) -> StudentLearningProfileSummary:
    return StudentLearningProfileSummary(
        profile_id=str(profile.get("profile_id") or ""),
        chapter_id=str(profile.get("chapter_id") or ""),
        title=str(profile.get("title") or ""),
        subtitle=str(profile.get("subtitle") or ""),
        family_number=str(profile.get("family_number") or ""),
        family_name=str(profile.get("family_name") or ""),
        element_symbols=[str(item) for item in profile.get("element_symbols") or [] if str(item).strip()],
    )


def _property_section(section: dict[str, Any]) -> StudentLearningPropertySection:
    return StudentLearningPropertySection(
        key=str(section.get("key") or ""),
        title=str(section.get("title") or ""),
        subtitle=str(section.get("subtitle") or ""),
        summary=str(section.get("summary") or ""),
        formula=str(section.get("formula") or ""),
        tone=str(section.get("tone") or "green"),
    )


def _property_cards(profile: dict[str, Any]) -> list[StudentLearningPropertyCard]:
    return [
        StudentLearningPropertyCard(
            key=str(card.get("key") or ""),
            label=str(card.get("label") or ""),
            value=str(card.get("value") or ""),
            description=str(card.get("description") or ""),
        )
        for card in profile.get("property_cards") or []
        if isinstance(card, dict)
    ]


def _family_common_properties(profile: dict[str, Any]) -> list[StudentLearningPropertyCard]:
    cards = profile.get("family_common_properties")
    if not isinstance(cards, list) or not cards:
        cards = profile.get("property_cards") or []
    return [
        StudentLearningPropertyCard(
            key=str(card.get("key") or ""),
            label=str(card.get("label") or ""),
            value=str(card.get("value") or ""),
            description=str(card.get("description") or ""),
        )
        for card in cards
        if isinstance(card, dict)
    ]


def _reference_media(profile: dict[str, Any]) -> list[StudentLearningReferenceMedia]:
    return [
        StudentLearningReferenceMedia(
            id=str(media.get("id") or ""),
            usage=str(media.get("usage") or ""),
            asset_type=str(media.get("asset_type") or ""),
            source_url=str(media.get("source_url") or ""),
            license=str(media.get("license") or ""),
            attribution=str(media.get("attribution") or ""),
            alt_text=str(media.get("alt_text") or ""),
            local_path=str(media.get("local_path")) if media.get("local_path") else None,
            element_symbols=[str(item) for item in media.get("element_symbols") or [] if str(item).strip()],
            property_keys=[str(item) for item in media.get("property_keys") or [] if str(item).strip()],
        )
        for media in profile.get("reference_media") or []
        if isinstance(media, dict)
    ]


def _element_badges(profile: dict[str, Any]) -> list[StudentLearningElementBadge]:
    return [
        StudentLearningElementBadge(
            symbol=str(element.get("symbol") or ""),
            name=str(element.get("name") or ""),
            atomic_number=int(element["atomic_number"]) if element.get("atomic_number") is not None else None,
            state=str(element.get("state")) if element.get("state") else None,
            group_label=str(element.get("group_label")) if element.get("group_label") else None,
            electron_configuration=str(element.get("electron_configuration")) if element.get("electron_configuration") else None,
            common_valence=str(element.get("common_valence")) if element.get("common_valence") else None,
            redox_tendency=str(element.get("redox_tendency")) if element.get("redox_tendency") else None,
            note=str(element.get("note")) if element.get("note") else None,
        )
        for element in profile.get("elements") or []
        if isinstance(element, dict)
    ]


def _media_resources(experiment: dict[str, Any], *, visible_only: bool = False) -> list[dict[str, Any]]:
    resources = experiment.get("media_resources") or []
    items = [item for item in resources if isinstance(item, dict)]
    if not visible_only:
        return items
    return [
        item
        for item in items
        if is_student_visible_media(str(item.get("upload_status") or ""), str(item.get("binding_status") or ""))
    ]


def _published_video_count(experiment: dict[str, Any]) -> int:
    return len(_media_resources(experiment, visible_only=True))


def _question_count(experiment: dict[str, Any]) -> int:
    return int(experiment.get("published_question_count") or 0)


def _experiment_chapter_ids(experiment: dict[str, Any]) -> tuple[str, ...]:
    ids: list[str] = []
    seen: set[str] = set()
    for binding in _chapter_bindings(experiment):
        chapter_id = str(binding.get("chapter_id") or "").strip()
        if chapter_id and chapter_id not in seen:
            ids.append(chapter_id)
            seen.add(chapter_id)
    return tuple(ids)


def _experiment_area_id(experiment: dict[str, Any]) -> str | None:
    bindings = sorted(
        _chapter_bindings(experiment),
        key=lambda item: (
            0 if item.get("coverage_type") == "primary" else 1,
            int(item.get("sort_order") or 999),
            str(item.get("chapter_id") or ""),
        ),
    )
    for binding in bindings:
        area_id = _chapter_area_id(str(binding.get("chapter_id") or ""))
        if area_id in AREA_NAMES:
            return area_id
    return None


def _point_summary(experiment: dict[str, Any]) -> StudentExperimentPointSummary:
    return StudentExperimentPointSummary(
        id=str(experiment["id"]),
        code=str(experiment.get("code") or ""),
        title=str(experiment.get("title") or experiment["id"]),
        summary=experiment.get("summary"),
        parent_code=_parent_code(experiment),
        parent_title=_parent_title(experiment),
        module_title=_module_title(experiment),
        chapter_ids=list(_experiment_chapter_ids(experiment)),
        video_candidate_count=len(_video_candidates(experiment)),
        published_video_count=_published_video_count(experiment),
        question_count=_question_count(experiment),
    )


def _group_summary(group: ParentGroup, *, recommended_parent_code: str | None = None) -> StudentExperimentGroupSummary:
    return StudentExperimentGroupSummary(
        parent_code=group.parent_code,
        parent_title=group.parent_title,
        area_id=group.area_id,
        area_name=group.area_name,
        chapter_ids=list(group.chapter_ids),
        experiment_count=len(group.experiments),
        published_video_count=sum(_published_video_count(experiment) for experiment in group.experiments),
        question_count=sum(_question_count(experiment) for experiment in group.experiments),
        recommended=group.parent_code == recommended_parent_code,
    )


def _build_parent_groups(experiments: list[dict[str, Any]]) -> list[ParentGroup]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for experiment in experiments:
        area_id = _experiment_area_id(experiment)
        if area_id not in AREA_NAMES or area_id == "f":
            continue
        buckets[(area_id, _parent_code(experiment))].append(experiment)

    groups: list[ParentGroup] = []
    for (area_id, parent_code), items in buckets.items():
        ordered_items = sorted(items, key=lambda item: (int(item.get("display_order") or 999), str(item.get("code") or "")))
        chapter_ids: list[str] = []
        seen_chapters: set[str] = set()
        for item in ordered_items:
            for chapter_id in _experiment_chapter_ids(item):
                if chapter_id not in seen_chapters:
                    chapter_ids.append(chapter_id)
                    seen_chapters.add(chapter_id)
        groups.append(
            ParentGroup(
                parent_code=parent_code,
                parent_title=_parent_title(ordered_items[0]),
                area_id=area_id,
                area_name=_chapter_area_name(area_id),
                chapter_ids=tuple(chapter_ids),
                display_order=min(int(item.get("display_order") or 999) for item in ordered_items),
                experiments=tuple(ordered_items),
            )
        )
    area_index = {area_id: index for index, area_id in enumerate(AREA_ORDER)}
    return sorted(groups, key=lambda group: (area_index.get(group.area_id, 99), group.display_order, group.parent_code))


def _student_experiment_sql(where_clause: str = "") -> str:
    return f"""
        SELECT
          fe.id,
          fe.code,
          fe.title,
          fe.summary,
          fe.status,
          fe.display_order,
          fe.metadata,
          COALESCE((
            SELECT jsonb_agg(
              jsonb_build_object(
                'chapter_id', ecb.chapter_id,
                'chapter_title', c.chapter_title,
                'chapter_number', c.chapter_number,
                'coverage_type', ecb.coverage_type,
                'sort_order', ecb.sort_order
              )
              ORDER BY ecb.sort_order, c.chapter_number NULLS LAST, ecb.chapter_id
            )
            FROM experiment_chapter_bindings ecb
            LEFT JOIN chapters c ON c.id = ecb.chapter_id
            WHERE ecb.experiment_id = fe.id
          ), '[]'::jsonb) AS chapter_bindings,
          COALESCE((
            SELECT jsonb_agg(
              jsonb_build_object(
                'media_id', ma.id,
                'title', COALESCE(mb.title, ma.title),
                'mime_type', COALESCE(ma.playback_mime_type, ma.mime_type),
                'upload_status', ma.upload_status,
                'binding_status', mb.status,
                'point_key', mb.metadata->>'point_key',
                'point_title', mb.metadata->>'point_title',
                'has_thumbnail', ma.thumbnail_relative_path IS NOT NULL
              )
              ORDER BY mb.sort_order, mb.created_at
            )
            FROM media_bindings mb
            JOIN media_assets ma ON ma.id = mb.media_asset_id
            WHERE mb.target_type = 'experiment'
              AND mb.target_id = fe.id
              AND mb.status <> 'archived'
          ), '[]'::jsonb) AS media_resources,
          (SELECT COUNT(*) FROM experiment_questions q WHERE q.experiment_id = fe.id AND q.status = 'published') AS published_question_count
        FROM formal_experiments fe
        {where_clause}
        ORDER BY fe.display_order, fe.code
    """


def _load_published_experiments(session: Any) -> list[dict[str, Any]]:
    rows = session.execute(
        text(
            _student_experiment_sql(
                """
                WHERE fe.status = 'published'
                  AND COALESCE(fe.metadata->>'archived_by_catalog_seed', 'false') <> 'true'
                """
            )
        )
    ).mappings()
    return [dict(row) for row in rows]


def _latest_pretest_area_id(session: Any, student_id: str) -> str | None:
    try:
        row = (
            session.execute(
                text(
                    """
                    SELECT weakest_area
                    FROM student_pretest_sessions
                    WHERE student_id = :student_id
                      AND status = 'completed'
                    ORDER BY completed_at DESC NULLS LAST, updated_at DESC, created_at DESC
                    LIMIT 1
                    """
                ),
                {"student_id": student_id},
            )
            .mappings()
            .first()
        )
    except SQLAlchemyError:
        # Compatibility barrier: the learning page must still open while the
        # pretest/learning-report branch is absent from a local database.
        session.rollback()
        return None
    if not row:
        return None
    return PRETEST_AREA_IDS.get(str(row.get("weakest_area") or ""))


def _lowest_mastery_chapter_id(session: Any, *, student_id: str, area_id: str) -> str | None:
    chapter_ids = [chapter_id for chapter_id, chapter in CHAPTER_AREA_MAP.items() if chapter.get("area_id") == area_id]
    if not chapter_ids:
        return None
    try:
        row = (
            session.execute(
                text(
                    """
                    SELECT kp.chapter_id, sm.mastery_score
                    FROM student_mastery sm
                    JOIN knowledge_points kp ON kp.id = sm.knowledge_point_id
                    WHERE sm.student_id = :student_id
                      AND kp.chapter_id = ANY(:chapter_ids)
                    ORDER BY sm.mastery_score ASC, kp.chapter_id ASC, kp.id ASC
                    LIMIT 1
                    """
                ),
                {"student_id": student_id, "chapter_ids": chapter_ids},
            )
            .mappings()
            .first()
        )
    except SQLAlchemyError:
        # Compatibility barrier: recommendation is optional; seed-backed
        # learning content is the source of truth for this page.
        session.rollback()
        return None
    return str(row["chapter_id"]) if row else None


def _lowest_experiment_mastery_parent_code(
    session: Any,
    *,
    student_id: str,
    groups: list[ParentGroup],
    area_id: str,
) -> str | None:
    candidates = [group for group in groups if group.area_id == area_id]
    if not candidates:
        return None
    experiment_ids = [
        str(experiment["id"])
        for group in candidates
        for experiment in group.experiments
    ]
    if not experiment_ids:
        return None
    try:
        mastery_scores = {
            str(row["experiment_id"]): float(row["mastery_score"])
            for row in session.execute(
                text(
                    """
                    SELECT experiment_id, mastery_score
                    FROM student_experiment_mastery
                    WHERE student_id = :student_id
                      AND experiment_id = ANY(:experiment_ids)
                    """
                ),
                {"student_id": student_id, "experiment_ids": experiment_ids},
            ).mappings()
        }
    except SQLAlchemyError:
        session.rollback()
        return None

    def group_average(group: ParentGroup) -> float:
        values = [
            mastery_scores.get(str(experiment["id"]), DEFAULT_EXPERIMENT_MASTERY_SCORE)
            for experiment in group.experiments
        ]
        return sum(values) / len(values) if values else DEFAULT_EXPERIMENT_MASTERY_SCORE

    weakest = min(candidates, key=lambda group: (group_average(group), group.display_order, group.parent_code))
    return weakest.parent_code


def _choose_recommendation(
    *,
    groups: list[ParentGroup],
    pretest_area_id: str | None,
    mastery_parent_code: str | None = None,
    mastery_chapter_id: str | None = None,
) -> tuple[str | None, str | None]:
    groups_by_area: dict[str, list[ParentGroup]] = defaultdict(list)
    for group in groups:
        groups_by_area[group.area_id].append(group)

    area_id = pretest_area_id if pretest_area_id in groups_by_area else DEFAULT_RECOMMENDED_AREA_ID
    if area_id not in groups_by_area:
        first_group = groups[0] if groups else None
        return (first_group.area_id, first_group.parent_code) if first_group else (None, None)

    candidates = groups_by_area[area_id]
    if mastery_parent_code:
        matched = next((group for group in candidates if group.parent_code == mastery_parent_code), None)
        if matched:
            return matched.area_id, matched.parent_code
    if mastery_chapter_id:
        matched = next((group for group in candidates if mastery_chapter_id in group.chapter_ids), None)
        if matched:
            return matched.area_id, matched.parent_code
    return candidates[0].area_id, candidates[0].parent_code


def _areas_for_groups(groups: list[ParentGroup]) -> list[StudentLearningArea]:
    groups_by_area: dict[str, list[ParentGroup]] = defaultdict(list)
    for group in groups:
        groups_by_area[group.area_id].append(group)

    areas: list[StudentLearningArea] = []
    for area_id in AREA_ORDER:
        area_groups = groups_by_area.get(area_id, [])
        areas.append(
            StudentLearningArea(
                area_id=area_id,
                area_name=_chapter_area_name(area_id),
                enabled=bool(area_groups),
                parent_codes=[group.parent_code for group in area_groups],
                experiment_count=sum(len(group.experiments) for group in area_groups),
                published_video_count=sum(
                    _published_video_count(experiment)
                    for group in area_groups
                    for experiment in group.experiments
                ),
                question_count=sum(_question_count(experiment) for group in area_groups for experiment in group.experiments),
            )
        )
    return areas


def _ensure_student_row(session: Any, user: AuthUser) -> None:
    student_id = _student_id(user)
    session.execute(
        text(
            """
            INSERT INTO students (id, display_name, class_name, user_id, student_id, class_id, status)
            VALUES (
              :student_id, :display_name, :class_name, CAST(:user_id AS uuid),
              :student_id, :class_id, 'active'
            )
            ON CONFLICT (id) DO UPDATE SET
              display_name = COALESCE(EXCLUDED.display_name, students.display_name),
              class_name = COALESCE(EXCLUDED.class_name, students.class_name),
              user_id = COALESCE(EXCLUDED.user_id, students.user_id),
              student_id = EXCLUDED.student_id,
              class_id = COALESCE(EXCLUDED.class_id, students.class_id),
              status = 'active',
              updated_at = now()
            """
        ),
        {
            "student_id": student_id,
            "display_name": user.display_name,
            "class_name": user.class_name,
            "user_id": user.id,
            "class_id": user.class_id,
        },
    )


def _record_learning_event(
    session: Any,
    *,
    user: AuthUser,
    event_type: str,
    parent_code: str | None = None,
    area_id: str | None = None,
    experiment_id: str | None = None,
    chapter_id: str | None = None,
) -> None:
    try:
        _ensure_student_row(session, user)
        session.execute(
            text(
                """
                INSERT INTO student_events (
                  student_id, event_type, chapter_id, experiment_id, metadata, created_at
                )
                VALUES (
                  :student_id,
                  :event_type,
                  :chapter_id,
                  CASE
                    WHEN CAST(:experiment_id AS text) IS NOT NULL
                     AND EXISTS (SELECT 1 FROM experiments e WHERE e.id = CAST(:experiment_id AS text))
                    THEN CAST(:experiment_id AS text)
                    ELSE NULL
                  END,
                  CAST(:metadata AS jsonb),
                  now()
                )
                """
            ),
            {
                "student_id": _student_id(user),
                "event_type": event_type,
                "chapter_id": chapter_id,
                "experiment_id": experiment_id,
                "metadata": _json(
                    {
                        "area_id": area_id,
                        "parent_code": parent_code,
                        "experiment_id": experiment_id,
                    }
                ),
            },
        )
    except SQLAlchemyError:
        session.rollback()


def get_student_learning_home(user: AuthUser) -> StudentLearningHomeResponse:
    with db_session() as session:
        experiments = _load_published_experiments(session)
        groups = _build_parent_groups(experiments)
        student_id = _student_id(user)
        pretest_area_id = _latest_pretest_area_id(session, student_id)
        recommendation_area_id = pretest_area_id or DEFAULT_RECOMMENDED_AREA_ID
        mastery_parent_code = _lowest_experiment_mastery_parent_code(
            session,
            student_id=student_id,
            groups=groups,
            area_id=recommendation_area_id,
        )
        mastery_chapter_id = _lowest_mastery_chapter_id(
            session,
            student_id=student_id,
            area_id=recommendation_area_id,
        )
        recommended_area_id, recommended_parent_code = _choose_recommendation(
            groups=groups,
            pretest_area_id=pretest_area_id,
            mastery_parent_code=mastery_parent_code,
            mastery_chapter_id=mastery_chapter_id,
        )
    return StudentLearningHomeResponse(
        recommended_area_id=recommended_area_id,
        recommended_parent_code=recommended_parent_code,
        areas=_areas_for_groups(groups),
        groups=[_group_summary(group, recommended_parent_code=recommended_parent_code) for group in groups],
    )


def get_student_experiment_group(user: AuthUser, parent_code: str) -> StudentExperimentGroupResponse:
    with db_session() as session:
        experiments = _load_published_experiments(session)
        groups = _build_parent_groups(experiments)
        group = next((item for item in groups if item.parent_code == parent_code), None)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment group not found")
        _record_learning_event(
            session,
            user=user,
            event_type="learning_group_opened",
            parent_code=group.parent_code,
            area_id=group.area_id,
            chapter_id=group.chapter_ids[0] if group.chapter_ids else None,
        )
    return StudentExperimentGroupResponse(
        parent_code=group.parent_code,
        parent_title=group.parent_title,
        area_id=group.area_id,
        area_name=group.area_name,
        experiments=[_point_summary(experiment) for experiment in group.experiments],
    )


def _student_video_resource(media: dict[str, Any]) -> StudentVideoResource:
    media_id = str(media.get("media_id") or "")
    has_thumbnail = bool(media.get("has_thumbnail"))
    return StudentVideoResource(
        media_id=media_id,
        title=str(media.get("title") or media_id),
        point_key=str(media.get("point_key")) if media.get("point_key") else None,
        point_title=str(media.get("point_title")) if media.get("point_title") else None,
        mime_type=str(media.get("mime_type")) if media.get("mime_type") else None,
        stream_path=f"/api/student/media/assets/{media_id}/stream" if media_id else None,
        thumbnail_path=f"/api/student/media/assets/{media_id}/thumbnail" if media_id and has_thumbnail else None,
    )


def _experiment_search_text(experiment: dict[str, Any]) -> str:
    metadata = _metadata(experiment)
    parts = [
        experiment.get("code"),
        experiment.get("title"),
        experiment.get("summary"),
        metadata.get("parent_code"),
        metadata.get("parent_title"),
        metadata.get("module_title"),
        metadata.get("module_display_title"),
        metadata.get("outline_group"),
        *(_video_candidates(experiment)),
    ]
    return " ".join(str(part or "") for part in parts).lower()


def _section_matches_experiment(section: dict[str, Any], experiment: dict[str, Any]) -> bool:
    keywords = [str(item).strip().lower() for item in section.get("experiment_keywords") or [] if str(item).strip()]
    if not keywords:
        return True
    text_value = _experiment_search_text(experiment)
    return any(keyword in text_value for keyword in keywords)


def _profile_experiments(profile: dict[str, Any], experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chapter_id = str(profile.get("chapter_id") or "").strip()
    matched = [experiment for experiment in experiments if chapter_id and chapter_id in _experiment_chapter_ids(experiment)]
    if matched:
        return matched
    keywords = [
        str(item).strip().lower()
        for section in profile.get("property_sections") or []
        if isinstance(section, dict)
        for item in section.get("experiment_keywords") or []
        if str(item).strip()
    ]
    if not keywords:
        return []
    return [
        experiment
        for experiment in experiments
        if any(keyword in _experiment_search_text(experiment) for keyword in keywords)
    ]


def validate_student_learning_experiment_coverage(experiments: list[dict[str, Any]]) -> dict[str, Any]:
    profiles = [profile for profile in _learning_profiles() if profile.get("enabled", True)]
    experiment_by_id = {str(experiment["id"]): experiment for experiment in experiments}
    strict_coverage: dict[str, list[str]] = defaultdict(list)
    actual_coverage: dict[str, list[str]] = defaultdict(list)
    profile_counts: dict[str, int] = {}
    errors: list[str] = []

    profile_chapter_ids: dict[str, str] = {}
    for profile in profiles:
        profile_id = str(profile.get("profile_id") or "")
        chapter_id = str(profile.get("chapter_id") or "").strip()
        if not profile_id or not chapter_id:
            errors.append(f"{profile_id or '<missing>'}: missing profile_id/chapter_id")
            continue
        if chapter_id in profile_chapter_ids:
            errors.append(f"{profile_id}: duplicate learning profile chapter_id {chapter_id}")
        profile_chapter_ids[chapter_id] = profile_id

        strict_matches = [
            experiment
            for experiment in experiments
            if chapter_id in _experiment_chapter_ids(experiment)
        ]
        actual_matches = _profile_experiments(profile, experiments)
        strict_ids = {str(experiment["id"]) for experiment in strict_matches}
        actual_ids = {str(experiment["id"]) for experiment in actual_matches}
        profile_counts[profile_id] = len(strict_ids)
        if not strict_ids:
            errors.append(f"{profile_id}: chapter {chapter_id} has no published experiments")
        extra_ids = sorted(actual_ids - strict_ids)
        if extra_ids:
            errors.append(f"{profile_id}: service coverage has non-chapter experiments {', '.join(extra_ids)}")
        missing_ids = sorted(strict_ids - actual_ids)
        if missing_ids:
            errors.append(f"{profile_id}: service coverage missed chapter experiments {', '.join(missing_ids)}")
        for experiment_id in strict_ids:
            strict_coverage[experiment_id].append(profile_id)
        for experiment_id in actual_ids:
            actual_coverage[experiment_id].append(profile_id)

    strict_covered_ids = set(strict_coverage)
    actual_covered_ids = set(actual_coverage)
    experiment_ids = set(experiment_by_id)
    uncovered_ids = sorted(experiment_ids - strict_covered_ids)
    if uncovered_ids:
        errors.append(f"uncovered published experiments: {', '.join(uncovered_ids)}")
    stale_ids = sorted(strict_covered_ids - experiment_ids)
    if stale_ids:
        errors.append(f"coverage references unknown experiments: {', '.join(stale_ids)}")
    if actual_covered_ids != strict_covered_ids:
        extra_actual = sorted(actual_covered_ids - strict_covered_ids)
        missing_actual = sorted(strict_covered_ids - actual_covered_ids)
        if extra_actual:
            errors.append(f"service coverage has extra experiments: {', '.join(extra_actual)}")
        if missing_actual:
            errors.append(f"service coverage missed experiments: {', '.join(missing_actual)}")

    multi_profile_experiment_ids = sorted(
        experiment_id
        for experiment_id, profile_ids in strict_coverage.items()
        if len(profile_ids) > 1
    )
    return {
        "ok": not errors,
        "errors": errors,
        "published_experiment_count": len(experiments),
        "enabled_profile_count": len(profiles),
        "covered_experiment_count": len(strict_covered_ids),
        "uncovered_experiment_count": len(uncovered_ids),
        "profiles_without_experiments": sorted(
            profile_id for profile_id, count in profile_counts.items() if count == 0
        ),
        "multi_profile_experiment_count": len(multi_profile_experiment_ids),
        "multi_profile_experiment_ids": multi_profile_experiment_ids,
        "profile_experiment_counts": profile_counts,
    }


def _candidate_point(experiment: dict[str, Any]) -> tuple[str | None, str | None]:
    for media in _media_resources(experiment, visible_only=True):
        point_key = str(media.get("point_key") or "").strip()
        point_title = str(media.get("point_title") or media.get("title") or "").strip()
        if point_key or point_title:
            return point_key or point_title, point_title or point_key
    candidates = _video_candidates(experiment)
    if candidates:
        return _candidate_point_key(0, candidates[0]), candidates[0]
    return None, None


def _learning_point_card(
    experiment: dict[str, Any],
    *,
    section: dict[str, Any],
) -> StudentLearningPointCard:
    summary = _point_summary(experiment)
    point_key, point_title = _candidate_point(experiment)
    return StudentLearningPointCard(
        **summary.model_dump(),
        property_key=str(section.get("key") or ""),
        property_title=str(section.get("title") or ""),
        point_key=point_key,
        point_title=point_title,
        formula=str(section.get("formula")) if section.get("formula") else None,
        videos=[_student_video_resource(media) for media in _media_resources(experiment, visible_only=True)],
        video_candidates=_video_candidates(experiment),
    )


def _learning_groups_for_section(
    *,
    section: dict[str, Any],
    experiments: list[dict[str, Any]],
) -> list[StudentLearningPointGroup]:
    matches = [experiment for experiment in experiments if _section_matches_experiment(section, experiment)]
    if not matches:
        matches = experiments[:]
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for experiment in matches:
        buckets[_parent_code(experiment)].append(experiment)

    groups: list[StudentLearningPointGroup] = []
    for parent_code, items in buckets.items():
        ordered_items = sorted(items, key=lambda item: (int(item.get("display_order") or 999), str(item.get("code") or "")))
        groups.append(
            StudentLearningPointGroup(
                property_key=str(section.get("key") or ""),
                property_title=str(section.get("title") or ""),
                parent_code=parent_code,
                parent_title=_parent_title(ordered_items[0]),
                points=[_learning_point_card(item, section=section) for item in ordered_items],
            )
        )
    return sorted(groups, key=lambda group: (group.parent_code, group.property_key))


def _learning_groups_for_chapter(
    *,
    profile: dict[str, Any],
    experiments: list[dict[str, Any]],
) -> list[StudentLearningChapterExperimentGroup]:
    section = {
        "key": "chapter",
        "title": str(profile.get("title") or profile.get("family_name") or "Chapter experiments"),
    }
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for experiment in experiments:
        buckets[_parent_code(experiment)].append(experiment)

    groups: list[StudentLearningChapterExperimentGroup] = []
    for parent_code, items in buckets.items():
        ordered_items = sorted(items, key=lambda item: (int(item.get("display_order") or 999), str(item.get("code") or "")))
        groups.append(
            StudentLearningChapterExperimentGroup(
                parent_code=parent_code,
                parent_title=_parent_title(ordered_items[0]),
                points=[_learning_point_card(item, section=section) for item in ordered_items],
            )
        )
    return sorted(groups, key=lambda group: group.parent_code)


def _select_learning_profile(
    *,
    profiles: list[dict[str, Any]],
    profile_id: str | None,
    session: Any,
    user: AuthUser,
) -> dict[str, Any] | None:
    enabled = [profile for profile in profiles if profile.get("enabled", True)]
    if not enabled:
        return None
    requested = str(profile_id or "").strip()
    if requested:
        match = next((profile for profile in enabled if str(profile.get("profile_id") or "") == requested), None)
        if match:
            return match

    student_id = _student_id(user)
    pretest_area_id = _latest_pretest_area_id(session, student_id)
    mastery_chapter_id = _lowest_mastery_chapter_id(
        session,
        student_id=student_id,
        area_id=pretest_area_id or DEFAULT_RECOMMENDED_AREA_ID,
    )
    if mastery_chapter_id:
        match = next((profile for profile in enabled if str(profile.get("chapter_id") or "") == mastery_chapter_id), None)
        if match:
            return match
    if pretest_area_id:
        area_chapters = {
            chapter_id
            for chapter_id, chapter in CHAPTER_AREA_MAP.items()
            if chapter.get("area_id") == pretest_area_id
        }
        match = next((profile for profile in enabled if str(profile.get("chapter_id") or "") in area_chapters), None)
        if match:
            return match
    return enabled[0]


def get_student_learning_page(user: AuthUser, profile_id: str | None = None) -> StudentLearningPageResponse:
    profiles = _learning_profiles()
    with db_session() as session:
        active = _select_learning_profile(profiles=profiles, profile_id=profile_id, session=session, user=user)
        experiments = _load_published_experiments(session)
        if active:
            _record_learning_event(
                session,
                user=user,
                event_type="learning_profile_opened",
                chapter_id=str(active.get("chapter_id") or "") or None,
            )
    if not active:
        return StudentLearningPageResponse(recommended_profile_id=None, profiles=[], active_profile=None)

    profile_experiments = _profile_experiments(active, experiments)
    sections = [section for section in active.get("property_sections") or [] if isinstance(section, dict)]
    related_groups = [
        group
        for section in sections
        for group in _learning_groups_for_section(section=section, experiments=profile_experiments)
    ]
    chapter_experiment_groups = _learning_groups_for_chapter(profile=active, experiments=profile_experiments)
    hero = active.get("hero") if isinstance(active.get("hero"), dict) else {}
    active_profile = StudentLearningProfile(
        profile_id=str(active.get("profile_id") or ""),
        chapter_id=str(active.get("chapter_id") or ""),
        title=str(active.get("title") or ""),
        subtitle=str(active.get("subtitle") or ""),
        family_number=str(active.get("family_number") or ""),
        family_name=str(active.get("family_name") or ""),
        hero=StudentLearningHero(
            eyebrow=str(hero.get("eyebrow") or ""),
            title=str(hero.get("title") or active.get("title") or ""),
            summary=str(hero.get("summary") or ""),
        ),
        default_element_symbol=str(active.get("default_element_symbol")) if active.get("default_element_symbol") else None,
        element_symbols=[str(item) for item in active.get("element_symbols") or [] if str(item).strip()],
        elements=_element_badges(active),
        property_cards=_property_cards(active),
        family_common_properties=_family_common_properties(active),
        property_sections=[_property_section(section) for section in sections],
        reference_media=_reference_media(active),
        related_groups=related_groups,
        chapter_experiment_groups=chapter_experiment_groups,
    )
    return StudentLearningPageResponse(
        recommended_profile_id=str(active.get("profile_id") or ""),
        profiles=[_profile_summary(profile) for profile in profiles if profile.get("enabled", True)],
        active_profile=active_profile,
    )


def get_student_experiment_detail(user: AuthUser, experiment_id: str) -> StudentExperimentDetailResponse:
    with db_session() as session:
        experiments = _load_published_experiments(session)
        experiment = next((item for item in experiments if str(item["id"]) == experiment_id), None)
        if not experiment or _experiment_area_id(experiment) == "f":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
        summary = _point_summary(experiment)
        visible_videos = _media_resources(experiment, visible_only=True)
        _record_learning_event(
            session,
            user=user,
            event_type="experiment_detail_opened",
            parent_code=summary.parent_code,
            area_id=_experiment_area_id(experiment),
            experiment_id=summary.id,
            chapter_id=summary.chapter_ids[0] if summary.chapter_ids else None,
        )
    return StudentExperimentDetailResponse(
        **summary.model_dump(),
        video_candidates=_video_candidates(experiment),
        videos=[_student_video_resource(media) for media in visible_videos],
    )


def _published_student_media_row(asset_id: str) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT ma.id,
                           COALESCE(ma.playback_relative_path, ma.relative_path) AS relative_path,
                           COALESCE(ma.playback_mime_type, ma.mime_type) AS mime_type,
                           ma.original_file_name,
                           ma.thumbnail_relative_path
                    FROM media_assets ma
                    JOIN media_bindings mb ON mb.media_asset_id = ma.id
                    JOIN formal_experiments fe ON fe.id = mb.target_id
                    WHERE ma.id = CAST(:asset_id AS uuid)
                      AND ma.upload_status = 'ready'
                      AND mb.target_type = 'experiment'
                      AND mb.status = 'published'
                      AND fe.status = 'published'
                    LIMIT 1
                    """
                ),
                {"asset_id": asset_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    return dict(row)


def _safe_media_file(relative_path: str) -> Path:
    root = get_settings().media_root.resolve()
    path = (root / relative_path).resolve()
    if root != path and root not in path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")
    return path


def stream_student_media_asset(asset_id: str) -> FileResponse:
    row = _published_student_media_row(asset_id)
    file_path = _safe_media_file(str(row["relative_path"]))
    return FileResponse(
        file_path,
        media_type=row.get("mime_type") or "application/octet-stream",
        filename=row.get("original_file_name") or file_path.name,
    )


def get_student_media_thumbnail(asset_id: str) -> FileResponse:
    row = _published_student_media_row(asset_id)
    thumbnail = row.get("thumbnail_relative_path")
    if not thumbnail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    return FileResponse(_safe_media_file(str(thumbnail)), media_type="image/jpeg", filename=f"{asset_id}.jpg")
