from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from server.app.domains import student_home_feed as home_feed_service
from server.app.student_video_save_schemas import StudentVideoPersonalState
from server.tests.route_helpers import assert_route


class _SessionContext:
    def __enter__(self) -> object:
        return object()

    def __exit__(self, *_args: object) -> None:
        return None


def _row(
    suffix: str,
    *,
    chapter_number: int = 13,
    point_title: str | None = None,
    snippet: str = "颜色变化",
    media_title: str | None = None,
    recommended: bool = False,
    recommended_order: int | None = None,
    recommended_updated_at: str | None = None,
) -> dict[str, Any]:
    return {
        "node_id": f"cat-point-{suffix}",
        "placement_node_id": f"cat-point-{suffix}",
        "canonical_point_id": f"cat-canon-{suffix}",
        "chapter_id": f"CH{chapter_number}",
        "chapter_title": f"第 {chapter_number} 章",
        "chapter_number": chapter_number,
        "node_title": point_title or f"实验 {suffix}",
        "node_display_order": int(suffix),
        "point_title": point_title or f"实验 {suffix}",
        "point_summary": f"实验 {suffix} 摘要",
        "snippet": snippet,
        "principle_equation": "Cl2 + 2KI = 2KCl + I2",
        "principle_text": "氯气氧化碘离子",
        "phenomenon_explanation": snippet,
        "safety_note": "保持通风",
        "catalog_path": ["实验目录", point_title or f"实验 {suffix}"],
        "catalog_order_path": [1, int(suffix)],
        "media_id": f"00000000-0000-0000-0000-0000000000{suffix}",
        "media_title": media_title or f"实验 {suffix} 视频",
        "mime_type": "video/mp4",
        "duration_seconds": 35,
        "has_thumbnail": True,
        "reaction_features": [],
        "condition_tags": [],
        "phenomenon_tags": [],
        "property_tags": [],
        "is_recommended": recommended,
        "recommended_order": recommended_order,
        "recommended_updated_at": recommended_updated_at,
    }


def _install_rows(monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, Any]]) -> None:
    monkeypatch.setattr(home_feed_service, "db_session", lambda: _SessionContext())
    monkeypatch.setattr(home_feed_service, "_feed_rows", lambda _session: rows)


def test_student_home_video_feed_route_is_registered() -> None:
    assert_route("/api/student/home-video-feed", "GET")


def test_home_feed_sql_enforces_canonical_publication_and_playback_contract() -> None:
    source = Path("server/app/domains/student_home_feed.py").read_text(encoding="utf-8")
    visibility_source = Path("server/app/domains/media/student_catalog_visibility.py").read_text(encoding="utf-8")

    assert "eq.condition_tags" not in source
    assert "student_home_video_recommendations" in source
    assert "STUDENT_VISIBLE_PLAYABLE_MEDIA_CTES" in source
    assert "FROM student_visible_playable_media visible_media" in source
    assert "content_status = 'published'" in visibility_source
    assert "binding.binding_status = 'published'" in visibility_source
    assert "asset.upload_status = 'ready'" in visibility_source
    assert "asset.playback_relative_path" in visibility_source
    assert "placeholder_video" in visibility_source
    assert "no-video-placeholder.mp4" in visibility_source
    assert source.count("media.mime_type") == 1
    for derived_field in [
        "plain_search_text",
        "canonical_display",
        "raw_text",
        "equation.formulae",
        "equation.aliases",
        "equation.reactants",
        "equation.products",
    ]:
        assert derived_field in source


def test_student_home_video_feed_maps_rows_to_stable_video_cards(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_rows(monkeypatch, [_row("01", recommended=True, recommended_order=0)])

    response = home_feed_service.student_home_video_feed(object(), limit=99)

    assert response.status == "ok"
    assert response.query == ""
    assert response.batch_size == 30
    assert response.has_more is False
    assert response.next_cursor is None
    assert response.pool_size == 1
    item = response.items[0]
    assert item.id == "home-video:cat-point-01:00000000-0000-0000-0000-000000000001"
    assert item.instance_id == item.id
    assert item.reason == "recommended"
    assert item.badges == ["第 13 章", "实验目录", "实验 01"]
    assert item.video.stream_path.endswith("/00000000-0000-0000-0000-000000000001/stream")
    assert item.video.thumbnail_path.endswith("/00000000-0000-0000-0000-000000000001/thumbnail")
    assert item.target.kind == "point_detail"
    assert item.target.node_id == "cat-point-01"
    assert item.personal_state.favorite is False


def test_query_normalization_and_matches_are_token_and_across_catalog_content_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        _row("01", point_title="KI 水溶液检验", snippet="加入淀粉后出现蓝色", media_title="unrelated clip"),
        _row("02", point_title="氯水漂白", snippet="试纸逐渐褪色", media_title="KI 蓝色 only in media title"),
    ]
    _install_rows(monkeypatch, rows)

    response = home_feed_service.student_home_video_feed(object(), query="  KI，蓝色 / ", limit=12)
    media_title_only = home_feed_service.student_home_video_feed(object(), query="only in media title", limit=12)

    assert response.query == "ki 蓝色"
    assert [item.placement_node_id for item in response.items] == ["cat-point-01"]
    assert media_title_only.status == "empty"
    assert media_title_only.items == []


