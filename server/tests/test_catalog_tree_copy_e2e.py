from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from server.app.app_runtime.main import app
from server.app.auth import AuthUser, get_current_user
from server.app.infrastructure.database import get_session_factory


@dataclass(frozen=True)
class CatalogCopyE2EFixture:
    client: TestClient
    test_id: str
    chapter_id: str
    user_id: str
    source_dir_id: str
    child_dir_id: str
    target_dir_id: str
    source_point_id: str
    canonical_point_id: str


def _test_user(user_id: str, test_id: str) -> AuthUser:
    return AuthUser(
        id=user_id,
        username=f"{test_id}-teacher",
        role="teacher",
        display_name="Catalog Copy E2E Teacher",
        status="active",
        must_change_password=False,
    )


def _cleanup_catalog_copy_fixture(test_id: str, chapter_id: str, user_id: str) -> None:
    session = get_session_factory()()
    try:
        session.execute(text("DELETE FROM chapters WHERE id = :chapter_id"), {"chapter_id": chapter_id})
        session.execute(
            text("DELETE FROM experiment_catalog_points WHERE metadata->>'e2e_test_id' = :test_id"),
            {"test_id": test_id},
        )
        session.execute(text("DELETE FROM app_users WHERE id = CAST(:user_id AS uuid)"), {"user_id": user_id})
        session.commit()
    finally:
        session.close()


