from __future__ import annotations

import pytest
from uuid import UUID

from server.app.auth import AuthUser
from server.app.catalog_tree_schemas import StudentPointDetailResponse
from server.app.domains.catalog_tree import preview
from server.app.domains.catalog_tree.equations import normalize_reaction_equation
from server.app.domains.errors import DomainHTTPException
from server.app.security import create_access_token


class _SessionScope:
    def __enter__(self) -> object:
        return object()

    def __exit__(self, *_args: object) -> None:
        return None


class _NoMediaSession:
    def execute(self, *_args: object, **_kwargs: object) -> "_NoMediaSession":
        return self

    def first(self) -> object | None:
        return None


class _NoMediaSessionScope:
    def __enter__(self) -> _NoMediaSession:
        return _NoMediaSession()

    def __exit__(self, *_args: object) -> None:
        return None


class _MediaRowSession:
    def execute(self, *_args: object, **_kwargs: object) -> "_MediaRowSession":
        return self

    def first(self) -> tuple[str] | None:
        return ("cat-point-a",)


class _MediaRowSessionScope:
    def __enter__(self) -> _MediaRowSession:
        return _MediaRowSession()

    def __exit__(self, *_args: object) -> None:
        return None


def _teacher_user() -> AuthUser:
    return AuthUser(
        id="00000000-0000-0000-0000-000000000001",
        username="teacher",
        role="teacher",
        display_name="Teacher",
        status="active",
        password_version=3,
    )


def _teacher_identity() -> preview.PreviewTeacherIdentity:
    user = _teacher_user()
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "password_version": user.password_version,
    }


def _preview_token(node_id: str, node_kind: str = "point") -> str:
    token, _claims = create_access_token(
        subject="00000000-0000-0000-0000-000000000001",
        role="catalog_preview",
        username="teacher",
        display_name="Teacher",
        password_version=3,
        expires_minutes=15,
        extra_claims={
            "purpose": preview.PREVIEW_PURPOSE,
            "node_id": node_id,
            "root_node_id": node_id,
            "node_kind": node_kind,
            "teacher_user_id": "teacher-1",
        },
    )
    return token


def _expired_preview_token(node_id: str) -> str:
    token, _claims = create_access_token(
        subject="00000000-0000-0000-0000-000000000001",
        role="catalog_preview",
        username="teacher",
        display_name="Teacher",
        password_version=3,
        expires_minutes=-1,
        extra_claims={"purpose": preview.PREVIEW_PURPOSE, "node_id": node_id, "teacher_user_id": "teacher-1"},
    )
    return token


def test_preview_token_is_scoped_to_one_catalog_point(monkeypatch: pytest.MonkeyPatch) -> None:
    include_archived_values: list[bool] = []
    monkeypatch.setattr(preview, "db_session", lambda: _SessionScope())
    monkeypatch.setattr(
        preview,
        "get_node",
        lambda _session, node_id, include_archived=False: include_archived_values.append(include_archived)
        or {
            "node_id": node_id,
            "id": node_id,
            "node_kind": "point",
            "status": "draft",
            "canonical_point_status": "draft",
        },
    )

    response = preview.create_catalog_point_preview_token(node_id="cat-point-a", teacher=_teacher_identity())

    assert include_archived_values == [True]
    assert response["preview_url"].startswith("/preview/catalog/points/cat-point-a?preview_token=")
    claims = preview.decode_catalog_preview_token(response["token"], node_id="cat-point-a")
    assert claims["purpose"] == preview.PREVIEW_PURPOSE
    assert claims["role"] == "catalog_preview"
    assert claims["node_id"] == "cat-point-a"
    assert claims["root_node_id"] == "cat-point-a"
    assert claims["node_kind"] == "point"
    with pytest.raises(DomainHTTPException) as exc:
        preview.decode_catalog_preview_token(response["token"], node_id="cat-point-b")
    assert exc.value.status_code == 403


def test_preview_token_can_scope_to_catalog_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    include_archived_values: list[bool] = []
    monkeypatch.setattr(preview, "db_session", lambda: _SessionScope())
    monkeypatch.setattr(
        preview,
        "get_node",
        lambda _session, node_id, include_archived=False: include_archived_values.append(include_archived)
        or {
            "node_id": node_id,
            "id": node_id,
            "node_kind": "directory",
            "chapter_id": "CH17",
            "title": "Halogen directory",
            "status": "draft",
        },
    )

    response = preview.create_catalog_node_preview_token(node_id="cat-dir-a", teacher=_teacher_identity())

    assert include_archived_values == [True]
    assert response["preview_url"].startswith("/preview/catalog/nodes/cat-dir-a?preview_token=")
    claims = preview.decode_catalog_preview_token(response["token"], node_id="cat-dir-a")
    assert claims["root_node_id"] == "cat-dir-a"
    assert claims["node_kind"] == "directory"


