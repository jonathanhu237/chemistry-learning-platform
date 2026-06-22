from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
import json
import urllib.error

import pytest
from fastapi import HTTPException

from server.app.auth import AuthUser
from server.app.infrastructure.settings import Settings
from server.app.api.student import student_video_library
from server.app.domains.video_library.index_client import (
    ANALYZER_ASSET_ROOT,
    VideoLibraryIndexClient,
    document_hash,
    forbidden_video_library_document_violations,
    video_library_analyzer_assets,
    video_library_index_mapping,
)
from server.app.domains.video_library import search as student_video_library_service
from server.app.domains.video_library.search import (
    ElasticsearchVideoLibrarySearchAdapter,
    LocalVideoLibrarySearchAdapter,
    _build_documents,
    _build_elasticsearch_search_payload,
    _source_route_matches,
    search_student_video_library,
)
from server.tests.route_helpers import assert_route


def _student_user() -> AuthUser:
    return AuthUser(
        id="student-video-library-user",
        username="20240002",
        role="student",
        display_name="Student",
        status="active",
        must_change_password=False,
        student_id="20240002",
        class_id="class-video",
    )


def _experiment(
    experiment_id: str,
    *,
    title: str,
    status: str = "published",
    chapter_id: str = "CH13",
    archived: bool = False,
    media_status: str = "published",
) -> dict[str, Any]:
    return {
        "id": experiment_id,
        "code": experiment_id.replace("EXP_", ""),
        "title": title,
        "summary": f"{title} summary",
        "status": status,
        "display_order": 1,
        "metadata": {
            "parent_code": "19-1",
            "parent_title": "Experiment 19-1",
            "module_display_title": "Chlorine water observation",
            "video_candidates": ["orange CCl4 layer"],
            "archived_by_catalog_seed": "true" if archived else "false",
        },
        "chapter_bindings": [{"chapter_id": chapter_id, "chapter_title": "Halogens", "coverage_type": "primary", "sort_order": 1}],
        "media_resources": [
            {
                "media_id": f"media-{experiment_id}",
                "title": "CCl4 orange layer video",
                "point_title": "Orange layer observation",
                "upload_status": "ready",
                "binding_status": media_status,
                "has_thumbnail": False,
            }
        ],
        "published_question_count": 2,
    }


def _profiles() -> list[dict[str, Any]]:
    return [
        {
            "enabled": True,
            "profile_id": "halogens-17",
            "chapter_id": "CH13",
            "title": "Halogens",
            "subtitle": "Halogen displacement",
            "family_name": "Group 17",
            "element_symbols": ["Cl", "Br", "I"],
            "default_element_symbol": "Cl",
            "property_sections": [
                {
                    "key": "oxidation",
                    "title": "Oxidation",
                    "formula": "Cl2 + 2Br- -> 2Cl- + Br2",
                    "experiment_keywords": ["chlorine", "orange"],
                }
            ],
        }
    ]


