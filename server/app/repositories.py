from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import text

from server.app.infrastructure.settings import get_settings
from server.app import data_loader
from server.app.infrastructure.database import db_session


class ContentRepository(Protocol):
    def areas(self) -> list[dict[str, Any]]: ...
    def chapters(self) -> list[dict[str, Any]]: ...
    def units(self) -> list[dict[str, Any]]: ...
    def knowledge_points(self) -> list[dict[str, Any]]: ...
    def experiments(self) -> list[dict[str, Any]]: ...
    def learning_cards(self) -> list[dict[str, Any]]: ...
    def questions(self) -> list[dict[str, Any]]: ...
    def links(self) -> list[dict[str, Any]]: ...
    def source_chunks(self) -> list[dict[str, Any]]: ...
    def get_chapter(self, chapter_id: str) -> dict[str, Any] | None: ...
    def get_unit(self, unit_id: str) -> dict[str, Any] | None: ...
    def get_knowledge_point(self, kp_id: str) -> dict[str, Any] | None: ...
    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None: ...
    def get_learning_card(self, experiment_id: str) -> dict[str, Any] | None: ...
    def get_question(self, question_id: str) -> dict[str, Any] | None: ...
    def related_chunks_for_kp(self, kp_id: str, limit: int = 8) -> list[dict[str, Any]]: ...
    def point_question_evidence(
        self,
        experiment_id: str,
        point_key: str,
        limit: int = 12,
    ) -> list[dict[str, Any]]: ...
    def point_reviewed_evidence(self, experiment_id: str, point_key: str) -> dict[str, Any] | None: ...


class LearningRepository(Protocol):
    def load_events(self) -> list[dict[str, Any]]: ...
    def append_event(self, event: dict[str, Any]) -> dict[str, Any]: ...
    def load_mastery(self) -> dict[str, Any]: ...
    def save_mastery(self, data: dict[str, Any]) -> None: ...
    def load_students(self) -> list[dict[str, Any]]: ...
    def save_students(self, students: list[dict[str, Any]]) -> None: ...


class ReviewRepository(Protocol):
    def list_items(self) -> list[dict[str, Any]]: ...


class MediaRepository(Protocol):
    def list_ready_bindings(self, target_type: str, target_id: str) -> list[dict[str, Any]]: ...


class AgentLogRepository(Protocol):
    def append_log(self, log: dict[str, Any]) -> dict[str, Any]: ...


