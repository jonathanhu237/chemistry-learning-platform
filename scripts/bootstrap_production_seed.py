from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bootstrap_admin import bootstrap_user


def _run(args: list[str], *, dry_run: bool = False) -> None:
    command = [sys.executable, *args]
    if dry_run:
        print("+ " + " ".join(command))
        return
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Bootstrap a blank server with the current production seed data, including catalog point content, "
            "precomputed textbook RAG embeddings, evidence bindings, and published question banks."
        )
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--skip-es", action="store_true", help="Skip textbook RAG Elasticsearch import.")
    parser.add_argument("--es-url", default=os.getenv("TEXTBOOK_RAG_ELASTICSEARCH_URL") or os.getenv("ELASTICSEARCH_URL") or "http://127.0.0.1:9200")
    parser.add_argument("--rag-index", default=os.getenv("TEXTBOOK_RAG_ELASTICSEARCH_INDEX") or "canonical-rag-chunks-qwen-v1")
    parser.add_argument("--keep-rag-index", action="store_true", help="Do not delete/recreate the textbook RAG index first.")
    parser.add_argument("--rebuild-search-indexes", action="store_true", help="Also rebuild teacher catalog and student video search indexes.")
    parser.add_argument("--bootstrap-admin", action="store_true", help="Create/update an admin account after seeding.")
    parser.add_argument("--admin-username", default="admin")
    parser.add_argument("--admin-password", default=os.getenv("SEED_ADMIN_PASSWORD") or "123456")
    parser.add_argument("--admin-display-name", default="系统管理员")
    parser.add_argument("--admin-role", choices=["platform_admin", "admin", "teacher"], default="admin")
    args = parser.parse_args()

    if not args.skip_migrations:
        _run(["scripts/apply_migrations.py"], dry_run=args.dry_run)

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

    if args.bootstrap_admin:
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "bootstrap_admin": True,
                        "username": args.admin_username,
                        "role": args.admin_role,
                        "display_name": args.admin_display_name,
                    },
                    ensure_ascii=False,
                )
            )
        else:
            bootstrap_user(args.admin_username, args.admin_password, args.admin_display_name, args.admin_role)
            print(f"{args.admin_role} account is ready: {args.admin_username}")


if __name__ == "__main__":
    main()
