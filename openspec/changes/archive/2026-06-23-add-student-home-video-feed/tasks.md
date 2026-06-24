## 1. Backend Feed Contract

- [x] 1.1 Add student home video feed response schemas with playable media, catalog path, badges, route target, and feed reason fields.
- [x] 1.2 Implement a backend read model that selects only published point placements with published point content, published ancestors, and an active ready video binding.
- [x] 1.3 Expose `GET /api/student/home-video-feed` under the authenticated student API and keep media resource fields out of the video-library search index.

## 2. Student H5 Feed UI

- [x] 2.1 Add student H5 API types and a `getStudentHomeVideoFeed` client helper.
- [x] 2.2 Replace the current home hero/action hub with loading, error, empty, and feed states for the home video stream.
- [x] 2.3 Render single-column 16:9 feed cards with poster/video preview, title, catalog path, badges, detail navigation, search action, and AI action.
- [x] 2.4 Implement one-active-card muted inline preview behavior using viewport visibility, with graceful fallback when autoplay fails.
- [x] 2.5 Add mobile CSS so feed cards keep stable dimensions, avoid horizontal overflow, and clear the bottom navigation safe area.

## 3. Tests And Validation

- [x] 3.1 Update student H5 e2e mocks and tests for the new home feed API, card rendering, point-detail navigation, video-library search entry, and single-active-video behavior.
- [x] 3.2 Add or update backend/API coverage for feed filtering and playable media response shape where practical.
- [x] 3.3 Run OpenSpec validation plus the relevant frontend/backend typecheck and test commands.