class JsonContentRepository:
    def areas(self) -> list[dict[str, Any]]:
        return data_loader.areas()

    def chapters(self) -> list[dict[str, Any]]:
        return data_loader.chapters()

    def units(self) -> list[dict[str, Any]]:
        return data_loader.units()

    def knowledge_points(self) -> list[dict[str, Any]]:
        return data_loader.knowledge_points()

    def experiments(self) -> list[dict[str, Any]]:
        return data_loader.experiments()

    def learning_cards(self) -> list[dict[str, Any]]:
        return data_loader.learning_cards()

    def questions(self) -> list[dict[str, Any]]:
        return data_loader.questions()

    def links(self) -> list[dict[str, Any]]:
        return data_loader.links()

    def source_chunks(self) -> list[dict[str, Any]]:
        return data_loader.source_chunks()

    def get_chapter(self, chapter_id: str) -> dict[str, Any] | None:
        return data_loader.get_chapter(chapter_id)

    def get_unit(self, unit_id: str) -> dict[str, Any] | None:
        return data_loader.get_unit(unit_id)

    def get_knowledge_point(self, kp_id: str) -> dict[str, Any] | None:
        return data_loader.get_knowledge_point(kp_id)

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        return data_loader.get_experiment(experiment_id)

    def get_learning_card(self, experiment_id: str) -> dict[str, Any] | None:
        return data_loader.get_learning_card(experiment_id)

    def get_question(self, question_id: str) -> dict[str, Any] | None:
        return data_loader.get_question(question_id)

    def related_chunks_for_kp(self, kp_id: str, limit: int = 8) -> list[dict[str, Any]]:
        return data_loader.related_chunks_for_kp(kp_id, limit)

    def point_question_evidence(
        self,
        experiment_id: str,
        point_key: str,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for question in data_loader.questions():
            related_experiment_ids = question.get("related_experiment_ids") or []
            if experiment_id and experiment_id not in related_experiment_ids and question.get("experiment_id") != experiment_id:
                continue
            metadata = _metadata_dict(question.get("metadata"))
            if point_key not in _metadata_point_keys(metadata):
                continue
            result.append({**question, "metadata": metadata})
            if len(result) >= limit:
                break
        return result

    def point_reviewed_evidence(self, experiment_id: str, point_key: str) -> dict[str, Any] | None:
        return None


class JsonLearningRepository:
    def load_events(self) -> list[dict[str, Any]]:
        return data_loader.load_events()

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return data_loader.append_event(event)

    def load_mastery(self) -> dict[str, Any]:
        return data_loader.load_mastery()

    def save_mastery(self, data: dict[str, Any]) -> None:
        data_loader.save_mastery(data)

    def load_students(self) -> list[dict[str, Any]]:
        return data_loader.load_students()

    def save_students(self, students: list[dict[str, Any]]) -> None:
        data_loader.save_students(students)


class JsonReviewRepository:
    def list_items(self) -> list[dict[str, Any]]:
        return data_loader.review_queue()


class EmptyMediaRepository:
    def list_ready_bindings(self, target_type: str, target_id: str) -> list[dict[str, Any]]:
        return []


class NoopAgentLogRepository:
    def append_log(self, log: dict[str, Any]) -> dict[str, Any]:
        return log


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with db_session() as session:
        return [dict(row) for row in session.execute(text(sql), params or {}).mappings().all()]


def _one(sql: str, params: dict[str, Any]) -> dict[str, Any] | None:
    rows = _rows(sql, params)
    return rows[0] if rows else None


def _table_exists(table_name: str) -> bool:
    row = _one("SELECT to_regclass(:table_name) AS table_name", {"table_name": f"public.{table_name}"})
    return bool(row and row.get("table_name"))


def _json_param(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _metadata_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _metadata_point_keys(metadata: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for item in metadata.get("primary_point_keys") or []:
        text = str(item or "").strip()
        if text:
            keys.add(text)
    for item in metadata.get("primary_points") or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("point_key") or "").strip()
        if text:
            keys.add(text)
    return keys


def _published_expr(table_alias: str = "") -> str:
    prefix = f"{table_alias}." if table_alias else ""
    return f"COALESCE({prefix}content_status, 'published') = 'published'"


def _active_curriculum_expr(table_alias: str = "") -> str:
    prefix = f"{table_alias}." if table_alias else ""
    return f"""
    (
      (
        NOT EXISTS (SELECT 1 FROM curriculum_versions WHERE status = 'active')
        AND {prefix}curriculum_version_id IS NULL
      )
      OR {prefix}curriculum_version_id = (
        SELECT id
        FROM curriculum_versions
        WHERE status = 'active'
        ORDER BY published_at DESC NULLS LAST, created_at DESC
        LIMIT 1
      )
    )
    """


class PostgresContentRepository:
    def areas(self) -> list[dict[str, Any]]:
        rows = self.chapters()
        seen: set[str] = set()
        areas: list[dict[str, Any]] = []
        for row in rows:
            area = row.get("element_area") or row.get("chapter_title") or ""
            if area and area not in seen:
                seen.add(area)
                areas.append({"area_id": area, "area_name": area})
        return areas

    def chapters(self) -> list[dict[str, Any]]:
        rows = _rows(
            f"""
            SELECT id AS chapter_id, chapter_number, chapter_title, element_area,
                   review_required, source_label, metadata, content_status
            FROM chapters
            WHERE COALESCE(content_status, 'published') = 'published'
              AND {_active_curriculum_expr()}
            ORDER BY chapter_number NULLS LAST, id
            """
        )
        return rows

    def units(self) -> list[dict[str, Any]]:
        return _rows(
            f"""
            SELECT id AS unit_id, chapter_id, chapter_title, unit_index, unit_title,
                   review_required, source_label, metadata, content_status
            FROM knowledge_units
            WHERE COALESCE(content_status, 'published') = 'published'
              AND {_active_curriculum_expr()}
            ORDER BY chapter_id, unit_index, id
            """
        )

    def knowledge_points(self) -> list[dict[str, Any]]:
        rows = _rows(
            f"""
            SELECT id AS knowledge_point_id, id, chapter_id, chapter_title, unit_id, unit_title,
                   content, element_area, tags, difficulty, review_required, source_label,
                   metadata, content_status
            FROM knowledge_points
            WHERE COALESCE(content_status, 'published') = 'published'
              AND {_active_curriculum_expr()}
            ORDER BY chapter_id, unit_id, id
            """
        )
        return rows

    def experiments(self) -> list[dict[str, Any]]:
        if _table_exists("formal_experiments"):
            rows = _rows(
                """
                SELECT
                  fe.id AS experiment_id,
                  fe.id,
                  fe.code,
                  fe.title AS name,
                  fe.title AS normalized_name,
                  fe.title_en,
                  fe.summary AS objective,
                  fe.summary,
                  fe.status AS content_status,
                  fe.display_order,
                  fe.source_refs,
                  fe.metadata,
                  COALESCE((
                    SELECT array_agg(ecb.chapter_id ORDER BY ecb.sort_order, ecb.chapter_id)
                    FROM experiment_chapter_bindings ecb
                    WHERE ecb.experiment_id = fe.id
                  ), '{}') AS chapter_ids,
                  (
                    SELECT ecb.chapter_id
                    FROM experiment_chapter_bindings ecb
                    WHERE ecb.experiment_id = fe.id
                    ORDER BY CASE ecb.coverage_type WHEN 'primary' THEN 0 WHEN 'partial' THEN 1 ELSE 2 END,
                             ecb.sort_order,
                             ecb.chapter_id
                    LIMIT 1
                  ) AS chapter_id,
                  '{}'::text[] AS related_knowledge_point_ids,
                  '{}'::text[] AS source_chunk_ids,
                  NULL::text AS video_url,
                  'experiment_unit' AS resource_mode,
                  false AS review_required
                FROM formal_experiments fe
                WHERE fe.status <> 'archived'
                ORDER BY fe.display_order, fe.code
                """
            )
            for row in rows:
                metadata = row.get("metadata") or {}
                row["student_visible"] = row.get("content_status") == "published"
                row["formal_catalog"] = True
                row["video_candidates"] = list(metadata.get("video_candidates") or [])
                row["parent_title"] = metadata.get("parent_title")
                row["module_title"] = metadata.get("module_display_title")
            if rows:
                return rows
        rows = _rows(
            """
            SELECT id AS experiment_id, id, name, name AS normalized_name, element_area,
                   element_group, element_group AS chapter_id, related_elements, objective, reagents, steps, phenomena,
                   equations, explanation, video_url, media_status, resource_mode,
                   review_required, content_status, metadata
            FROM experiments
            ORDER BY id
            """
        )
        for row in rows:
            row["student_visible"] = row.get("content_status") == "published"
        return rows

    def learning_cards(self) -> list[dict[str, Any]]:
        rows = _rows(
            """
            SELECT id, experiment_id, title, objective, reagents, steps, phenomena,
                   equations, principle, safety_notes, related_knowledge_points,
                   source_chunks, review_required, content_status
            FROM experiment_learning_cards
            ORDER BY id
            """
        )
        for row in rows:
            row["student_visible"] = row.get("content_status") == "published"
        return rows

    def questions(self) -> list[dict[str, Any]]:
        rows = _rows(
            """
            SELECT id AS question_id, id, question_type, stem, options, answer, explanation,
                   difficulty, related_knowledge_point_ids, related_experiment_ids,
                   source_chunk_ids, review_required, content_status
            FROM questions
            ORDER BY id
            """
        )
        for row in rows:
            row["student_visible"] = row.get("content_status") == "published"
            row["chapter_id"] = self._question_chapter_id(row)
        return rows

    def links(self) -> list[dict[str, Any]]:
        return _rows(
            """
            SELECT id, from_type, from_id, relation, to_type, to_id, confidence,
                   review_required, content_status
            FROM links
            ORDER BY id
            """
        )

    def source_chunks(self) -> list[dict[str, Any]]:
        return _rows(
            """
            SELECT sc.id AS chunk_id, sc.id, sc.document_id, sd.file_name AS source_file,
                   sc.chapter_id, sc.page_number, sc.section_title, sc.chunk_index, sc.text,
                   sc.markdown, sc.related_knowledge_point_ids, sc.related_experiment_ids,
                   sc.tags, sc.metadata, sc.review_required, sc.content_status
            FROM source_chunks sc
            LEFT JOIN source_documents sd ON sd.id = sc.document_id
            ORDER BY sc.document_id, sc.chunk_index, sc.id
            """
        )

    def get_chapter(self, chapter_id: str) -> dict[str, Any] | None:
        return _one(
            f"""
            SELECT id AS chapter_id, chapter_number, chapter_title, element_area,
                   review_required, source_label, metadata, content_status
            FROM chapters
            WHERE id = :chapter_id AND COALESCE(content_status, 'published') = 'published'
              AND {_active_curriculum_expr()}
            """,
            {"chapter_id": chapter_id},
        )

    def get_unit(self, unit_id: str) -> dict[str, Any] | None:
        return _one(
            f"""
            SELECT id AS unit_id, chapter_id, chapter_title, unit_index, unit_title,
                   review_required, source_label, metadata, content_status
            FROM knowledge_units
            WHERE id = :unit_id AND COALESCE(content_status, 'published') = 'published'
              AND {_active_curriculum_expr()}
            """,
            {"unit_id": unit_id},
        )

    def get_knowledge_point(self, kp_id: str) -> dict[str, Any] | None:
        return _one(
            f"""
            SELECT id AS knowledge_point_id, id, chapter_id, chapter_title, unit_id,
                   unit_title, content, element_area, tags, difficulty, review_required,
                   source_label, metadata, content_status
            FROM knowledge_points
            WHERE id = :kp_id AND COALESCE(content_status, 'published') = 'published'
              AND {_active_curriculum_expr()}
            """,
            {"kp_id": kp_id},
        )

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        rows = [item for item in self.experiments() if item.get("experiment_id") == experiment_id or item.get("id") == experiment_id]
        return rows[0] if rows else None

    def get_learning_card(self, experiment_id: str) -> dict[str, Any] | None:
        rows = [item for item in self.learning_cards() if item.get("experiment_id") == experiment_id]
        return rows[0] if rows else None

    def get_question(self, question_id: str) -> dict[str, Any] | None:
        rows = [item for item in self.questions() if item.get("question_id") == question_id or item.get("id") == question_id]
        return rows[0] if rows else None

    def related_chunks_for_kp(self, kp_id: str, limit: int = 8) -> list[dict[str, Any]]:
        rows = _rows(
            """
            SELECT sc.id AS chunk_id, sc.id, sc.document_id, sd.file_name AS source_file,
                   sc.chapter_id, sc.page_number, sc.section_title, sc.chunk_index, sc.text,
                   sc.markdown, sc.related_knowledge_point_ids, sc.related_experiment_ids,
                   sc.tags, sc.metadata, sc.review_required, sc.content_status
            FROM links l
            JOIN source_chunks sc ON sc.id = l.from_id
            LEFT JOIN source_documents sd ON sd.id = sc.document_id
            WHERE l.from_type = 'source_chunk'
              AND l.to_type = 'knowledge_point'
              AND l.to_id = :kp_id
              AND COALESCE(l.content_status, 'pending_review') = 'published'
              AND COALESCE(sc.content_status, 'pending_review') = 'published'
            ORDER BY l.confidence DESC NULLS LAST, sc.id
            LIMIT :limit
            """,
            {"kp_id": kp_id, "limit": limit},
        )
        if rows:
            return rows
        return _rows(
            """
            SELECT sc.id AS chunk_id, sc.id, sc.document_id, sd.file_name AS source_file,
                   sc.chapter_id, sc.page_number, sc.section_title, sc.chunk_index, sc.text,
                   sc.markdown, sc.related_knowledge_point_ids, sc.related_experiment_ids,
                   sc.tags, sc.metadata, sc.review_required, sc.content_status
            FROM source_chunks sc
            LEFT JOIN source_documents sd ON sd.id = sc.document_id
            WHERE :kp_id = ANY(sc.related_knowledge_point_ids)
              AND COALESCE(sc.content_status, 'pending_review') = 'published'
            ORDER BY sc.document_id, sc.chunk_index
            LIMIT :limit
            """,
            {"kp_id": kp_id, "limit": limit},
        )

    def point_question_evidence(
        self,
        experiment_id: str,
        point_key: str,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        if not experiment_id or not point_key or not _table_exists("experiment_questions"):
            return []
        rows = _rows(
            """
            SELECT
              q.id::text AS question_id,
              q.id::text AS id,
              q.experiment_id,
              q.question_type,
              q.stem,
              q.source_chunk_ids,
              q.source_refs,
              q.status,
              q.metadata,
              q.updated_at,
              q.created_at
            FROM experiment_questions q
            WHERE q.experiment_id = :experiment_id
              AND COALESCE(q.status, 'draft') = 'published'
              AND (
                q.metadata->'primary_point_keys' ? :point_key
                OR EXISTS (
                  SELECT 1
                  FROM jsonb_array_elements(
                    CASE
                      WHEN jsonb_typeof(q.metadata->'primary_points') = 'array'
                      THEN q.metadata->'primary_points'
                      ELSE '[]'::jsonb
                    END
                  ) AS point
                  WHERE point->>'point_key' = :point_key
                )
              )
            ORDER BY q.updated_at DESC NULLS LAST, q.created_at DESC NULLS LAST
            LIMIT :limit
            """,
            {"experiment_id": experiment_id, "point_key": point_key, "limit": limit},
        )
        for row in rows:
            row["metadata"] = _metadata_dict(row.get("metadata"))
        return rows

    def point_reviewed_evidence(self, experiment_id: str, point_key: str) -> dict[str, Any] | None:
        if not experiment_id or not point_key or not _table_exists("experiment_video_point_evidence"):
            return None
        row = _one(
            """
            SELECT
              experiment_id,
              point_key,
              experiment_code,
              point_title,
              experiment_chunk_ids,
              theory_chunk_ids,
              manual_reviewed,
              review_grade,
              source_label,
              metadata,
              created_at,
              updated_at
            FROM experiment_video_point_evidence
            WHERE experiment_id = :experiment_id
              AND point_key = :point_key
            """,
            {"experiment_id": experiment_id, "point_key": point_key},
        )
        if not row:
            return None
        row["metadata"] = _metadata_dict(row.get("metadata"))
        return row

    def _question_chapter_id(self, question: dict[str, Any]) -> str | None:
        kp_ids = question.get("related_knowledge_point_ids") or []
        if not kp_ids:
            return None
        point = self.get_knowledge_point(kp_ids[0])
        return point.get("chapter_id") if point else None


class PostgresLearningRepository:
    def load_events(self) -> list[dict[str, Any]]:
        return _rows(
            """
            SELECT id, student_id, event_type, chapter_id, unit_id, knowledge_point_id, experiment_id, point_node_id,
                   question_id, difficulty, correct, metadata, created_at
            FROM student_events
            ORDER BY created_at
            """
        )

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        with db_session() as session:
            session.execute(
                text(
                    """
                    INSERT INTO student_events (
                      student_id, event_type, chapter_id, unit_id, knowledge_point_id, experiment_id,
                      point_node_id, question_id, difficulty, correct, metadata, created_at
                    )
                    VALUES (
                      :student_id, :event_type, :chapter_id, :unit_id, :knowledge_point_id, :experiment_id,
                      :point_node_id, :question_id, :difficulty, :correct, CAST(:metadata AS jsonb),
                      COALESCE(CAST(:created_at AS timestamptz), now())
                    )
                    """
                ),
                {
                    "student_id": event.get("student_id"),
                    "event_type": event.get("event_type"),
                    "chapter_id": event.get("chapter_id"),
                    "unit_id": event.get("unit_id"),
                    "knowledge_point_id": event.get("knowledge_point_id"),
                    "experiment_id": event.get("experiment_id"),
                    "point_node_id": event.get("point_node_id") or (event.get("metadata") or {}).get("point_node_id"),
                    "question_id": event.get("question_id"),
                    "difficulty": event.get("difficulty"),
                    "correct": event.get("correct"),
                    "metadata": _json_param(event.get("metadata")),
                    "created_at": event.get("created_at"),
                },
            )
        return event

    def load_mastery(self) -> dict[str, Any]:
        rows = _rows(
            """
            SELECT student_id, knowledge_point_id, state_prob, mastery_score, updated_at
            FROM student_mastery
            """
        )
        mastery: dict[str, Any] = {}
        for row in rows:
            student = mastery.setdefault(row["student_id"], {})
            student[row["knowledge_point_id"]] = {
                "state_prob": [float(value) for value in row["state_prob"]],
                "mastery_score": float(row["mastery_score"]),
                "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
                "history": [],
            }
        return mastery

    def save_mastery(self, data: dict[str, Any]) -> None:
        with db_session() as session:
            for student_id, student_mastery in data.items():
                for kp_id, state in student_mastery.items():
                    session.execute(
                        text(
                            """
                            INSERT INTO student_mastery (
                              student_id, knowledge_point_id, state_prob, mastery_score, updated_at
                            )
                            VALUES (:student_id, :kp_id, :state_prob, :mastery_score, now())
                            ON CONFLICT (student_id, knowledge_point_id)
                            DO UPDATE SET
                              state_prob = EXCLUDED.state_prob,
                              mastery_score = EXCLUDED.mastery_score,
                              updated_at = now()
                            """
                        ),
                        {
                            "student_id": student_id,
                            "kp_id": kp_id,
                            "state_prob": state.get("state_prob") or [],
                            "mastery_score": state.get("mastery_score") or 0,
                        },
                    )

    def load_students(self) -> list[dict[str, Any]]:
        return _rows(
            """
            SELECT sp.student_id AS id, sp.student_id, sp.student_name AS display_name,
                   c.class_name, sp.class_id, au.status, sp.metadata, sp.created_at
            FROM student_profiles sp
            JOIN app_users au ON au.id = sp.user_id
            LEFT JOIN classes c ON c.id = sp.class_id
            ORDER BY c.class_name, sp.student_id
            """
        )

    def save_students(self, students: list[dict[str, Any]]) -> None:
        raise NotImplementedError("Postgres student writes must use roster/account services")


class PostgresReviewRepository:
    def list_items(self) -> list[dict[str, Any]]:
        from server.app.review import list_review_items

        return list_review_items()["items"]


class PostgresMediaRepository:
    def list_ready_bindings(self, target_type: str, target_id: str) -> list[dict[str, Any]]:
        rows = _rows(
            """
            SELECT mb.id AS binding_id, mb.target_type, mb.target_id, mb.title,
                   mb.metadata->>'point_key' AS point_key,
                   mb.metadata->>'point_title' AS point_title,
                   ma.id AS media_id, ma.original_file_name,
                   COALESCE(ma.playback_relative_path, ma.relative_path) AS relative_path,
                   ma.thumbnail_relative_path,
                   COALESCE(ma.playback_mime_type, ma.mime_type) AS mime_type,
                   ma.file_size_bytes, ma.duration_seconds,
                   ma.width, ma.height, ma.video_codec, ma.audio_codec
            FROM media_bindings mb
            JOIN media_assets ma ON ma.id = mb.media_asset_id
            WHERE mb.target_type = :target_type
              AND mb.target_id = :target_id
              AND mb.status = 'published'
              AND ma.upload_status = 'ready'
              AND COALESCE(ma.lifecycle_status, 'active') = 'active'
            ORDER BY mb.sort_order, mb.created_at
            """,
            {"target_type": target_type, "target_id": target_id},
        )
        public_base_url = get_settings().api_public_base_url
        for row in rows:
            row["playback_url"] = f"{public_base_url}/api/media/{row['media_id']}"
            if row.get("thumbnail_relative_path"):
                row["poster_url"] = f"{public_base_url}/api/media/{row['media_id']}/poster"
        return rows


class PostgresAgentLogRepository:
    def append_log(self, log: dict[str, Any]) -> dict[str, Any]:
        with db_session() as session:
            session.execute(
                text(
                    """
                    INSERT INTO agent_logs (
                      user_id, student_id, user_role, question, classification,
                      tool_calls, source_refs, guardrail_decisions, response_text,
                      response_metadata
                    )
                    VALUES (
                      :user_id, :student_id, :user_role, :question,
                      CAST(:classification AS jsonb), CAST(:tool_calls AS jsonb),
                      CAST(:source_refs AS jsonb), CAST(:guardrail_decisions AS jsonb),
                      :response_text, CAST(:response_metadata AS jsonb)
                    )
                    """
                ),
                {
                    "user_id": log.get("user_id"),
                    "student_id": log.get("student_id"),
                    "user_role": log.get("user_role"),
                    "question": log.get("question") or "",
                    "classification": _json_param(log.get("classification")),
                    "tool_calls": _json_param(log.get("tool_calls") or []),
                    "source_refs": _json_param(log.get("source_refs") or []),
                    "guardrail_decisions": _json_param(log.get("guardrail_decisions") or []),
                    "response_text": log.get("response_text"),
                    "response_metadata": _json_param(log.get("response_metadata")),
                },
            )
        return log


@dataclass(frozen=True)
class RepositoryProvider:
    content: ContentRepository
    learning: LearningRepository
    review: ReviewRepository
    media: MediaRepository
    agent_logs: AgentLogRepository


def get_repositories() -> RepositoryProvider:
    settings = get_settings()
    if settings.data_backend == "postgres":
        return RepositoryProvider(
            content=PostgresContentRepository(),
            learning=PostgresLearningRepository(),
            review=PostgresReviewRepository(),
            media=PostgresMediaRepository(),
            agent_logs=PostgresAgentLogRepository(),
        )
    return RepositoryProvider(
        content=JsonContentRepository(),
        learning=JsonLearningRepository(),
        review=JsonReviewRepository(),
        media=EmptyMediaRepository(),
        agent_logs=NoopAgentLogRepository(),
    )
