from __future__ import annotations

import argparse
import getpass

from sqlalchemy import text

from server.app.infrastructure.database import apply_migrations, db_session
from server.app.security import hash_password


def bootstrap_user(username: str, password: str, display_name: str, role: str) -> None:
    password_hash = hash_password(password)
    with db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO app_users (
                  username, role, display_name, password_hash, status,
                  must_change_password, password_version, metadata
                )
                VALUES (
                  :username, :role, :display_name, :password_hash, 'active',
                  false, 1, '{}'::jsonb
                )
                ON CONFLICT (username) DO UPDATE SET
                  role = EXCLUDED.role,
                  display_name = EXCLUDED.display_name,
                  password_hash = EXCLUDED.password_hash,
                  status = 'active',
                  must_change_password = false,
                  password_version = app_users.password_version + 1,
                  updated_at = now()
                """
            ),
            {
                "username": username,
                "role": role,
                "display_name": display_name,
                "password_hash": password_hash,
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a local platform-admin or teacher-console account.")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--display-name", default="系统管理员")
    parser.add_argument("--role", choices=["platform_admin", "admin", "teacher"], default="admin")
    parser.add_argument("--password", help="If omitted, prompts securely.")
    parser.add_argument("--skip-migrations", action="store_true")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password: ")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    if not args.skip_migrations:
        apply_migrations()
    bootstrap_user(args.username, password, args.display_name, args.role)
    print(f"{args.role} account is ready: {args.username}")


if __name__ == "__main__":
    main()
