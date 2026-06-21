from __future__ import annotations

import json

from server.app.domains.video_library.index_client import forbidden_video_library_document_violations
from server.app.domains.video_library.search import LocalVideoLibrarySearchAdapter, _build_documents


def test_directory_category_text_matches_descendant_point_without_directory_documents() -> None:
    documents = _build_documents(
        [],
        profiles=[
            {
                "enabled": True,
                "profile_id": "halogens-17",
                "chapter_id": "CH17",
                "title": "Halogens",
                "family_name": "Halogens",
                "element_symbols": ["Cl", "Br"],
            }
        ],
        point_rows=[
            {
                "node_id": "cat-point-halogen",
                "placement_node_id": "cat-point-halogen",
                "canonical_point_id": "cat-canon-halogen",
                "chapter_id": "CH17",
                "chapter_title": "Halogen chapter",
                "node_title": "Orange layer observation",
                "point_title": "Orange layer observation",
                "principle_mode": "equation",
                "principle_equation": "Cl2 + 2Br- = 2Cl- + Br2",
                "principle_text": None,
                "phenomenon_explanation": "The organic layer turns orange.",
                "safety_note": "Use ventilation.",
                "catalog_path": ["Halogen displacement", "Oxidation experiments", "Orange layer observation"],
                "directory_context": [
                    {
                        "title": "Oxidation experiments",
                    }
                ],
                "related_links": [],
                "video_count": 1,
                "videos": [
                    {
                        "media_id": "media-1",
                        "title": "Bound ready video",
                        "original_file_name": "bound-ready-source.mp4",
                    }
                ],
                "content_updated_at": None,
            }
        ],
    )

    matches = LocalVideoLibrarySearchAdapter().search("oxidation experiments", documents, 10)
    video_title_matches = LocalVideoLibrarySearchAdapter().search("Bound ready video", documents, 10)

    assert [document.id for document in documents] == ["cat-point-halogen"]
    assert matches and matches[0].id == "cat-point-halogen"
    assert matches[0].result_type == "video_point"
    assert matches[0].target is not None
    assert matches[0].target.kind == "point_detail"
    assert matches[0].target.placement_node_id == "cat-point-halogen"
    assert matches[0].target.canonical_point_id == "cat-canon-halogen"
    assert matches[0].index_source is not None
    assert matches[0].index_source["placement_node_id"] == "cat-point-halogen"
    assert matches[0].index_source["canonical_point_id"] == "cat-canon-halogen"
    assert "Oxidation experiments" in matches[0].index_source["category_text"]
    assert matches[0].index_source["has_video"] is True
    assert matches[0].index_source["video_count"] == 1
    assert "videos" not in matches[0].index_source
    assert forbidden_video_library_document_violations(matches[0].index_source) == []
    assert "Bound ready video" not in matches[0].search_text
    assert "media-1" not in json.dumps(matches[0].index_source, ensure_ascii=False)
    assert "bound-ready-source.mp4" not in json.dumps(matches[0].index_source, ensure_ascii=False)
    assert video_title_matches == []
