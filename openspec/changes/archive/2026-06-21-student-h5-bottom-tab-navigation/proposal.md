## Why

The authenticated student H5 currently behaves like a single long web page: it keeps the large chemistry-college brand rail on learning screens, relies on floating AI and feedback controls, and lets local chapter controls become the only visible navigation after scroll. This does not match a phone-first learning app, where students need stable bottom navigation, persistent current context, and clear destinations for learning, experiments, AI, assessment, and profile actions.

This change turns the student H5 into a mobile app shell while preserving the current React/Vite H5 deployment path and existing backend contracts.

## What Changes

- Add an authenticated bottom tab navigation shell for the student H5 app.
- Organize the app around five phone-first destinations: `学习`, `实验`, `问答`, `测评`, and `我的`.
- Remove the large `中山大学化学学院 / 元素实验` brand rail from authenticated app pages; keep institutional branding for login and onboarding surfaces where it is useful.
- Move AI from the floating `问 AI` entry into a dedicated `问答` tab that references the admin learning assistant workbench pattern, adapted for students and phones.
- Move feedback out of the floating page feedback control and into `我的`; students can attach or upload screenshots when reporting issues instead of relying on a per-page feedback widget.
- Keep contextual learning handoffs: learning or experiment pages may still pass chapter/experiment/point context into the assistant, but the primary assistant surface is the `问答` tab.
- Keep chapter-local controls local: the facts/experiments switcher remains a chapter control, while the bottom nav owns app-level navigation.
- **BREAKING (UI):** authenticated student pages no longer expose floating AI or floating feedback buttons as global controls.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-platform-shell`: define the authenticated mobile app shell and bottom tab navigation ownership.
- `student-h5-mobile-design-system`: add bottom nav, safe-area, sticky header, and no-floating-entry interaction rules.
- `student-h5-learning-experience`: define the new app information architecture, remove the authenticated brand rail, and move feedback/profile responsibilities.
- `student-chat-guardrails`: change student assistant presentation from floating chat to a full `问答` tab while keeping guardrails and context.
- `ai-access-configuration`: clarify how admin feature switches hide or disable bottom-nav assistant and profile feedback entries.

## Impact

- `apps/student-web/src/App.tsx`: split the current linear `LearningRoute` surface into an authenticated app shell with tab-level routing; refactor `StudentAiChat` and `StudentFeedbackFab` into reusable panel/form components.
- `apps/student-web/src/styles.css`: add bottom tab layout tokens, safe-area spacing, app header rules, and remove obsolete floating AI/feedback positioning from the authenticated shell.
- `apps/student-web/src/api.ts`: no new backend API is expected; continue using app config, assistant streaming, learning payload, posttest, and feedback submission endpoints.
- `apps/student-web/src/App.e2e.test.tsx` and `apps/student-web/scripts/mobile-viewport-qa.mjs`: update tests from floating entry expectations to bottom-tab navigation and profile feedback flows.
- `server/app/student_assistant_schemas.py` and `server/app/services/student_assistant_service.py`: no required backend change is expected because `learning_home` and optional chapter/experiment/point context already support a global assistant tab.
- `server/app/routers/student_platform.py`: no required route change is expected because screenshot feedback already supports authenticated identity, metadata, page path, and optional image attachment.
