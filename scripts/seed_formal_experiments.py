from __future__ import annotations

import argparse
from pathlib import Path

from server.app.database import apply_migrations, db_session
from server.app.formal_experiments import DEFAULT_FORMAL_EXPERIMENTS_PATH, load_formal_experiment_catalog, seed_formal_experiments


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the formal experiment catalog used by experiment management.")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_FORMAL_EXPERIMENTS_PATH)
    parser.add_argument("--skip-migrations", action="store_true")
    args = parser.parse_args()

    if not args.skip_migrations:
        applied = apply_migrations()
        if applied:
            print("Applied migrations: " + ", ".join(applied))

    catalog = load_formal_experiment_catalog(args.catalog)
    with db_session() as session:
        report = seed_formal_experiments(session, catalog)
    print("Seeded formal experiments:")
    print(f"- experiments: {report['experiment_count']}")
    print(f"- chapter bindings: {report['binding_count']}")
    if report["missing_chapters"]:
        print("- missing chapters: " + ", ".join(report["missing_chapters"]))


if __name__ == "__main__":
    main()