def test_query_matches_structured_reaction_equation_derived_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    row = _row("01", point_title="氧化还原观察", snippet="观察实验现象")
    row.update(
        {
            "principle_equation": "",
            "principle_text": "",
            "equation_search_text": "SO3^2- + Ba2+ → BaSO3↓",
            "equation_formulae": ["SO3^2-", "Ba2+", "BaSO3"],
            "equation_aliases": ["亚硫酸根", "亚硫酸钡"],
            "equation_reactants": ["SO3^2-", "Ba2+"],
            "equation_products": ["BaSO3"],
        }
    )
    _install_rows(monkeypatch, [row])

    response = home_feed_service.student_home_video_feed(object(), query="亚硫酸根 BaSO3", limit=12)

    assert [item.placement_node_id for item in response.items] == ["cat-point-01"]


def test_recommendations_sort_first_by_order_then_update_and_catalog_is_stable() -> None:
    rows = [
        _row("04", chapter_number=14),
        _row("03", recommended=True, recommended_order=1, recommended_updated_at="2026-07-20T09:00:00Z"),
        _row("01", recommended=True, recommended_order=0, recommended_updated_at="2026-07-20T08:00:00Z"),
        _row("02", recommended=True, recommended_order=1, recommended_updated_at="2026-07-20T10:00:00Z"),
        _row("05", chapter_number=13),
    ]

    ordered = home_feed_service._ordered_home_rows(rows)

    assert [row["placement_node_id"] for row in ordered] == [
        "cat-point-01",
        "cat-point-02",
        "cat-point-03",
        "cat-point-05",
        "cat-point-04",
    ]


def test_home_feed_is_finite_and_cursor_keeps_stable_instances(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_rows(monkeypatch, [_row("01"), _row("02"), _row("03")])

    first = home_feed_service.student_home_video_feed(object(), limit=2)
    second = home_feed_service.student_home_video_feed(object(), limit=2, cursor=first.next_cursor)

    assert first.has_more is True
    assert first.next_cursor
    assert len(first.items) == 2
    assert second.has_more is False
    assert second.next_cursor is None
    assert len(second.items) == 1
    assert {item.id for item in first.items}.isdisjoint({item.id for item in second.items})
    assert all(item.instance_id == item.id for item in [*first.items, *second.items])


def test_malformed_query_mismatched_and_stale_pool_cursors_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [_row("01"), _row("02"), _row("03")]
    _install_rows(monkeypatch, rows)

    first = home_feed_service.student_home_video_feed(object(), query="实验", limit=1)
    assert first.next_cursor

    with pytest.raises(Exception) as malformed:
        home_feed_service.student_home_video_feed(object(), query="实验", limit=1, cursor="not-a-cursor")
    with pytest.raises(Exception) as mismatched:
        home_feed_service.student_home_video_feed(object(), query="颜色", limit=1, cursor=first.next_cursor)

    rows.append(_row("04"))
    with pytest.raises(Exception) as stale:
        home_feed_service.student_home_video_feed(object(), query="实验", limit=1, cursor=first.next_cursor)

    assert malformed.value.status_code == 400
    assert mismatched.value.status_code == 400
    assert stale.value.status_code == 400


def test_favorite_feed_reuses_published_pool_and_sorts_by_saved_at_desc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [_row("01"), _row("02"), _row("03")]

    def states(_session: object, _user: object, _items: list[tuple[str, str]]) -> dict[str, StudentVideoPersonalState]:
        return {
            "cat-point-01:00000000-0000-0000-0000-000000000001": StudentVideoPersonalState(
                favorite=True,
                favorite_saved_at="2026-07-20T10:00:00Z",
            ),
            "cat-point-02:00000000-0000-0000-0000-000000000002": StudentVideoPersonalState(),
            "cat-point-03:00000000-0000-0000-0000-000000000003": StudentVideoPersonalState(
                favorite=True,
                favorite_saved_at="2026-07-20T11:00:00Z",
            ),
        }

    _install_rows(monkeypatch, rows)
    monkeypatch.setattr(home_feed_service, "personal_states_for_items", states)

    response = home_feed_service.student_saved_video_feed(object(), limit=10)

    assert response.query == ""
    assert response.has_more is False
    assert [item.placement_node_id for item in response.items] == ["cat-point-03", "cat-point-01"]
    assert all(item.personal_state.favorite for item in response.items)
