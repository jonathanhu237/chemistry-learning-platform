from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REDACT_VALUE_AFTER = {
    "--admin-password",
    "--teacher-password",
    "--student-password",
}


def _display_command(command: list[str]) -> str:
    redacted: list[str] = []
    skip_next = False
    for item in command:
        if skip_next:
            redacted.append("***")
            skip_next = False
            continue
        redacted.append(item)
        if item in REDACT_VALUE_AFTER:
            skip_next = True
    return " ".join(redacted)


def _run(args: list[str], *, dry_run: bool = False) -> None:
    command = [sys.executable, *args]
    if dry_run:
        print("+ " + _display_command(command), flush=True)
        return
    subprocess.run(command, cwd=ROOT, check=True)


def _append_arg(args: list[str], flag: str, value: str | None) -> None:
    if value is not None and value != "":
        args.extend([flag, value])


def _append_path_arg(args: list[str], flag: str, value: Path | None) -> None:
    if value is not None:
        args.extend([flag, str(value)])


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Bootstrap a blank server with current production seed data: demo identities, catalog point content, "
            "videos, precomputed textbook RAG embeddings, evidence bindings, and published question banks."
        )
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--skip-identities", action="store_true", help="Skip teacher/class/student demo identity seed.")
    parser.add_argument("--skip-assessments", action="store_true", help="Skip simulated demo student assessment data.")
    parser.add_argument("--skip-media", action="store_true", help="Skip experiment video media restore/import.")
    parser.add_argument("--skip-es", action="store_true", help="Skip textbook RAG Elasticsearch import.")
    parser.add_argument("--skip-validation", action="store_true", help="Skip final complete seed validation.")
    parser.add_argument("--es-url", default=os.getenv("TEXTBOOK_RAG_ELASTICSEARCH_URL") or os.getenv("ELASTICSEARCH_URL") or "http://127.0.0.1:9200")
    parser.add_argument("--rag-index", default=os.getenv("TEXTBOOK_RAG_ELASTICSEARCH_INDEX") or "canonical-rag-chunks-qwen-v1")
    parser.add_argument("--keep-rag-index", action="store_true", help="Do not delete/recreate the textbook RAG index first.")
    parser.add_argument("--rebuild-search-indexes", action="store_true", help="Also rebuild teacher catalog and student video search indexes.")
    parser.add_argument("--teacher-username", default=os.getenv("SEED_TEACHER_USERNAME"))
    parser.add_argument("--teacher-password", default=os.getenv("SEED_TEACHER_PASSWORD"))
    parser.add_argument("--teacher-display-name", default=os.getenv("SEED_TEACHER_DISPLAY_NAME"))
    parser.add_argument("--class-id", default=os.getenv("SEED_CLASS_ID"))
    parser.add_argument("--class-name", default=os.getenv("SEED_CLASS_NAME"))
    parser.add_argument("--student-password", default=os.getenv("SEED_STUDENT_PASSWORD"))
    parser.add_argument("--media-root", type=Path, default=Path(os.getenv("MEDIA_ROOT")) if os.getenv("MEDIA_ROOT") else None)
    parser.add_argument(
        "--replace-existing-video-bindings",
        action="store_true",
        help="Allow media seed import to archive non-seed active point-video bindings.",
    )
    args = parser.parse_args()

    if not args.skip_migrations:
        _run(["scripts/apply_migrations.py"], dry_run=args.dry_run)

    if not args.skip_identities:
        identity_step = ["scripts/seed_demo_identities.py", "import", "--skip-migrations"]
        if args.dry_run:
            identity_step.append("--dry-run")
        _append_arg(identity_step, "--teacher-username", args.teacher_username)
        _append_arg(identity_step, "--teacher-password", args.teacher_password)
        _append_arg(identity_step, "--teacher-display-name", args.teacher_display_name)
        _append_arg(identity_step, "--class-id", args.class_id)
        _append_arg(identity_step, "--class-name", args.class_name)
        _append_arg(identity_step, "--student-password", args.student_password)
        _run(identity_step, dry_run=False)

    steps = [
        ["scripts/publish_reviewed_curriculum.py", "--skip-migrations"],
        ["scripts/seed_formal_experiments.py", "--skip-migrations"],
        ["scripts/import_canonical_evidence.py", "--skip-migrations"],
        ["scripts/import_experiment_knowledge_framework.py", "--skip-migrations"],
        ["scripts/import_experiment_catalog_seed.py", "--skip-migrations"],
        ["scripts/seed_full_catalog_point_content.py", "import", "--skip-migrations"],
        ["scripts/seed_catalog_point_evidence.py", "import", "--skip-migrations"],
        ["scripts/seed_current_question_bank.py", "import", "--skip-migrations"],
    ]
    for step in steps:
        _run(step, dry_run=args.dry_run)

    if not args.skip_assessments:
        _run(["scripts/seed_demo_student_assessments.py", "import", "--skip-migrations"], dry_run=args.dry_run)

    if not args.skip_media:
        media_step = ["scripts/seed_experiment_videos.py", "import", "--skip-migrations"]
        if args.dry_run:
            media_step.append("--dry-run")
        _append_path_arg(media_step, "--media-root", args.media_root)
        if args.replace_existing_video_bindings:
            media_step.append("--replace-existing-bindings")
        _run(media_step, dry_run=False)

    if not args.skip_es:
        es_step = [
            "scripts/import_precomputed_textbook_rag.py",
            "--es-url",
            args.es_url,
            "--index",
            args.rag_index,
        ]
        if not args.keep_rag_index:
            es_step.append("--recreate")
        _run(es_step, dry_run=args.dry_run)

    if args.rebuild_search_indexes:
        _run(["scripts/rebuild_teacher_catalog_search_index.py", "--recreate"], dry_run=args.dry_run)
        _run(["scripts/rebuild_video_library_index.py", "--recreate"], dry_run=args.dry_run)

    if not args.skip_validation:
        validation_step = ["scripts/validate_complete_seed_bootstrap.py"]
        _append_path_arg(validation_step, "--media-root", args.media_root)
        _append_arg(validation_step, "--teacher-username", args.teacher_username)
        _append_arg(validation_step, "--class-id", args.class_id)
        _run(validation_step, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
