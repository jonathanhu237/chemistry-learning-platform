## Why

Teacher student preview currently depends on a student iframe URL that defaults to `127.0.0.1:5173`. That works only from the host machine and makes the preview shell diverge from the real phone path, so desktop preview cannot reliably replace phone debugging.

## What Changes

- Default the Compose-published student frontend to `222.200.189.249:5173`.
- Default teacher student-preview session URLs to `http://222.200.189.249:5173`.
- Allow the LAN student preview origin in backend CORS and preview-origin validation.
- Keep all addresses configurable through environment variables for other machines or deployments.
- Update documentation/spec contracts so future container starts preserve the LAN-accessible default.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-student-device-preview`: Clarifies that preview URLs must resolve to the configured LAN-accessible student frontend origin, not a loopback-only origin.
- `production-engineering-quality`: Clarifies that the default `web-student` Compose publishing target includes both host bind address and port.

## Impact

- Compose configuration: `docker-compose.yml`, `.env`, `.env.example`.
- Backend settings defaults: student-preview base URL and allowed origins.
- OpenSpec contracts for teacher preview and production engineering quality.
- Container lifecycle: backend and student frontend must be recreated after configuration changes.
