from __future__ import annotations

from typing import Any

from sqlalchemy import text


def clean(value: Any) -> str:
    return str(value or "").strip()


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = [value]
    return [clean(item) for item in values if clean(item)]


def unique_strings(*groups: Any) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in string_list(group):
            if value not in seen:
                seen.add(value)
                output.append(value)
    return output


def point_placement_id(point: dict[str, Any] | None) -> str:
    if not isinstance(point, dict):
        return ""
    return clean(
        point.get("source_placement_node_id")
        or point.get("placement_node_id")
        or point.get("point_node_id")
        or point.get("point_id")
        or point.get("node_id")
    )


def point_canonical_id(point: dict[str, Any] | None) -> str:
    if not isinstance(point, dict):
        return ""
    return clean(point.get("canonical_point_id") or point.get("primary_canonical_point_id"))


def point_title(point: dict[str, Any] | None) -> str:
    if not isinstance(point, dict):
        return ""
    return clean(point.get("point_title") or point.get("title") or point.get("canonical_point_title") or point_placement_id(point))


def collect_question_point_identity(payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> dict[str, list[str]]:
    metadata = metadata if isinstance(metadata, dict) else {}
    primary_points = metadata.get("primary_points") if isinstance(metadata.get("primary_points"), list) else []
    option_links = metadata.get("option_links") if isinstance(metadata.get("option_links"), list) else []
    placement_ids = unique_strings(
        payload.get("primary_point_node_ids"),
        payload.get("source_placement_node_ids"),
        metadata.get("primary_point_node_ids"),
        metadata.get("point_node_ids"),
        metadata.get("source_placement_node_ids"),
        [point_placement_id(point) for point in primary_points if isinstance(point, dict)],
        [point_placement_id(link) for link in option_links if isinstance(link, dict)],
    )
    canonical_ids = unique_strings(
        payload.get("primary_canonical_point_ids"),
        payload.get("canonical_point_ids"),
        metadata.get("primary_canonical_point_ids"),
        metadata.get("canonical_point_ids"),
        [point_canonical_id(point) for point in primary_points if isinstance(point, dict)],
        [point_canonical_id(link) for link in option_links if isinstance(link, dict)],
    )
    return {
        "placement_node_ids": placement_ids,
        "source_placement_node_ids": unique_strings(
            payload.get("source_placement_node_ids"),
            metadata.get("source_placement_node_ids"),
            placement_ids,
        ),
        "canonical_point_ids": canonical_ids,
    }


def _placement_rows(session: Any, placement_node_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not placement_node_ids:
        return {}
    rows = session.execute(
        text(
            """
            SELECT n.id AS placement_node_id,
                   n.canonical_point_id,
                   n.title AS placement_title,
                   n.chapter_id,
                   cp.title AS canonical_point_title
            FROM experiment_catalog_nodes n
            LEFT JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
            WHERE n.id = ANY(:node_ids)
              AND n.node_kind = 'point'
            """
        ),
        {"node_ids": placement_node_ids},
    ).mappings()
    return {clean(row["placement_node_id"]): dict(row) for row in rows}


def _canonical_rows(session: Any, canonical_point_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not canonical_point_ids:
        return {}
    rows = session.execute(
        text(
            """
            SELECT id AS canonical_point_id, title AS canonical_point_title
            FROM experiment_catalog_points
            WHERE id = ANY(:canonical_point_ids)
            """
        ),
        {"canonical_point_ids": canonical_point_ids},
    ).mappings()
    return {clean(row["canonical_point_id"]): dict(row) for row in rows}


def normalize_question_point_identity(session: Any, payload: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {})
    collected = collect_question_point_identity(payload, metadata)
    placement_ids = collected["placement_node_ids"]
    placement_rows = _placement_rows(session, placement_ids)
    mapped_canonical_ids = [
        clean(placement_rows[placement_id].get("canonical_point_id"))
        for placement_id in placement_ids
        if placement_id in placement_rows and clean(placement_rows[placement_id].get("canonical_point_id"))
    ]
    canonical_ids = unique_strings(collected["canonical_point_ids"], mapped_canonical_ids)
    canonical_rows = _canonical_rows(session, canonical_ids)
    source_placement_ids = unique_strings(
        collected["source_placement_node_ids"],
        [placement_id for placement_id in placement_ids if placement_id in placement_rows],
    )
    primary_point_node_ids = unique_strings(placement_ids)

    raw_points = metadata.get("primary_points") if isinstance(metadata.get("primary_points"), list) else []
    enriched_points: list[dict[str, Any]] = []
    seen_points: set[tuple[str, str]] = set()

    def add_point(raw: dict[str, Any], *, placement_id: str = "", canonical_id: str = "") -> None:
        row = placement_rows.get(placement_id) if placement_id else None
        canonical_id = clean(canonical_id or (row or {}).get("canonical_point_id"))
        canonical_row = canonical_rows.get(canonical_id) if canonical_id else None
        title = clean(
            raw.get("point_title")
            or raw.get("title")
            or (row or {}).get("canonical_point_title")
            or (row or {}).get("placement_title")
            or (canonical_row or {}).get("canonical_point_title")
            or placement_id
            or canonical_id
        )
        key = (placement_id, canonical_id)
        if key in seen_points:
            return
        seen_points.add(key)
        enriched_points.append(
            {
                **raw,
                "point_node_id": placement_id or raw.get("point_node_id") or "",
                "source_placement_node_id": placement_id or raw.get("source_placement_node_id") or "",
                "canonical_point_id": canonical_id or raw.get("canonical_point_id") or "",
                "point_title": title,
            }
        )

    for raw_point in raw_points:
        if not isinstance(raw_point, dict):
            continue
        add_point(raw_point, placement_id=point_placement_id(raw_point), canonical_id=point_canonical_id(raw_point))

    for placement_id in placement_ids:
        add_point({}, placement_id=placement_id)

    for canonical_id in canonical_ids:
        if canonical_id not in {point.get("canonical_point_id") for point in enriched_points}:
            add_point({}, canonical_id=canonical_id)

    metadata["primary_point_node_ids"] = primary_point_node_ids
    metadata["source_placement_node_ids"] = source_placement_ids
    metadata["primary_canonical_point_ids"] = canonical_ids
    if enriched_points:
        metadata["primary_points"] = enriched_points

    return {
        **payload,
        "primary_point_node_ids": primary_point_node_ids,
        "source_placement_node_ids": source_placement_ids,
        "primary_canonical_point_ids": canonical_ids,
        "metadata": metadata,
    }
