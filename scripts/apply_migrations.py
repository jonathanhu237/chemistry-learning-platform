from __future__ import annotations

from server.app.database import apply_migrations


def main() -> None:
    applied = apply_migrations()
    if applied:
        print("Applied migrations:")
        for version in applied:
            print(f"- {version}")
        return
    print("No pending migrations.")


if __name__ == "__main__":
    main()