def _point_row(
    experiment: dict[str, Any],
    *,
    node_id: str = "cat-point-orange-layer",
    point_title: str = "Orange layer observation",
    principle_mode: str = "equation",
    principle_equation: str = "Cl2 + 2 KBr = 2 KCl + Br2",
    principle_text: str = "",
    phenomenon_explanation: str = "Chlorine water turns the CCl4 layer orange by producing bromine.",
    safety_note: str = "Handle chlorine water in a ventilated space.",
    videos: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    video_resources = videos if videos is not None else experiment["media_resources"]
    return {
        "node_id": node_id,
        "chapter_id": "CH13",
        "chapter_title": "Halogens",
        "node_title": point_title,
        "catalog_path": ["Halogens", experiment["title"], point_title],
        "code": experiment["code"],
        "experiment_title": experiment["title"],
        "summary": experiment["summary"],
        "experiment_status": experiment["status"],
        "display_order": experiment["display_order"],
        "experiment_metadata": experiment["metadata"],
        "chapter_bindings": experiment["chapter_bindings"],
        "point_title": point_title,
        "point_order": 1,
        "principle_mode": principle_mode,
        "principle_equation": principle_equation,
        "principle_text": principle_text,
        "phenomenon_explanation": phenomenon_explanation,
        "safety_note": safety_note,
        "teacher_note": "Teacher-only note must never be indexed or shown to students.",
        "content_updated_at": "2026-06-19T00:00:00Z",
        "video_count": 1 if video_resources else 0,
        "videos": video_resources,
        "related_links": [{"node_id": "cat-point-related", "title": "Related published point"}],
    }


@contextmanager
def _fake_session():
    yield object()


def test_student_video_library_route_is_registered() -> None:
    assert_route("/api/student/video-library/search", "GET")


def test_video_library_rejects_non_experiment_video_domain() -> None:
    with pytest.raises(HTTPException) as exc_info:
        student_video_library.video_library_search(_student_user(), q="admin", domain="admin")

    assert exc_info.value.status_code == 400


def test_video_library_documents_only_include_student_visible_material() -> None:
    visible = _experiment("EXP_VISIBLE", title="Visible chlorine displacement")
    documents = _build_documents(
        [
            visible,
            _experiment("EXP_DRAFT", title="Draft teacher-only experiment", status="draft"),
            _experiment("EXP_ARCHIVED", title="Archived experiment", archived=True),
            _experiment("EXP_F_AREA", title="F area experiment", chapter_id="CH21"),
            _experiment("EXP_HIDDEN_MEDIA", title="Hidden media", media_status="draft"),
        ],
        _profiles(),
        point_rows=[_point_row(visible)],
    )

    search_text = "\n".join(document.search_text for document in documents)

    assert "Visible chlorine displacement" in search_text
    assert "Draft teacher-only experiment" not in search_text
    assert "Archived experiment" not in search_text
    assert "F area experiment" not in search_text
    assert "media-EXP_HIDDEN_MEDIA" not in search_text
    assert "Teacher-only note" not in search_text
    assert all(document.target for document in documents)


def test_video_library_point_documents_use_teacher_content_without_ai_evidence() -> None:
    experiment = _experiment("EXP_POINT", title="Sodium thiosulfate and acid")
    point_rows = [
        _point_row(
            experiment,
            point_title="Na2S2O3 and HCl reaction",
            principle_equation="Na2S2O3 + 2 HCl = 2 NaCl + SↁE+ SO2ↁE+ H2O",
            phenomenon_explanation="Teacher-authored sulfur precipitation and sulfur dioxide explanation.",
            safety_note="Teacher-authored SO2 safety note.",
            videos=[],
        )
    ]

    documents = _build_documents([experiment], _profiles(), point_rows=point_rows)

    assert len(documents) == 1
    document = documents[0]
    assert document.id == "cat-point-orange-layer"
    assert document.target and document.target.node_id == "cat-point-orange-layer"
    assert document.target.route == "/point/cat-point-orange-layer"
    assert document.target.catalog_path == ["Halogens", "Sodium thiosulfate and acid", "Na2S2O3 and HCl reaction"]
    assert "Teacher-authored sulfur precipitation" in document.search_text
    assert "Teacher-only note" not in document.search_text
    assert "source_chunks" not in document.search_text
    assert "experiment_video_point_evidence" not in document.search_text
    assert document.index_source
    assert document.index_source["id"] == "cat-point-orange-layer"
    assert document.index_source["node_id"] == "cat-point-orange-layer"
    assert document.index_source["has_video"] is False
    assert "NA2S2O3" in document.index_source["formulae"]
    assert document.index_source["title_formulae"]
    assert "title_formula_pairs" in document.index_source
    assert "NA2S2O3" in document.index_source["participants"]
    assert document.index_source["equation_formula_pairs"]
    assert document.index_source["equation_rows"]
    assert "strict_aliases" in document.index_source
    assert "phenomenon_tags" in document.index_source
    assert "gas_generation" in document.index_source["reaction_features"]
    assert "precipitation" in document.index_source["reaction_features"]


def test_video_library_documents_do_not_index_video_resource_semantics() -> None:
    experiment = _experiment("EXP_PRIVATE_VIDEO", title="Visible experiment")
    private_title = "Teacher internal deletion checklist title"
    private_filename = "teacher-only-original-filename.mp4"
    documents = _build_documents(
        [experiment],
        _profiles(),
        point_rows=[
            _point_row(
                experiment,
                point_title="Copper flame color observation",
                principle_text="Copper salts color a flame green.",
                principle_mode="text",
                phenomenon_explanation="The flame appears green.",
                videos=[
                    {
                        "media_id": "media-private-991",
                        "title": private_title,
                        "original_file_name": private_filename,
                        "thumbnail_relative_path": "thumbs/private.jpg",
                        "source_relative_path": "originals/private.mp4",
                        "playback_relative_path": "playback/private.mp4",
                    }
                ],
            )
        ],
    )

    assert len(documents) == 1
    document = documents[0]
    source = document.index_source or {}
    assert document.search_text
    assert source["has_video"] is True
    assert source["video_count"] == 1
    assert "videos" not in source
    assert forbidden_video_library_document_violations(source) == []
    for forbidden_text in [private_title, private_filename, "media-private-991", "private.mp4"]:
        assert forbidden_text not in document.search_text
        assert forbidden_text not in json.dumps(source, ensure_ascii=False)

    assert LocalVideoLibrarySearchAdapter().search(private_title, documents, 10) == []
    assert _source_route_matches(source, {"query_text": private_title, "normalized_query": private_title}) == []


def test_video_library_es_mapping_uses_chemistry_ik_stopwords_and_synonyms() -> None:
    mapping = video_library_index_mapping()
    analysis = mapping["settings"]["analysis"]
    properties = mapping["mappings"]["properties"]

    assert mapping["mappings"]["_meta"]["mapping_version"] == "chemistry-point-placement-v5"
    assert "videos" not in properties
    assert "media_id" not in properties
    assert "media_title" not in properties
    assert "original_file_name" not in properties
    assert analysis["analyzer"]["chemistry_ik"]["tokenizer"] == "ik_max_word"
    assert analysis["analyzer"]["chemistry_ik"]["filter"] == ["lowercase", "chemistry_stop"]
    assert analysis["analyzer"]["chemistry_ik_search"]["tokenizer"] == "ik_smart"
    assert analysis["analyzer"]["chemistry_ik_search"]["filter"] == ["lowercase", "chemistry_synonyms", "chemistry_stop"]
    assert analysis["filter"]["chemistry_stop"]["stopwords_path"] == "analysis/chemistry_stopwords.txt"
    assert analysis["filter"]["chemistry_synonyms"]["synonyms_path"] == "analysis/chemistry_synonyms.txt"

    for field in ["title", "search_text", "principle", "phenomenon_explanation", "safety_note", "related_text", "equation_rows"]:
        field_mapping = properties[field]
        assert field_mapping["analyzer"] == "chemistry_ik"
        assert field_mapping["search_analyzer"] == "chemistry_ik_search"

    for field in [
        "formulae",
        "title_formulae",
        "title_formula_pairs",
        "strict_aliases",
        "reactants",
        "products",
        "participants",
        "equation_formula_pairs",
        "condition_tags",
        "phenomenon_tags",
        "property_tags",
    ]:
        assert field in properties


def test_elasticsearch_query_payload_uses_formula_and_retrieval_routes() -> None:
    payload, plan = _build_elasticsearch_search_payload("H2O2 KMnO4 \u9178\u6027", limit=5)
    route_names = {route["name"] for route in plan["routes"]}
    payload_text = json.dumps(payload, ensure_ascii=False)

    assert {
        "title_formula_exact",
        "title_formula_pair",
        "equation_formula_pair",
        "formula_exact",
        "participants_exact",
        "strict_alias_exact",
        "equation_text",
        "condition_tags",
    }.issubset(route_names)
    assert "h2o2" in payload_text
    assert "kmno4" in payload_text
    assert "formula_exact" in payload_text
    assert "title_formula_pair" in payload_text
    assert "equation_formula_pair" in payload_text
    assert "participants_exact" in payload_text


def test_video_library_index_client_serializes_datetime_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class _Response:
        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"result":"updated"}'

    def fake_urlopen(request: Any, timeout: float) -> _Response:
        captured["timeout"] = timeout
        captured["data"] = request.data.decode("utf-8")
        return _Response()

    payload = {
        "id": "cat-point-1",
        "node_id": "cat-point-1",
        "updated_at": datetime(2026, 6, 21, 3, 16, tzinfo=timezone.utc),
    }

    monkeypatch.setattr("server.app.domains.video_library.index_client.urllib.request.urlopen", fake_urlopen)

    client = VideoLibraryIndexClient(base_url="http://search:9200", index="student-video-library", timeout=1.5)
    client.upsert_document(payload)

    assert document_hash(payload)
    assert captured["timeout"] == 1.5
    assert '"updated_at": "2026-06-21T03:16:00+00:00"' in captured["data"]


