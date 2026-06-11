"""Compatibility entrypoint for admin-only deployments."""

from server.app.admin_main import app

__all__ = ["app"]
