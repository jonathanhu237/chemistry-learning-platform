from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.database import apply_migrations, db_session
from server.app.security import hash_password, verify_password

DEFAULT_SEED_PATH = ROOT / "data" / "seed" / "identity" / "demo_identity_seed_v1.json"
SEED_TYPE = "demo_identity_seed"
SEED_VERSION = 1


def _json_param(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_student_id(value: str) -> str:
    return value.strip().upper()


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
    if not isinstance(payload.get("class"), dict):
        raise ValueError(f"{path} class must be an object")
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
    klass = payload.get("class") or {}
    students = payload.get("students") or []
    if not str(teacher.get("username") or "").strip():
        errors.append("teacher.username is required")
    if (teacher.get("role") or "teacher") != "teacher":
        errors.append("teacher.role must be teacher")
    if not str(klass.get("id") or "").strip():
        errors.append("class.id is required")
    if not str(klass.get("class_name") or "").strip():
        errors.append("class.class_name is required")
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
        if not str(student.get("student_name") or "").strip():
            errors.append(f"students[{index}].student_name is required")
    expected = payload.get("expected_counts") or {}
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
            "classes": 1 if isinstance(payload.get("class"), dict) else 0,
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
    teacher_user_id: str,
    class_id: str,
    class_name: str | None = None,
) -> None:
    klass = payload["class"]
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
    klass = payload["class"]
    settings = payload.get("registration_settings") or {}
    resolved_teacher_username = teacher_username or os.getenv("SEED_TEACHER_USERNAME") or str(teacher["username"])
    resolved_teacher_password = _secret_from_spec(teacher.get("password") or {}, override=teacher_password)
    resolved_class_id = class_id or os.getenv("SEED_CLASS_ID") or str(klass["id"])
    resolved_class_name = class_name or os.getenv("SEED_CLASS_NAME") or str(klass["class_name"])
    resolved_student_password = _secret_from_spec(settings.get("default_password") or {}, override=student_password)
    students = [item for item in payload.get("students") or [] if isinstance(item, dict)]
    summary = {
        "teacher_username": resolved_teacher_username,
        "class_id": resolved_class_id,
        "class_name": resolved_class_name,
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
        _upsert_class(
            session,
            payload,
            teacher_user_id=teacher_user_id,
            class_id=resolved_class_id,
            class_name=resolved_class_name,
        )
        _upsert_registration_settings(
            session,
            payload,
            teacher_user_id=teacher_user_id,
            class_id=resolved_class_id,
            student_password=resolved_student_password,
        )
        for index, student in enumerate(students, start=1):
            _upsert_student(
                session,
                payload,
                student=student,
                teacher_user_id=teacher_user_id,
                class_id=resolved_class_id,
                class_name=resolved_class_name,
                row_number=index,
                student_password=resolved_student_password,
            )
    return {**summary, "teacher_user_id": teacher_user_id}


def validate_database(payload: dict[str, Any], *, teacher_username: str | None = None, class_id: str | None = None) -> dict[str, Any]:
    teacher = payload["teacher"]
    klass = payload["class"]
    students = [item for item in payload.get("students") or [] if isinstance(item, dict)]
    expected_students = len(students)
    resolved_teacher_username = teacher_username or os.getenv("SEED_TEACHER_USERNAME") or str(teacher["username"])
    resolved_class_id = class_id or os.getenv("SEED_CLASS_ID") or str(klass["id"])
    with db_session() as session:
        row = session.execute(
            text(
                """
                SELECT
                  EXISTS (
                    SELECT 1 FROM app_users
                    WHERE username = :teacher_username
                      AND role = 'teacher'
                      AND status = 'active'
                  ) AS teacher_ready,
                  EXISTS (
                    SELECT 1 FROM classes
                    WHERE id = :class_id AND status = 'active'
                  ) AS class_ready,
                  EXISTS (
                    SELECT 1
                    FROM teacher_classes tc
                    JOIN app_users u ON u.id = tc.teacher_user_id
                    WHERE tc.class_id = :class_id
                      AND u.username = :teacher_username
                  ) AS teacher_class_ready,
                  (
                    SELECT count(*) FROM roster_entries
                    WHERE class_id = :class_id
                      AND status = 'active'
                      AND activated_user_id IS NOT NULL
                  ) AS active_roster_entries,
                  (
                    SELECT count(*)
                    FROM student_profiles sp
                    JOIN app_users u ON u.id = sp.user_id
                    WHERE sp.class_id = :class_id
                      AND u.role = 'student'
                      AND u.status = 'active'
                  ) AS active_student_profiles,
                  (
                    SELECT count(*)
                    FROM students
                    WHERE class_id = :class_id
                      AND status = 'active'
                  ) AS active_legacy_students,
                  (
                    SELECT count(*)
                    FROM (
                      SELECT normalized_student_id
                      FROM roster_entries
                      WHERE status <> 'disabled'
                      GROUP BY normalized_student_id
                      HAVING count(*) > 1
                    ) duplicate_ids
                  ) AS duplicate_active_student_ids
                """
            ),
            {"teacher_username": resolved_teacher_username, "class_id": resolved_class_id},
        ).mappings().one()
    errors: list[str] = []
    if not row["teacher_ready"]:
        errors.append(f"seed teacher {resolved_teacher_username!r} is missing or inactive")
    if not row["class_ready"]:
        errors.append(f"seed class {resolved_class_id!r} is missing or inactive")
    if not row["teacher_class_ready"]:
        errors.append("teacher-class ownership is missing")
    for key in ["active_roster_entries", "active_student_profiles", "active_legacy_students"]:
        if int(row[key] or 0) != expected_students:
            errors.append(f"{key}: expected {expected_students}, got {int(row[key] or 0)}")
    if int(row["duplicate_active_student_ids"] or 0) != 0:
        errors.append(f"duplicate active student ids: {int(row['duplicate_active_student_ids'])}")
    return {
        "ok": not errors,
        "errors": errors,
        "summary": {
            "teacher_username": resolved_teacher_username,
            "class_id": resolved_class_id,
            "students": expected_students,
            **{key: int(row[key] or 0) for key in ["active_roster_entries", "active_student_profiles", "active_legacy_students"]},
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