def test_es_ik_analyzer_assets_cover_required_chemistry_smoke_terms() -> None:
    assets = video_library_analyzer_assets()
    asset_ids = {item["id"] for item in assets["files"]}

    assert assets["ok"] is True
    assert {"hit_stopwords", "project_chemistry_stopwords", "chemistry_custom", "es_stopwords", "chemistry_synonyms"}.issubset(asset_ids)
    assert "的" in (ANALYZER_ASSET_ROOT / "analysis-ik" / "custom" / "hit_stopwords.dic").read_text(encoding="utf-8")
    assert "点位" in (ANALYZER_ASSET_ROOT / "analysis-ik" / "custom" / "project_chemistry_stopwords.dic").read_text(encoding="utf-8")
    assert "硫代硫酸钠" in (ANALYZER_ASSET_ROOT / "analysis-ik" / "custom" / "chemistry_custom.dic").read_text(encoding="utf-8")
    assert "HCl, 盐酸, 氯化氢, hydrochloric acid" in (ANALYZER_ASSET_ROOT / "analysis" / "chemistry_synonyms.txt").read_text(encoding="utf-8")


def test_video_library_local_search_returns_grouped_actionable_results(monkeypatch: pytest.MonkeyPatch) -> None:
    experiment = _experiment("EXP_VISIBLE", title="Visible chlorine displacement")
    monkeypatch.setattr(student_video_library_service, "db_session", _fake_session)
    monkeypatch.setattr(student_video_library_service, "_load_published_point_rows", lambda _session: [_point_row(experiment)])
    monkeypatch.setattr(student_video_library_service, "_learning_profiles", _profiles)
    monkeypatch.setattr(student_video_library_service, "get_settings", lambda: Settings(video_library_search_backend="local"))

    response = search_student_video_library(_student_user(), query="orange", limit=10)

    assert response.status == "ok"
    assert response.backend == "local"
    assert response.total >= 1
    assert response.groups
    assert all(item.target for group in response.groups for item in group.items)
    assert any(item.target and item.target.kind == "point_detail" for group in response.groups for item in group.items)
    assert any(
        item.target and item.target.node_id == "cat-point-orange-layer"
        for group in response.groups
        for item in group.items
        if item.type == "video_point"
    )