def _insert_catalog_copy_fixture(test_id: str) -> tuple[str, str, str, str, str, str, str]:
    session = get_session_factory()()
    user_id = str(uuid4())
    chapter_id = f"E2E_COPY_{test_id}"
    canonical_point_id = f"{test_id}-canonical-a"
    source_dir_id = f"{test_id}-source-dir"
    child_dir_id = f"{test_id}-child-dir"
    target_dir_id = f"{test_id}-target-dir"
    source_point_id = f"{test_id}-source-point"
    metadata = {"e2e_test_id": test_id}
    try:
        session.execute(text("SELECT 1"))
        session.execute(
            text(
                """
                INSERT INTO app_users (id, username, role, display_name, password_hash, status, metadata)
                VALUES (CAST(:user_id AS uuid), :username, 'teacher', 'Catalog Copy E2E Teacher', 'test-only', 'active', CAST(:metadata AS jsonb))
                """
            ),
            {"user_id": user_id, "username": f"{test_id}-teacher", "metadata": '{"e2e_test_id": "%s"}' % test_id},
        )
        session.execute(
            text(
                """
                INSERT INTO chapters (id, chapter_number, chapter_title)
                VALUES (:chapter_id, 99001, :chapter_title)
                """
            ),
            {"chapter_id": chapter_id, "chapter_title": f"E2E Copy Chapter {test_id}"},
        )
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_points (id, title, summary, status, metadata, created_by, updated_by)
                VALUES (:canonical_point_id, 'E2E Canonical Point', '', 'draft', CAST(:metadata AS jsonb), CAST(:user_id AS uuid), CAST(:user_id AS uuid))
                """
            ),
            {"canonical_point_id": canonical_point_id, "metadata": '{"e2e_test_id": "%s"}' % test_id, "user_id": user_id},
        )
        node_rows = [
            (source_dir_id, None, "directory", "Source Directory", 1, None),
            (target_dir_id, None, "directory", "Target Directory", 2, None),
            (child_dir_id, source_dir_id, "directory", "Child Directory", 1, None),
            (source_point_id, source_dir_id, "point", "Source Point", 2, canonical_point_id),
        ]
        for node_id, parent_id, kind, title, display_order, canonical_id in node_rows:
            session.execute(
                text(
                    """
                    INSERT INTO experiment_catalog_nodes (
                      id, chapter_id, parent_id, node_kind, title, summary, status, display_order,
                      canonical_point_id, metadata, created_by, updated_by
                    )
                    VALUES (
                      :node_id, :chapter_id, :parent_id, :node_kind, :title, '', 'draft', :display_order,
                      :canonical_point_id, CAST(:metadata AS jsonb), CAST(:user_id AS uuid), CAST(:user_id AS uuid)
                    )
                    """
                ),
                {
                    "node_id": node_id,
                    "chapter_id": chapter_id,
                    "parent_id": parent_id,
                    "node_kind": kind,
                    "title": title,
                    "display_order": display_order,
                    "canonical_point_id": canonical_id,
                    "metadata": '{"e2e_test_id": "%s"}' % test_id,
                    "user_id": user_id,
                },
            )
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_content (
                  node_id, canonical_point_id, point_title, teacher_note, principle_mode, principle_text,
                  phenomenon_explanation, safety_note, content_status, created_by, updated_by, metadata
                )
                VALUES (
                  :node_id, :canonical_point_id, 'Source Point', '', 'text', 'E2E principle',
                  'E2E phenomenon', 'E2E safety', 'draft', CAST(:user_id AS uuid), CAST(:user_id AS uuid), CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "node_id": source_point_id,
                "canonical_point_id": canonical_point_id,
                "user_id": user_id,
                "metadata": '{"e2e_test_id": "%s"}' % test_id,
            },
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        session.close()
        _cleanup_catalog_copy_fixture(test_id, chapter_id, user_id)
        pytest.skip(f"catalog copy e2e requires a migrated test database: {exc.__class__.__name__}")
    finally:
        if session.is_active:
            session.close()
    return user_id, chapter_id, source_dir_id, child_dir_id, target_dir_id, source_point_id, canonical_point_id


@pytest.fixture()
def catalog_copy_e2e() -> CatalogCopyE2EFixture:
    test_id = f"e2e-copy-{uuid4().hex[:12]}"
    user_id, chapter_id, source_dir_id, child_dir_id, target_dir_id, source_point_id, canonical_point_id = _insert_catalog_copy_fixture(test_id)
    app.dependency_overrides[get_current_user] = lambda: _test_user(user_id, test_id)
    try:
        with TestClient(app) as client:
            yield CatalogCopyE2EFixture(
                client=client,
                test_id=test_id,
                chapter_id=chapter_id,
                user_id=user_id,
                source_dir_id=source_dir_id,
                child_dir_id=child_dir_id,
                target_dir_id=target_dir_id,
                source_point_id=source_point_id,
                canonical_point_id=canonical_point_id,
            )
    finally:
        app.dependency_overrides.clear()
        _cleanup_catalog_copy_fixture(test_id, chapter_id, user_id)


def _node_count(chapter_id: str) -> int:
    session = get_session_factory()()
    try:
        return int(session.execute(text("SELECT COUNT(*) FROM experiment_catalog_nodes WHERE chapter_id = :chapter_id"), {"chapter_id": chapter_id}).scalar_one())
    finally:
        session.close()


def _canonical_count(test_id: str) -> int:
    session = get_session_factory()()
    try:
        return int(
            session.execute(
                text("SELECT COUNT(*) FROM experiment_catalog_points WHERE metadata->>'e2e_test_id' = :test_id"),
                {"test_id": test_id},
            ).scalar_one()
        )
    finally:
        session.close()


def _sibling_orders(parent_id: str) -> list[tuple[str, int]]:
    session = get_session_factory()()
    try:
        rows = session.execute(
            text(
                """
                SELECT id, display_order
                FROM experiment_catalog_nodes
                WHERE parent_id = :parent_id AND status <> 'archived'
                ORDER BY id
                """
            ),
            {"parent_id": parent_id},
        ).all()
        return [(str(row[0]), int(row[1])) for row in rows]
    finally:
        session.close()


def _content_rows_for_node(node_id: str) -> int:
    session = get_session_factory()()
    try:
        return int(
            session.execute(
                text("SELECT COUNT(*) FROM experiment_catalog_point_content WHERE node_id = :node_id"),
                {"node_id": node_id},
            ).scalar_one()
        )
    finally:
        session.close()


def _content_rows_for_canonical(canonical_point_id: str) -> int:
    session = get_session_factory()()
    try:
        return int(
            session.execute(
                text("SELECT COUNT(*) FROM experiment_catalog_point_content WHERE canonical_point_id = :canonical_point_id"),
                {"canonical_point_id": canonical_point_id},
            ).scalar_one()
        )
    finally:
        session.close()


def _copied_point_from_source(*, copied_parent_id: str, source_node_id: str) -> dict[str, object]:
    session = get_session_factory()()
    try:
        row = session.execute(
            text(
                """
                SELECT id, parent_id, canonical_point_id, metadata
                FROM experiment_catalog_nodes
                WHERE parent_id = :copied_parent_id
                  AND node_kind = 'point'
                  AND metadata->>'copied_from_node_id' = :source_node_id
                LIMIT 1
                """
            ),
            {"copied_parent_id": copied_parent_id, "source_node_id": source_node_id},
        ).mappings().one()
        return dict(row)
    finally:
        session.close()


def _node_row(node_id: str) -> dict[str, object]:
    session = get_session_factory()()
    try:
        row = session.execute(
            text(
                """
                SELECT id, parent_id, canonical_point_id, metadata
                FROM experiment_catalog_nodes
                WHERE id = :node_id
                """
            ),
            {"node_id": node_id},
        ).mappings().one()
        return dict(row)
    finally:
        session.close()


def test_copy_directory_to_itself_is_rejected_and_creates_no_nodes(catalog_copy_e2e: CatalogCopyE2EFixture) -> None:
    before_nodes = _node_count(catalog_copy_e2e.chapter_id)
    before_canonicals = _canonical_count(catalog_copy_e2e.test_id)

    response = catalog_copy_e2e.client.post(
        f"/api/admin/catalog/nodes/{catalog_copy_e2e.source_dir_id}/copy",
        json={"parent_id": catalog_copy_e2e.source_dir_id, "title": "Should Not Exist"},
    )

    assert response.status_code == 400
    assert "Directory cannot be copied into itself or its descendants" in response.json()["detail"]
    assert _node_count(catalog_copy_e2e.chapter_id) == before_nodes
    assert _canonical_count(catalog_copy_e2e.test_id) == before_canonicals


def test_copy_directory_to_own_descendant_is_rejected_and_creates_no_nodes(catalog_copy_e2e: CatalogCopyE2EFixture) -> None:
    before_nodes = _node_count(catalog_copy_e2e.chapter_id)
    before_canonicals = _canonical_count(catalog_copy_e2e.test_id)

    response = catalog_copy_e2e.client.post(
        f"/api/admin/catalog/nodes/{catalog_copy_e2e.source_dir_id}/copy",
        json={"parent_id": catalog_copy_e2e.child_dir_id, "title": "Should Not Exist"},
    )

    assert response.status_code == 400
    assert "Directory cannot be copied into itself or its descendants" in response.json()["detail"]
    assert _node_count(catalog_copy_e2e.chapter_id) == before_nodes
    assert _canonical_count(catalog_copy_e2e.test_id) == before_canonicals


def test_reference_point_to_same_directory_rejects_duplicate_canonical_and_rolls_back_order_shift(catalog_copy_e2e: CatalogCopyE2EFixture) -> None:
    before_nodes = _node_count(catalog_copy_e2e.chapter_id)
    before_canonicals = _canonical_count(catalog_copy_e2e.test_id)
    before_orders = _sibling_orders(catalog_copy_e2e.source_dir_id)

    response = catalog_copy_e2e.client.post(
        f"/api/admin/catalog/nodes/{catalog_copy_e2e.source_point_id}/copy",
        json={"parent_id": catalog_copy_e2e.source_dir_id, "title": "Duplicate Reference"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "目标目录已包含同一实验点位，请选择其他目录"
    assert _node_count(catalog_copy_e2e.chapter_id) == before_nodes
    assert _canonical_count(catalog_copy_e2e.test_id) == before_canonicals
    assert _sibling_orders(catalog_copy_e2e.source_dir_id) == before_orders


def test_reference_point_to_different_directory_reuses_canonical_without_copying_content(catalog_copy_e2e: CatalogCopyE2EFixture) -> None:
    before_canonicals = _canonical_count(catalog_copy_e2e.test_id)
    before_canonical_content = _content_rows_for_canonical(catalog_copy_e2e.canonical_point_id)

    response = catalog_copy_e2e.client.post(
        f"/api/admin/catalog/nodes/{catalog_copy_e2e.source_point_id}/copy",
        json={"parent_id": catalog_copy_e2e.target_dir_id, "title": "Referenced Point"},
    )

    assert response.status_code == 200
    detail = response.json()
    copied_node = detail["node"]
    assert copied_node["node_kind"] == "point"
    assert copied_node["parent_id"] == catalog_copy_e2e.target_dir_id
    assert copied_node["canonical_point_id"] == catalog_copy_e2e.canonical_point_id
    copied_row = _node_row(copied_node["node_id"])
    assert copied_row["metadata"]["copy_reuses_canonical_point"] is True
    assert _canonical_count(catalog_copy_e2e.test_id) == before_canonicals
    assert _content_rows_for_canonical(catalog_copy_e2e.canonical_point_id) == before_canonical_content
    assert _content_rows_for_node(copied_node["node_id"]) == 0


def test_copy_directory_to_other_directory_reuses_descendant_point_identity(catalog_copy_e2e: CatalogCopyE2EFixture) -> None:
    before_canonicals = _canonical_count(catalog_copy_e2e.test_id)
    before_canonical_content = _content_rows_for_canonical(catalog_copy_e2e.canonical_point_id)

    response = catalog_copy_e2e.client.post(
        f"/api/admin/catalog/nodes/{catalog_copy_e2e.source_dir_id}/copy",
        json={"parent_id": catalog_copy_e2e.target_dir_id, "title": "Copied Directory"},
    )

    assert response.status_code == 200
    copied_directory = response.json()["node"]
    assert copied_directory["node_kind"] == "directory"
    assert copied_directory["parent_id"] == catalog_copy_e2e.target_dir_id
    copied_point = _copied_point_from_source(
        copied_parent_id=copied_directory["node_id"],
        source_node_id=catalog_copy_e2e.source_point_id,
    )
    assert copied_point["canonical_point_id"] == catalog_copy_e2e.canonical_point_id
    assert copied_point["metadata"]["copy_reuses_canonical_point"] is True
    assert _canonical_count(catalog_copy_e2e.test_id) == before_canonicals
    assert _content_rows_for_canonical(catalog_copy_e2e.canonical_point_id) == before_canonical_content
    assert _content_rows_for_node(str(copied_point["id"])) == 0
