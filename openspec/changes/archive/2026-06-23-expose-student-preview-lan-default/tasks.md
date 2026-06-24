## 1. Configuration Defaults

- [x] 1.1 Update Compose defaults so `web-student` publishes on `222.200.189.249:5173`.
- [x] 1.2 Update backend preview-session defaults and env files so generated student preview URLs use `http://222.200.189.249:5173`.
- [x] 1.3 Add the LAN student origin to frontend and preview allowed-origin defaults without removing override support.
- [x] 1.4 Update teacher preview URL validation so the LAN student origin is the default expected iframe origin.

## 2. Verification And Runtime

- [x] 2.1 Validate the OpenSpec change.
- [x] 2.2 Run focused backend/settings or source checks for preview URL configuration.
- [x] 2.3 Recreate affected containers and verify `web-student` is reachable at `http://222.200.189.249:5173`.
