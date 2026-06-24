## Context

The teacher console creates student preview sessions through the backend. The backend returns a `preview_url` that is loaded into the teacher preview iframe. Today both the Compose backend environment and backend settings default point that URL at `http://127.0.0.1:5173`, while the student container can be published through a different host bind address.

The teacher preview frontend also validates the returned iframe origin before rendering it. That validation must use the same configured student app base as the backend-generated URL.

The current debugging need is to make the teacher preview layer use the same reachable student frontend origin as real phone testing: `http://222.200.189.249:5173`.

## Goals / Non-Goals

**Goals:**

- Make `web-student` publish by default on `222.200.189.249:5173` in the local Compose stack.
- Make teacher student-preview session URLs default to `http://222.200.189.249:5173`.
- Add the LAN student origin to preview-origin validation and backend frontend-origin allowlists.
- Make the teacher preview URL validator expect the LAN student origin by default.
- Preserve environment-variable overrides so another developer or deployment can choose a different bind address.
- Recreate the affected containers so the running preview stack uses the new defaults.

**Non-Goals:**

- Do not change the student learning popover behavior in this change.
- Do not expose Postgres, Elasticsearch, or admin/teacher frontends on the LAN address.
- Do not remove localhost support from example allowlists where it is useful for development.

## Decisions

### Decision: Use the configured LAN origin as the default preview origin

Set `STUDENT_PREVIEW_APP_BASE_URL` to `http://222.200.189.249:5173` in Compose and backend defaults.

Rationale: teacher preview needs an iframe URL that works from the teacher preview shell and matches the reachable student container. A loopback-only URL makes the preview path environment-dependent and masks iframe/input issues.

Alternative considered: keep backend defaults on loopback and require manual `.env` override. Rejected because the user explicitly needs this workspace's default container start to use the LAN preview address.

### Decision: Keep environment overrides

Use `${...:-...}` Compose defaults and `.env` entries instead of hardcoding every environment.

Rationale: the current machine uses `222.200.189.249`, but another environment may need a different LAN IP or a deployed hostname.

### Decision: Do not widen preview framing to arbitrary origins

Add only the specific LAN student origin to allowed origins.

Rationale: preview framing is a clickjacking-sensitive boundary. Fixing the local preview target should not turn the teacher console into a general iframe host.

## Risks / Trade-offs

- [Risk] The LAN IP changes. -> Mitigation: operators can override `WEB_STUDENT_HOST_BIND`, `STUDENT_PREVIEW_APP_BASE_URL`, and `STUDENT_PREVIEW_ALLOWED_ORIGINS` in `.env`.
- [Risk] Teacher preview is opened from a different teacher origin. -> Mitigation: keep the existing teacher frame ancestors and update only the student preview origin; add further teacher origins only when the teacher service is intentionally exposed.
- [Risk] Existing tests that assume loopback URLs become stale. -> Mitigation: update configuration-sensitive tests or keep them focused on URL mechanics rather than a specific host unless the default is being asserted.

## Migration Plan

1. Update Compose and env defaults.
2. Update backend settings defaults.
3. Update OpenSpec deltas.
4. Validate OpenSpec and targeted tests.
5. Recreate backend and `web-student` containers so the new preview URL and port binding are active.

Rollback: set `.env` back to loopback values and run `docker compose up -d --force-recreate backend web-student`.