def test_preview_catalog_node_returns_directory_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _preview_token("cat-dir-a", "directory")
    monkeypatch.setattr(preview, "db_session", lambda: _SessionScope())
    monkeypatch.setattr(
        preview,
        "get_node",
        lambda _session, node_id, include_archived=False: {
            "node_id": node_id,
            "id": node_id,
            "node_kind": "directory",
            "chapter_id": "CH17",
            "parent_id": None,
            "title": "Halogen directory",
            "summary": "Preview this directory",
            "status": "draft",
            "display_order": 1,
            "has_children": True,
            "descendant_point_count": 1,
            "has_point_content": False,
            "media_count": 0,
            "published_media_count": 0,
        },
    )
    monkeypatch.setattr(
        preview,
        "breadcrumbs",
        lambda _session, _node_id: [{"node_id": "cat-dir-a", "title": "Halogen directory", "node_kind": "directory", "chapter_id": "CH17"}],
    )
    monkeypatch.setattr(
        preview,
        "_preview_children",
        lambda _session, parent_id: [
            {
                "node_id": "cat-point-a",
                "chapter_id": "CH17",
                "parent_id": parent_id,
                "node_kind": "point",
                "title": "Child point",
                "summary": "",
                "status": "draft",
                "display_order": 1,
                "actions": ["open_point"],
                "has_children": False,
                "has_point_content": True,
                "media_count": 0,
                "published_media_count": 0,
            }
        ],
    )
    monkeypatch.setattr(
        preview,
        "get_student_learning_page_by_chapter",
        lambda *, chapter_id: {
            "recommended_profile_id": "halogens-17",
            "profiles": [],
            "active_profile": {"profile_id": "halogens-17", "chapter_id": chapter_id},
        },
    )

    payload = preview.preview_catalog_node(node_id="cat-dir-a", preview_token=token)

    assert payload["node_kind"] == "directory"
    assert payload["directory"]["node"]["title"] == "Halogen directory"
    assert payload["directory"]["children"][0]["node_id"] == "cat-point-a"
    assert payload["learning_page"]["active_profile"]["profile_id"] == "halogens-17"
    assert payload["point"] is None