def test_video_library_disabled_search_returns_controlled_state(monkeypatch: pytest.MonkeyPatch) -> None:
    experiment = _experiment("EXP_VISIBLE", title="Visible chlorine displacement")
    monkeypatch.setattr(student_video_library_service, "db_session", _fake_session)
    monkeypatch.setattr(student_video_library_service, "_load_published_point_rows", lambda _session: [_point_row(experiment)])
    monkeypatch.setattr(student_video_library_service, "_learning_profiles", _profiles)
    monkeypatch.setattr(
        student_video_library_service,
        "get_settings",
        lambda: Settings(video_library_search_enabled=False),
    )

    response = search_student_video_library(_student_user(), query="orange", limit=10)

    assert response.status == "disabled"
    assert response.backend == "disabled"
    assert response.groups == []
    assert response.browse.recommended


def test_elasticsearch_adapter_returns_only_known_typed_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    experiment = _experiment("EXP_VISIBLE", title="Visible chlorine displacement")
    documents = _build_documents([experiment], _profiles(), point_rows=[_point_row(experiment)])
    known_id = documents[0].id

    class _Response:
        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return (
                b'{"hits":{"hits":[{"_source":{"id":"'
                + known_id.encode("utf-8")
                + b'"}},{"_source":{"id":"missing"}}]}}'
            )

    monkeypatch.setattr(student_video_library_service.urllib.request, "urlopen", lambda *_args, **_kwargs: _Response())

    adapter = ElasticsearchVideoLibrarySearchAdapter(base_url="http://search:9200", index="student-video-library", timeout=1)
    results = adapter.search("orange", documents, limit=10)

    assert [item.id for item in results] == [known_id]


def test_elasticsearch_failure_without_local_fallback_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    experiment = _experiment("EXP_VISIBLE", title="Visible chlorine displacement")
    monkeypatch.setattr(student_video_library_service, "db_session", _fake_session)
    monkeypatch.setattr(student_video_library_service, "_load_published_point_rows", lambda _session: [_point_row(experiment)])
    monkeypatch.setattr(student_video_library_service, "_learning_profiles", _profiles)
    monkeypatch.setattr(
        student_video_library_service,
        "get_settings",
        lambda: Settings(
            video_library_search_backend="elasticsearch",
            video_library_search_url="http://search:9200",
            video_library_search_local_fallback=False,
        ),
    )
    monkeypatch.setattr(
        ElasticsearchVideoLibrarySearchAdapter,
        "search",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(urllib.error.URLError("search down")),
    )

    response = search_student_video_library(_student_user(), query="orange", limit=10)

    assert response.status == "error"
    assert response.backend == "elasticsearch"
    assert response.groups == []
