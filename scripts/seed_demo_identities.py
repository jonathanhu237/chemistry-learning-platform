from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import bindparam, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.database import apply_migrations, db_session
from server.app.security import hash_password, verify_password

DEFAULT_SEED_PATH = ROOT / "data" / "seed" / "identity" / "demo_identity_seed_v1.json"
SEED_TYPE = "demo_identity_seed"
SEED_VERSION = 1
LEGACY_SEED_STUDENT_PATTERN = "SEED%"
LEGACY_SEED_STUDENT_ID_TABLES = (
    "agent_logs",
    "experiment_question_attempts",
    "student_assessment_reports",
    "student_events",
    "student_experiment_mastery",
    "student_experiment_progress",
    "student_feedback",
    "student_mastery",
    "student_point_mastery",
    "student_posttest_sessions",
    "student_pretest_sessions",
    "student_smart_assessment_sessions",
)


def _json_param(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_student_id(value: str) -> str:
    return value.strip().upper()


def _seed_classes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    classes = payload.get("classes")
    if isinstance(classes, list) and classes:
        return [item for item in classes if isinstance(item, dict)]
    klass = payload.get("class")
    return [klass] if isinstance(klass, dict) else []


def _resolved_classes(
    payload: dict[str, Any],
    *,
    class_id: str | None = None,
    class_name: str | None = None,
) -> list[dict[str, Any]]:
    class_id_override = class_id or os.getenv("SEED_CLASS_ID")
    class_name_override = class_name or os.getenv("SEED_CLASS_NAME")
    resolved: list[dict[str, Any]] = []
    for index, klass in enumerate(_seed_classes(payload)):
        source_id = str(klass.get("id") or "").strip()
        source_name = str(klass.get("class_name") or source_id).strip()
        resolved_id = class_id_override if index == 0 and class_id_override else source_id
        resolved_name = class_name_override if index == 0 and class_name_override else source_name
        resolved.append(
            {
                "source_id": source_id,
                "id": str(resolved_id).strip(),
                "class_name": str(resolved_name).strip(),
                "payload": klass,
            }
        )
    return resolved


def load_seed(path: Path = DEFAULT_SEED_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    if payload.get("seed_type") != SEED_TYPE:
        raise ValueError(f"{path} seed_type must be {SEED_TYPE!r}")
    if int(payload.get("version") or 0) != SEED_VERSION:
        raise ValueError(f"{path} version must be {SEED_VERSION}")
    if not isinstance(payload.get("teacher"), dict):
        raise ValueError(f"{path} teacher must be an object")
    if not _seed_classes(payload):
        raise ValueError(f"{path} must define class or classes")
    if not isinstance(payload.get("students"), list):
        raise ValueError(f"{path} students must be a list")
    return payload


def _secret_from_spec(spec: dict[str, Any], *, override: str | None = None) -> str:
    if override:
        return override
    env_name = str(spec.get("env") or "").strip()
    if env_name and os.getenv(env_name):
        return os.environ[env_name]
    value = str(spec.get("default") or "").strip()
    if not value:
        raise ValueError("Seed password is empty; provide a CLI override or environment variable.")
    return value


def _existing_password_hash(session: Any, username: str) -> str | None:
    row = session.execute(
        text("SELECT password_hash FROM app_users WHERE username = :username"),
        {"username": username},
    ).mappings().first()
    return str(row["password_hash"]) if row else None


def _password_hash_for_upsert(session: Any, *, username: str, password: str) -> tuple[str, bool]:
    existing = _existing_password_hash(session, username)
    if existing and verify_password(password, existing):
        return existing, False
    return hash_password(password), True


def _validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    teacher = payload.get("teacher") or {}
    classes = _seed_classes(payload)
    students = payload.get("students") or []
    if not str(teacher.get("username") or "").strip():
        errors.append("teacher.username is required")
    if (teacher.get("role") or "teacher") != "teacher":
        errors.append("teacher.role must be teacher")
    if not classes:
        errors.append("class or classes is required")
    seen_classes: set[str] = set()
    for index, klass in enumerate(classes, start=1):
        class_id = str(klass.get("id") or "").strip()
        if not class_id:
            errors.append(f"classes[{index}].id is required")
            continue
        if class_id in seen_classes:
            errors.append(f"classes[{index}].id duplicates {class_id}")
        seen_classes.add(class_id)
        if not str(klass.get("class_name") or "").strip():
            errors.append(f"classes[{index}].class_name is required")
    default_class_id = str(classes[0].get("id") or "").strip() if classes else ""
    seen_students: set[str] = set()
    for index, student in enumerate(students, start=1):
        if not isinstance(student, dict):
            errors.append(f"students[{index}] must be an object")
            continue
        student_id = _normalize_student_id(str(student.get("student_id") or ""))
        if not student_id:
            errors.append(f"students[{index}].student_id is required")
            continue
        if student_id in seen_students:
            errors.append(f"students[{index}].student_id duplicates {student_id}")
        seen_students.add(student_id)
        student_class_id = str(student.get("class_id") or default_class_id).strip()
        if not student_class_id:
            errors.append(f"students[{index}].class_id is required")
        elif seen_classes and student_class_id not in seen_classes:
            errors.append(f"students[{index}].class_id {student_class_id!r} is not defined")
        if not str(student.get("student_name") or "").strip():
            errors.append(f"students[{index}].student_name is required")
    expected = payload.get("expected_counts") or {}
    expected_classes = int(expected.get("classes") or len(classes))
    if len(classes) != expected_classes:
        errors.append(f"classes: expected {expected_classes}, got {len(classes)}")
    expected_students = int(expected.get("students") or len(students))
    if len(students) != expected_students:
        errors.append(f"students: expected {expected_students}, got {len(students)}")
    return errors


def validate_seed_payload(payload: dict[str, Any]) -> dict[str, Any]:
    errors = _validate_payload(payload)
    return {
        "ok": not errors,
        "errors": errors,
        "summary": {
            "teacher": 1 if isinstance(payload.get("teacher"), dict) else 0,
            "classes": len(_seed_classes(payload)),
            "students": len(payload.get("students") or []),
        },
    }


def _seed_metadata(payload: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = {
        "seed_owned": True,
        "seed_type": SEED_TYPE,
        "seed_version": payload.get("seed_version") or "demo-identity-v1",
        "seeded_at": _iso_now(),
    }
    if extra:
        metadata.update(extra)
    return metadata


def _prune_legacy_seed_students(session: Any, payload: dict[str, Any]) -> int:
    students = [item for item in payload.get("students") or [] if isinstance(item, dict)]
    if any(_normalize_student_id(str(student.get("student_id") or "")).startswith("SEED") for student in students):
        return 0

    params = {"pattern": LEGACY_SEED_STUDENT_PATTERN, "seed_type": SEED_TYPE}
    deleted = 0
    for table_name in LEGACY_SEED_STUDENT_ID_TABLES:
        result = session.execute(text(f"DELETE FROM {table_name} WHERE student_id LIKE :pattern"), params)
        deleted += int(result.rowcount or 0)
    for table_name in ("student_profiles", "roster_entries", "students"):
        result = session.execute(
            text(
                f"""
                DELETE FROM {table_name}
                WHERE student_id LIKE :pattern
                  AND COALESCE(metadata->>'seed_type', '') = :seed_type
                """
            ),
            params,
        )
        deleted += int(result.rowcount or 0)
    result = session.execute(
        text(
            """
            DELETE FROM app_users
            WHERE username LIKE :pattern
              AND role = 'student'
              AND COALESCE(metadata->>'seed_type', '') = :seed_type
            """
        ),
        params,
    )
    deleted += int(result.rowcount or 0)
    return deleted


def _upsert_teacher(
    session: Any,
    payload: dict[str, Any],
    *,
    username: str,
    password: str,
    display_name: str | None = None,
) -> str:
    teacher = payload["teacher"]
    password_hash, password_changed = _password_hash_for_upsert(session, username=username, password=password)
    row = session.execute(
        text(
            """
            INSERT INTO app_users (
              username, role, display_name, password_hash, status, must_change_password,
              password_version, metadata, account_purpose, updated_at
            )
            VALUES (
              :username, :role, :display_name, :password_hash, :status, :must_change_password,
              1, CAST(:metadata AS jsonb), 'standard', now()
            )
            ON CONFLICT (username) DO UPDATE SET
              role = EXCLUDED.role,
              display_name = EXCLUDED.display_name,
              password_hash = CASE WHEN :password_changed THEN EXCLUDED.password_hash ELSE app_users.password_hash END,
              status = EXCLUDED.status,
              must_change_password = EXCLUDED.must_change_password,
              password_version = CASE
                WHEN :password_changed THEN app_users.password_version + 1
                ELSE app_users.password_version
              END,
              metadata = COALESCE(app_users.metadata, '{}'::jsonb) || EXCLUDED.metadata,
              account_purpose = 'standard',
              updated_at = now()
            RETURNING id
            """
        ),
        {
            "username": username,
            "role": teacher.get("role") or "teacher",
            "display_name": display_name or teacher.get("display_name") or username,
            "password_hash": password_hash,
            "password_changed": password_changed,
            "status": teacher.get("status") or "active",
            "must_change_password": bool(teacher.get("must_change_password", False)),
            "metadata": _json_param(_seed_metadata(payload, teacher.get("metadata") if isinstance(teacher.get("metadata"), dict) else {})),
        },
    ).mappings().one()
    return str(row["id"])


def _upsert_class(
    session: Any,
    payload: dict[str, Any],
    *,
    klass: dict[str, Any],
    teacher_user_id: str,
    class_id: str,
    class_name: str | None = None,
) -> None:
    session.execute(
        text(
            """
            INSERT INTO classes (
              id, class_name, description, status, metadata, class_purpose,
              owner_teacher_user_id, system_managed, hidden_from_teacher, updated_at
            )
            VALUES (
              :class_id, :class_name, :description, :status, CAST(:metadata AS jsonb), :class_purpose,
              CAST(:teacher_user_id AS uuid), :system_managed, :hidden_from_teacher, now()
            )
            ON CONFLICT (id) DO UPDATE SET
              class_name = EXCLUDED.class_name,
              description = EXCLUDED.description,
              status = EXCLUDED.status,
              metadata = COALESCE(classes.metadata, '{}'::jsonb) || EXCLUDED.metadata,
              class_purpose = EXCLUDED.class_purpose,
              owner_teacher_user_id = EXCLUDED.owner_teacher_user_id,
              system_managed = EXCLUDED.system_managed,
              hidden_from_teacher = EXCLUDED.hidden_from_teacher,
              updated_at = now()
            """
        ),
        {
            "class_id": class_id,
            "class_name": class_name or klass.get("class_name") or class_id,
            "description": klass.get("description"),
            "status": klass.get("status") or "active",
            "metadata": _json_param(_seed_metadata(payload, klass.get("metadata") if isinstance(klass.get("metadata"), dict) else {})),
            "class_purpose": klass.get("class_purpose") or "instructional",
            "teacher_user_id": teacher_user_id,
            "system_managed": bool(klass.get("system_managed", False)),
            "hidden_from_teacher": bool(klass.get("hidden_from_teacher", False)),
        },
    )
    session.execute(
        text(
            """
            INSERT INTO teacher_classes (teacher_user_id, class_id, class_role)
            VALUES (CAST(:teacher_user_id AS uuid), :class_id, :class_role)
            ON CONFLICT (teacher_user_id, class_id) DO UPDATE SET
              class_role = EXCLUDED.class_role
            """
        ),
        {
            "teacher_user_id": teacher_user_id,
            "class_id": class_id,
            "class_role": klass.get("teacher_class_role") or "owner",
        },
    )


def _upsert_registration_settings(
    session: Any,
    payload: dict[str, Any],
    *,
    teacher_user_id: str,
    class_id: str,
    student_password: str,
) -> None:
    settings = payload.get("registration_settings") or {}
    password_hash = hash_password(student_password) if settings.get("default_password_mode") == "shared" else None
    session.execute(
        text(
            """
            INSERT INTO registration_settings (
              id, mode, default_password_policy, default_password_mode,
              default_password_hash, updated_by, metadata, updated_at
            )
            VALUES (
              'student_registration', :mode, :policy, :password_mode,
              :password_hash, CAST(:teacher_user_id AS uuid), CAST(:metadata AS jsonb), now()
            )
            ON CONFLICT (id) DO UPDATE SET
              mode = EXCLUDED.mode,
              default_password_policy = EXCLUDED.default_password_policy,
              default_password_mode = EXCLUDED.default_password_mode,
              default_password_hash = EXCLUDED.default_password_hash,
              updated_by = EXCLUDED.updated_by,
              metadata = COALESCE(registration_settings.metadata, '{}'::jsonb) || EXCLUDED.metadata,
              updated_at = now()
            """
        ),
        {
            "mode": settings.get("mode") or "roster_only",
            "policy": settings.get("default_password_policy") or "seed_demo_shared_password",
            "password_mode": settings.get("default_password_mode") or "shared",
            "password_hash": password_hash,
            "teacher_user_id": teacher_user_id,
            "metadata": _json_param(_seed_metadata(payload, settings.get("metadata") if isinstance(settings.get("metadata"), dict) else {})),
        },
    )
    session.execute(
        text(
            """
            INSERT INTO class_registration_settings (
              class_id, mode, default_password_policy, default_password_mode,
              default_password_hash, updated_by, metadata, updated_at
            )
            VALUES (
              :class_id, :mode, :policy, :password_mode,
              :password_hash, CAST(:teacher_user_id AS uuid), CAST(:metadata AS jsonb), now()
            )
            ON CONFLICT (class_id) DO UPDATE SET
              mode = EXCLUDED.mode,
              default_password_policy = EXCLUDED.default_password_policy,
              default_password_mode = EXCLUDED.default_password_mode,
              default_password_hash = EXCLUDED.default_password_hash,
              updated_by = EXCLUDED.updated_by,
              metadata = COALESCE(class_registration_settings.metadata, '{}'::jsonb) || EXCLUDED.metadata,
              updated_at = now()
            """
        ),
        {
            "class_id": class_id,
            "mode": settings.get("mode") or "roster_only",
            "policy": settings.get("default_password_policy") or "seed_demo_shared_password",
            "password_mode": settings.get("default_password_mode") or "shared",
            "password_hash": password_hash,
            "teacher_user_id": teacher_user_id,
            "metadata": _json_param(_seed_metadata(payload, settings.get("metadata") if isinstance(settings.get("metadata"), dict) else {})),
        },
    )


def _upsert_student(
    session: Any,
    payload: dict[str, Any],
    *,
    student: dict[str, Any],
    teacher_user_id: str,
    class_id: str,
    class_name: str,
    row_number: int,
    student_password: str,
) -> None:
    student_id = _normalize_student_id(str(student.get("student_id") or ""))
    username = _normalize_student_id(str(student.get("username") or student_id))
    student_name = str(student.get("student_name") or student.get("display_name") or student_id).strip()
    password_hash, password_changed = _password_hash_for_upsert(session, username=username, password=student_password)
    metadata = _seed_metadata(payload, {"student_id": student_id})
    user_row = session.execute(
        text(
            """
            INSERT INTO app_users (
              username, role, display_name, password_hash, status, must_change_password,
              password_version, metadata, account_purpose, owner_teacher_user_id, updated_at
            )
            VALUES (
              :username, 'student', :display_name, :password_hash, :status, :must_change_password,
              1, CAST(:metadata AS jsonb), :account_purpose, CAST(:teacher_user_id AS uuid), now()
            )
            ON CONFLICT (username) DO UPDATE SET
              role = 'student',
              display_name = EXCLUDED.display_name,
              password_hash = CASE WHEN :password_changed THEN EXCLUDED.password_hash ELSE app_users.password_hash END,
              status = EXCLUDED.status,
              must_change_password = EXCLUDED.must_change_password,
              password_version = CASE
                WHEN :password_changed THEN app_users.password_version + 1
                ELSE app_users.password_version
              END,
              metadata = COALESCE(app_users.metadata, '{}'::jsonb) || EXCLUDED.metadata,
              account_purpose = EXCLUDED.account_purpose,
              owner_teacher_user_id = EXCLUDED.owner_teacher_user_id,
              updated_at = now()
            RETURNING id
            """
        ),
        {
            "username": username,
            "display_name": student.get("display_name") or student_name,
            "password_hash": password_hash,
            "password_changed": password_changed,
            "status": student.get("status") or "active",
            "must_change_password": bool(student.get("must_change_password", False)),
            "metadata": _json_param(metadata),
            "account_purpose": student.get("account_purpose") or "standard",
            "teacher_user_id": teacher_user_id,
        },
    ).mappings().one()
    user_id = str(user_row["id"])
    roster_row = session.execute(
        text(
            """
            INSERT INTO roster_entries (
              class_id, student_id, student_name, normalized_student_id,
              status, activation_mode, activated_user_id, row_number, errors,
              metadata, entry_purpose, owner_teacher_user_id, system_managed, updated_at
            )
            VALUES (
              :class_id, :student_id, :student_name, :normalized_student_id,
              :status, 'default_password', CAST(:user_id AS uuid), :row_number, '[]'::jsonb,
              CAST(:metadata AS jsonb), :entry_purpose, CAST(:teacher_user_id AS uuid), false, now()
            )
            ON CONFLICT (class_id, student_id) DO UPDATE SET
              student_name = EXCLUDED.student_name,
              normalized_student_id = EXCLUDED.normalized_student_id,
              status = EXCLUDED.status,
              activation_mode = EXCLUDED.activation_mode,
              activated_user_id = EXCLUDED.activated_user_id,
              row_number = EXCLUDED.row_number,
              errors = '[]'::jsonb,
              metadata = COALESCE(roster_entries.metadata, '{}'::jsonb) || EXCLUDED.metadata,
              entry_purpose = EXCLUDED.entry_purpose,
              owner_teacher_user_id = EXCLUDED.owner_teacher_user_id,
              system_managed = false,
              updated_at = now()
            RETURNING id
            """
        ),
        {
            "class_id": class_id,
            "student_id": student_id,
            "student_name": student_name,
            "normalized_student_id": student_id,
            "status": student.get("status") or "active",
            "user_id": user_id,
            "row_number": row_number,
            "metadata": _json_param(metadata),
            "entry_purpose": student.get("entry_purpose") or "instructional",
            "teacher_user_id": teacher_user_id,
        },
    ).mappings().one()
    roster_entry_id = str(roster_row["id"])
    session.execute(
        text(
            """
            INSERT INTO student_profiles (
              user_id, student_id, student_name, class_id, roster_entry_id,
              activated_at, metadata, profile_purpose, owner_teacher_user_id, updated_at
            )
            VALUES (
              CAST(:user_id AS uuid), :student_id, :student_name, :class_id,
              CAST(:roster_entry_id AS uuid), now(), CAST(:metadata AS jsonb),
              :profile_purpose, CAST(:teacher_user_id AS uuid), now()
            )
            ON CONFLICT (student_id) DO UPDATE SET
              user_id = EXCLUDED.user_id,
              student_name = EXCLUDED.student_name,
              class_id = EXCLUDED.class_id,
              roster_entry_id = EXCLUDED.roster_entry_id,
              activated_at = COALESCE(student_profiles.activated_at, now()),
              metadata = COALESCE(student_profiles.metadata, '{}'::jsonb) || EXCLUDED.metadata,
              profile_purpose = EXCLUDED.profile_purpose,
              owner_teacher_user_id = EXCLUDED.owner_teacher_user_id,
              updated_at = now()
            """
        ),
        {
            "user_id": user_id,
            "student_id": student_id,
            "student_name": student_name,
            "class_id": class_id,
            "roster_entry_id": roster_entry_id,
            "metadata": _json_param(metadata),
            "profile_purpose": student.get("profile_purpose") or "instructional",
            "teacher_user_id": teacher_user_id,
        },
    )
    session.execute(
        text(
            """
            INSERT INTO students (id, display_name, class_name, metadata, user_id, student_id, class_id, status, updated_at)
            VALUES (
              :student_id, :display_name, :class_name, CAST(:metadata AS jsonb),
              CAST(:user_id AS uuid), :student_id, :class_id, 'active', now()
            )
            ON CONFLICT (id) DO UPDATE SET
              display_name = EXCLUDED.display_name,
              class_name = EXCLUDED.class_name,
              metadata = COALESCE(students.metadata, '{}'::jsonb) || EXCLUDED.metadata,
              user_id = EXCLUDED.user_id,
              student_id = EXCLUDED.student_id,
              class_id = EXCLUDED.class_id,
              status = 'active',
              updated_at = now()
            """
        ),
        {
            "student_id": student_id,
            "display_name": student.get("display_name") or student_name,
            "class_name": class_name,
            "metadata": _json_param(metadata),
            "user_id": user_id,
            "class_id": class_id,
        },
    )


def import_seed(
    payload: dict[str, Any],
    *,
    teacher_username: str | None = None,
    teacher_password: str | None = None,
    teacher_display_name: str | None = None,
    class_id: str | None = None,
    class_name: str | None = None,
    student_password: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    validation = validate_seed_payload(payload)
    if not validation["ok"]:
        raise ValueError("Identity seed validation failed:\n" + "\n".join(validation["errors"]))
    teacher = payload["teacher"]
    settings = payload.get("registration_settings") or {}
    resolved_teacher_username = teacher_username or os.getenv("SEED_TEACHER_USERNAME") or str(teacher["username"])
    resolved_teacher_password = _secret_from_spec(teacher.get("password") or {}, override=teacher_password)
    resolved_seed_classes = _resolved_classes(payload, class_id=class_id, class_name=class_name)
    if not resolved_seed_classes:
        raise ValueError("Identity seed has no classes to import.")
    class_by_source_id = {item["source_id"]: item for item in resolved_seed_classes}
    default_source_class_id = resolved_seed_classes[0]["source_id"]
    resolved_student_password = _secret_from_spec(settings.get("default_password") or {}, override=student_password)
    students = [item for item in payload.get("students") or [] if isinstance(item, dict)]
    summary = {
        "teacher_username": resolved_teacher_username,
        "classes": len(resolved_seed_classes),
        "class_ids": [item["id"] for item in resolved_seed_classes],
        "students": len(students),
        "writes": not dry_run,
    }
    if dry_run:
        return summary
    with db_session() as session:
        teacher_user_id = _upsert_teacher(
            session,
            payload,
            username=resolved_teacher_username,
            password=resolved_teacher_password,
            display_name=teacher_display_name,
        )
        for resolved_class in resolved_seed_classes:
            _upsert_class(
                session,
                payload,
                klass=resolved_class["payload"],
                teacher_user_id=teacher_user_id,
                class_id=resolved_class["id"],
                class_name=resolved_class["class_name"],
            )
            _upsert_registration_settings(
                session,
                payload,
                teacher_user_id=teacher_user_id,
                class_id=resolved_class["id"],
                student_password=resolved_student_password,
            )
        pruned_legacy_seed_students = _prune_legacy_seed_students(session, payload)
        row_numbers_by_class: dict[str, int] = {}
        for student in students:
            source_class_id = str(student.get("class_id") or default_source_class_id).strip()
            resolved_class = class_by_source_id[source_class_id]
            row_numbers_by_class[resolved_class["id"]] = row_numbers_by_class.get(resolved_class["id"], 0) + 1
            _upsert_student(
                session,
                payload,
                student=student,
                teacher_user_id=teacher_user_id,
                class_id=resolved_class["id"],
                class_name=resolved_class["class_name"],
                row_number=row_numbers_by_class[resolved_class["id"]],
                student_password=resolved_student_password,
            )
    return {**summary, "teacher_user_id": teacher_user_id, "pruned_legacy_seed_students": pruned_legacy_seed_students}


def validate_database(payload: dict[str, Any], *, teacher_username: str | None = None, class_id: str | None = None) -> dict[str, Any]:
    teacher = payload["teacher"]
    students = [item for item in payload.get("students") or [] if isinstance(item, dict)]
    resolved_seed_classes = _resolved_classes(payload, class_id=class_id)
    if not resolved_seed_classes:
        raise ValueError("Identity seed has no classes to validate.")
    class_by_source_id = {item["source_id"]: item for item in resolved_seed_classes}
    default_source_class_id = resolved_seed_classes[0]["source_id"]
    expected_students_by_class = {item["id"]: 0 for item in resolved_seed_classes}
    for student in students:
        source_class_id = str(student.get("class_id") or default_source_class_id).strip()
        resolved_class = class_by_source_id[source_class_id]
        expected_students_by_class[resolved_class["id"]] += 1
    expected_students = len(students)
    resolved_teacher_username = teacher_username or os.getenv("SEED_TEACHER_USERNAME") or str(teacher["username"])
    resolved_class_ids = [item["id"] for item in resolved_seed_classes]
    class_id_bind = bindparam("class_ids", expanding=True)
    with db_session() as session:
        teacher_row = session.execute(
            text(
                """
                SELECT
                  EXISTS (
                    SELECT 1 FROM app_users
                    WHERE username = :teacher_username
                      AND role = 'teacher'
                      AND status = 'active'
                  ) AS teacher_ready
                """
            ),
            {"teacher_username": resolved_teacher_username},
        ).mappings().one()
        active_class_ids = {
            str(row["id"])
            for row in session.execute(
                text("SELECT id FROM classes WHERE id IN :class_ids AND status = 'active'").bindparams(class_id_bind),
                {"class_ids": tuple(resolved_class_ids)},
            ).mappings()
        }
        teacher_class_ids = {
            str(row["class_id"])
            for row in session.execute(
                text(
                    """
                    SELECT tc.class_id
                    FROM teacher_classes tc
                    JOIN app_users u ON u.id = tc.teacher_user_id
                    WHERE tc.class_id IN :class_ids
                      AND u.username = :teacher_username
                    """
                ).bindparams(class_id_bind),
                {"class_ids": tuple(resolved_class_ids), "teacher_username": resolved_teacher_username},
            ).mappings()
        }
        roster_counts = {
            str(row["class_id"]): int(row["count"] or 0)
            for row in session.execute(
                text(
                    """
                    SELECT class_id, count(*) AS count
                    FROM roster_entries
                    WHERE class_id IN :class_ids
                      AND status = 'active'
                      AND activated_user_id IS NOT NULL
                    GROUP BY class_id
                    """
                ).bindparams(class_id_bind),
                {"class_ids": tuple(resolved_class_ids)},
            ).mappings()
        }
        profile_counts = {
            str(row["class_id"]): int(row["count"] or 0)
            for row in session.execute(
                text(
                    """
                    SELECT sp.class_id, count(*) AS count
                    FROM student_profiles sp
                    JOIN app_users u ON u.id = sp.user_id
                    WHERE sp.class_id IN :class_ids
                      AND u.role = 'student'
                      AND u.status = 'active'
                    GROUP BY sp.class_id
                    """
                ).bindparams(class_id_bind),
                {"class_ids": tuple(resolved_class_ids)},
            ).mappings()
        }
        legacy_counts = {
            str(row["class_id"]): int(row["count"] or 0)
            for row in session.execute(
                text(
                    """
                    SELECT class_id, count(*) AS count
                    FROM students
                    WHERE class_id IN :class_ids
                      AND status = 'active'
                    GROUP BY class_id
                    """
                ).bindparams(class_id_bind),
                {"class_ids": tuple(resolved_class_ids)},
            ).mappings()
        }
        duplicate_row = session.execute(
            text(
                """
                SELECT count(*) AS duplicate_active_student_ids
                FROM (
                  SELECT normalized_student_id
                  FROM roster_entries
                  WHERE status <> 'disabled'
                  GROUP BY normalized_student_id
                  HAVING count(*) > 1
                ) duplicate_ids
                """
            )
        ).mappings().one()
    errors: list[str] = []
    if not teacher_row["teacher_ready"]:
        errors.append(f"seed teacher {resolved_teacher_username!r} is missing or inactive")
    missing_class_ids = [item for item in resolved_class_ids if item not in active_class_ids]
    if missing_class_ids:
        errors.append(f"seed classes missing or inactive: {', '.join(missing_class_ids)}")
    missing_teacher_class_ids = [item for item in resolved_class_ids if item not in teacher_class_ids]
    if missing_teacher_class_ids:
        errors.append(f"teacher-class ownership is missing for: {', '.join(missing_teacher_class_ids)}")
    count_sets = {
        "active_roster_entries": roster_counts,
        "active_student_profiles": profile_counts,
        "active_legacy_students": legacy_counts,
    }
    for class_id_value, expected_count in expected_students_by_class.items():
        for key, counts in count_sets.items():
            actual_count = counts.get(class_id_value, 0)
            if actual_count != expected_count:
                errors.append(f"{key} for {class_id_value}: expected {expected_count}, got {actual_count}")
    duplicate_count = int(duplicate_row["duplicate_active_student_ids"] or 0)
    if duplicate_count != 0:
        errors.append(f"duplicate active student ids: {duplicate_count}")
    return {
        "ok": not errors,
        "errors": errors,
        "summary": {
            "teacher_username": resolved_teacher_username,
            "classes": len(resolved_class_ids),
            "class_ids": resolved_class_ids,
            "students": expected_students,
            "active_roster_entries": sum(roster_counts.values()),
            "active_student_profiles": sum(profile_counts.values()),
            "active_legacy_students": sum(legacy_counts.values()),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the default teacher account, demo class, and student roster.")
    parser.add_argument("command", choices=["import", "validate", "payload"], nargs="?", default="import")
    parser.add_argument("--seed-path", type=Path, default=DEFAULT_SEED_PATH)
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--teacher-username")
    parser.add_argument("--teacher-password")
    parser.add_argument("--teacher-display-name")
    parser.add_argument("--class-id")
    parser.add_argument("--class-name")
    parser.add_argument("--student-password")
    args = parser.parse_args()

    payload = load_seed(args.seed_path)
    if args.command == "payload":
        result = validate_seed_payload(payload)
    else:
        if not args.skip_migrations:
            apply_migrations()
        if args.command == "validate":
            result = validate_database(payload, teacher_username=args.teacher_username, class_id=args.class_id)
        else:
            result = import_seed(
                payload,
                teacher_username=args.teacher_username,
                teacher_password=args.teacher_password,
                teacher_display_name=args.teacher_display_name,
                class_id=args.class_id,
                class_name=args.class_name,
                student_password=args.student_password,
                dry_run=args.dry_run,
            )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if isinstance(result, dict) and result.get("ok") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