def test_directory_preview_scope_rejects_sibling_node(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _preview_token("cat-dir-a", "directory")
    monkeypatch.setattr(preview, "db_session", lambda: _NoMediaSessionScope())

    with pytest.raises(DomainHTTPException) as exc:
        preview.preview_catalog_node(node_id="cat-point-outside", preview_token=token)

    assert exc.value.status_code == 403


def test_preview_token_rejects_expired_tokens() -> None:
    with pytest.raises(DomainHTTPException) as exc:
        preview.decode_catalog_preview_token(_expired_preview_token("cat-point-a"), node_id="cat-point-a")
    assert exc.value.status_code == 401


def test_preview_point_detail_uses_draft_content_without_student_session(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _preview_token("cat-point-a")
    monkeypatch.setattr(preview, "db_session", lambda: _SessionScope())
    monkeypatch.setattr(
        preview,
        "get_node",
        lambda _session, node_id, include_archived=False: {
            "node_id": node_id,
            "id": node_id,
            "node_kind": "point",
            "chapter_id": "CH13",
            "title": "Tree title",
            "summary": "",
            "status": "draft",
            "canonical_point_id": "cat-canon-a",
            "canonical_point_status": "draft",
        },
    )
    monkeypatch.setattr(
        preview,
        "get_content",
        lambda _session, _node_id: {
            "content_status": "draft",
            "point_title": "Draft point title",
            "principle_mode": "text",
            "principle_text": "Draft principle",
            "phenomenon_explanation": "Draft phenomenon",
            "safety_note": "Draft safety",
            "teacher_note": "teacher-only",
        },
    )
    monkeypatch.setattr(
        preview,
        "breadcrumbs",
        lambda _session, _node_id: [{"node_id": "cat-point-a", "title": "Draft point title", "node_kind": "point", "chapter_id": "CH13"}],
    )
    monkeypatch.setattr(
        preview,
        "_preview_videos",
        lambda _session, _node_id, scoped_token: [
            {
                "media_id": "media-a",
                "title": "Preview video",
                "mime_type": "video/mp4",
                "stream_path": f"/api/preview/media/assets/media-a/stream?preview_token={scoped_token}",
                "thumbnail_path": None,
            }
        ],
    )
    monkeypatch.setattr(
        preview,
        "related_links",
        lambda _session, _node_id, include_hidden=False, include_defaults=True: [
            {
                "target_node_id": "cat-point-b",
                "target_placement_node_id": "cat-point-b",
                "target_canonical_point_id": "cat-canon-b",
                "target_title": "Neighbor",
                "relation_type": "generated_default",
                "hidden": False,
            }
        ],
    )

    detail = preview.preview_point_detail(node_id="cat-point-a", preview_token=token)

    assert detail["title"] == "Draft point title"
    assert detail["principle_text"] == "Draft principle"
    assert detail["has_video"] is True
    assert detail["videos"][0]["stream_path"].endswith(f"preview_token={token}")
    assert detail["related_points"][0]["title"] == "Neighbor"
    assert detail["assessment_context"]["point_node_id"] == "cat-point-a"
    assert "teacher_note" not in detail


def test_preview_point_detail_allows_archived_placement_when_shared_point_is_available(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _preview_token("cat-point-a")
    include_archived_values: list[bool] = []
    monkeypatch.setattr(preview, "db_session", lambda: _SessionScope())
    monkeypatch.setattr(
        preview,
        "get_node",
        lambda _session, node_id, include_archived=False: include_archived_values.append(include_archived)
        or {
            "node_id": node_id,
            "id": node_id,
            "node_kind": "point",
            "chapter_id": "CH13",
            "title": "Archived placement title",
            "summary": "",
            "status": "archived",
            "canonical_point_id": "cat-canon-a",
            "canonical_point_status": "published",
        },
    )
    monkeypatch.setattr(
        preview,
        "get_content",
        lambda _session, _node_id: {
            "content_status": "published",
            "point_title": "Previewable archived placement",
            "principle_mode": "text",
            "principle_text": "Preview principle",
            "phenomenon_explanation": "Preview phenomenon",
            "safety_note": "Preview safety",
        },
    )
    monkeypatch.setattr(
        preview,
        "breadcrumbs",
        lambda _session, _node_id: [{"node_id": "cat-point-a", "title": "Previewable archived placement", "node_kind": "point", "chapter_id": "CH13"}],
    )
    monkeypatch.setattr(preview, "_preview_videos", lambda _session, _node_id, scoped_token: [])
    monkeypatch.setattr(preview, "related_links", lambda *_args, **_kwargs: [])

    detail = preview.preview_point_detail(node_id="cat-point-a", preview_token=token)

    assert include_archived_values == [True]
    assert detail["title"] == "Previewable archived placement"


def test_preview_point_detail_serializes_reaction_equation_ids_for_student_response(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _preview_token("cat-point-a")
    equation_id = UUID("25f9754b-66a3-41cc-96de-34b39b9320f6")
    normalized_equation = normalize_reaction_equation(
        {
            "id": equation_id,
            "node_id": "cat-point-a",
            "canonical_point_id": "cat-canon-a",
            "row_order": 1,
            "raw_text": "Cl2 + 2I- -> 2Cl- + I2",
        },
        row_order=1,
    )
    monkeypatch.setattr(preview, "db_session", lambda: _SessionScope())
    monkeypatch.setattr(
        preview,
        "get_node",
        lambda _session, node_id, include_archived=False: {
            "node_id": node_id,
            "id": node_id,
            "node_kind": "point",
            "chapter_id": "CH13",
            "title": "Equation point",
            "summary": "",
            "status": "published",
            "canonical_point_id": "cat-canon-a",
            "canonical_point_status": "published",
        },
    )
    monkeypatch.setattr(
        preview,
        "get_content",
        lambda _session, _node_id: {
            "content_status": "published",
            "point_title": "Equation point",
            "principle_mode": "equation",
            "principle_equation": "Cl2 + 2I- -> 2Cl- + I2",
            "reaction_equations": [normalized_equation],
            "phenomenon_explanation": "Layer color changes.",
            "safety_note": "Handle chlorine water in hood.",
        },
    )
    monkeypatch.setattr(
        preview,
        "breadcrumbs",
        lambda _session, _node_id: [{"node_id": "cat-point-a", "title": "Equation point", "node_kind": "point", "chapter_id": "CH13"}],
    )
    monkeypatch.setattr(preview, "_preview_videos", lambda _session, _node_id, scoped_token: [])
    monkeypatch.setattr(preview, "related_links", lambda *_args, **_kwargs: [])

    detail = preview.preview_point_detail(node_id="cat-point-a", preview_token=token)
    response = StudentPointDetailResponse(**detail)

    assert detail["reaction_equations"][0]["id"] == str(equation_id)
    assert response.reaction_equations[0].id == str(equation_id)


def test_preview_media_scope_rejects_unbound_media(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preview, "db_session", lambda: _NoMediaSessionScope())

    with pytest.raises(DomainHTTPException) as exc:
        preview.assert_preview_media_scope(asset_id="00000000-0000-0000-0000-000000000099", preview_token=_preview_token("cat-point-a"))

    assert exc.value.status_code == 404


def test_directory_preview_media_scope_returns_bound_descendant_point(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preview, "db_session", lambda: _MediaRowSessionScope())

    node_id = preview.assert_preview_media_scope(
        asset_id="00000000-0000-0000-0000-000000000001",
        preview_token=_preview_token("cat-dir-a", "directory"),
    )

    assert node_id == "cat-point-a"
