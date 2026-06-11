from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.curriculum import create_curriculum_draft, load_curriculum_artifact, publish_curriculum_version
from server.app.database import apply_migrations

DEFAULT_CURRICULUM = ROOT / "data" / "processed" / "reviewed_curriculum.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and publish the reviewed KC/KP curriculum version.")
    parser.add_argument("--curriculum", type=Path, default=DEFAULT_CURRICULUM)
    parser.add_argument("--draft-only", action="store_true")
    parser.add_argument("--skip-migrations", action="store_true")
    args = parser.parse_args()

    if not args.skip_migrations:
        apply_migrations()
    draft = create_curriculum_draft(load_curriculum_artifact(args.curriculum))
    print(f"Draft curriculum version: {draft['id']} ({draft['version_code']})")
    if args.draft_only:
        return
    published = publish_curriculum_version(str(draft["id"]))
    print(f"Published curriculum version: {published['id']} ({published['version_code']})")


if __name__ == "__main__":
    main()
