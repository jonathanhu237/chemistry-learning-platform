## Context

`main` was advanced to `5e84169` and now contains the new student H5 architecture:

- periodic-table entry before chapter learning,
- current family/chapter learning pages,
- facts/experiments segmented chapter views,
- chapter experiment groups derived by chapter parent experiment and point,
- `StudentFeedbackFab` integrated with mobile overlay governance,
- `/api/student/app-config` plus feature flags for AI and feedback.

PR #2 (`origin/pr/2` at `457417e`) adds five commits:

- `77c68b1 feat: add experiment mastery analytics`
- `cf2a612 feat: add teacher analytics report drilldowns`
- `b9c57a2 feat: group teacher analytics by experiment family`
- `2f0eacd fix: render student reports with experiment mastery`
- `457417e feat: add student page feedback`

After `main` moved, PR #2 is no longer a clean conceptual merge. Local three-way analysis shows conflicts in:

- `apps/student-web/package.json`
- `apps/student-web/src/App.tsx`
- `apps/student-web/src/api.ts`
- `apps/student-web/src/styles.css`
- `apps/student-web/vite.config.ts`
- `server/app/admin_main.py`
- `server/app/services/student_learning_service.py`

The difficult conflict is not syntax. It is ownership:

- PR #2's student feedback UI was written as a separate `PageFeedback` component against the old learning routes.
- `main` already has a student feedback entry wired into the new mobile overlay system and feature flags.
- PR #2 creates a separate multipart `/api/student/feedback` router.
- `main` already owns `/api/student/feedback` inside `student_platform.py` and derives student/class identity from the authenticated token.

## Detailed Goal

Create an integration branch from current `origin/main` that merges PR #2 without regressing the student H5 architecture. The final result SHALL preserve `main` as the product and routing source of truth, while absorbing PR #2's durable capabilities:

- teacher-facing experiment mastery analytics,
- experiment-family analytics grouping,
- report drilldowns and exports,
- feedback image attachments,
- admin feedback attachment visibility,
- experiment mastery persistence from pretest/posttest,
- math-capable Markdown rendering for AI-generated report text,
- PR #2's relevant tests and frontend test tooling.

The merge is complete only when:

- there is one student feedback endpoint behavior, not duplicate route ownership,
- there is one mobile feedback entry, not two floating feedback widgets,
- student learning still opens through entry/chapter/point routes with facts/experiments tabs,
- experiment grouping remains chapter-based in the H5 learning page,
- analytics use experiment mastery without forcing the H5 page back to property-section navigation,
- tests and mobile QA demonstrate that both PR2 capabilities and current H5 flows survived.

## Goals / Non-Goals

**Goals:**

- Merge PR #2 onto current `main` through a controlled integration branch.
- Preserve current student H5 route state and visual hierarchy.
- Use current mobile primitives and overlay rules for feedback attachment UI.
- Keep authenticated student identity and feature-flag enforcement authoritative on the backend.
- Add experiment mastery as a data and analytics signal, with fallback behavior if local databases lack new tables before migrations.
- Keep PR #2 migrations numbered as `017` and `018`, because current `main` ends at `016`.
- Add or adapt tests so each merged capability is covered.

**Non-Goals:**

- Do not restore the old `home/group/experiment` H5 learning flow as the primary student surface.
- Do not introduce a second student feedback route or a second floating feedback widget.
- Do not make property sections the primary experiment video grouping again.
- Do not merge unrelated cleanup such as repository object pruning or historical mojibake cleanup outside touched code.
- Do not redesign the admin analytics UX beyond what is required to safely absorb PR #2.

## Decisions

### 1. Integrate from `main`, not from the PR branch

Create a fresh branch from current `origin/main`, then merge `origin/pr/2` into it. This keeps the new H5 architecture as the baseline and makes every conflict a conscious adaptation.

Alternative considered: update PR #2 first and then merge through GitHub. That hides the ownership decisions inside the PR branch and makes it easier to accidentally accept old student route assumptions.

### 2. Keep `student_platform.py` as the student platform router owner

`student_platform.py` already owns:

- `/api/student/app-config`,
- student feature flags,
- authenticated identity derivation,
- feedback switch enforcement,
- spoof-resistant metadata handling.

The merge should not mount PR #2's `student_feedback.py` as a second router with the same `POST /api/student/feedback` path. Instead, port its multipart form parsing and attachment handling into the existing student platform feedback handler.

The unified handler should:

- accept the current H5 feedback payload,
- support one optional image attachment,
- normalize feedback type aliases,
- reject disabled feedback by feature flag,
- strip or quarantine client-supplied student/class identity,
- create the feedback record and attachment in one logical operation,
- return a shape compatible with existing `FeedbackItem` usage plus `attachment_count`.

If backward compatibility is needed during implementation, the single handler may dispatch by `Content-Type` and accept both JSON and multipart form data. The implementation must still expose only one authoritative route handler.

### 3. Adapt PR #2 feedback UI into `StudentFeedbackFab`

Do not render PR #2's `PageFeedback` directly in the H5 app. It is not wired into current overlay coordination and was built around the old route states.

Port the useful behavior into `StudentFeedbackFab`:

- feedback type choices,
- 5 MB image validation,
- png/jpg/jpeg/webp restriction,
- screenshot picker and removable file pill,
- viewport/user-agent metadata,
- success/error states.

Keep current overlay behavior:

- AI and feedback panels remain mutually governed,
- feedback is hidden when the feature flag is disabled,
- context includes chapter, selected element, active view, experiment, point key, and page path when available.

### 4. Treat experiment mastery as an analytics and recommendation signal, not H5 navigation ownership

PR #2's `student_experiment_mastery` is valuable for analytics and recommendation. It must not replace the seed-backed current chapter model.

Integration rules:

- pretest/posttest submissions update experiment mastery from attempt rows,
- analytics may group and score experiment mastery,
- student learning recommendation may consult experiment mastery where tables exist,
- fallback remains deterministic through seed profiles, pretest area, and current profile selection if mastery data or migrations are absent,
- `chapter_experiment_groups` remains the H5 experiment view contract.

### 5. Keep admin analytics mostly additive

PR #2's admin analytics changes are mostly on the admin side and should be integrated as additive behavior:

- add TypeScript API types for experiment mastery and report drilldowns,
- add experiment family/group columns and drawer/detail views,
- update exports and report display,
- preserve existing admin routing and component ownership.

Where admin analytics depends on backend shape, backend and frontend types must be updated together.

### 6. Use PR #2 migrations as-is unless a numbering conflict appears

Current `main` ends at migration `016_student_posttest_sessions.sql`. PR #2 adds:

- `017_student_experiment_mastery.sql`
- `018_feedback_attachments.sql`

These numbers are currently valid. If a new migration lands before implementation, renumber the PR2 migrations in the integration branch and update references/tests.

### 7. Render AI report text with the math-capable Markdown path

PR #2 adds `AiMarkdown.tsx` and dependencies for `react-markdown`, `remark-gfm`, `remark-math`, and `katex`. Integrate this renderer where AI/fallback report text appears, especially posttest summaries and mistake explanations.

The renderer should support existing assistant chemistry rendering contracts. It must not force a broad UI rewrite of the student H5 screen.

## Conflict Strategy

| File | Strategy |
| --- | --- |
| `apps/student-web/package.json` | Union scripts/deps: keep `qa:mobile`; add PR2 `test`, `test:e2e`, Vitest/jsdom, Markdown/KaTeX deps. Regenerate lockfile. |
| `apps/student-web/vite.config.ts` | Keep configurable proxy target; add PR2 Vitest jsdom config. |
| `apps/student-web/src/api.ts` | Preserve current app-config and H5 learning types; extend feedback request to support attachment/FormData; add PR2 analytics/report types only where used. |
| `apps/student-web/src/App.tsx` | Keep current `entry/chapter/point/posttest/summary` route model. Port PR2 attachment and Markdown report behavior into current components. Do not restore old `group/experiment` branches. |
| `apps/student-web/src/styles.css` | Keep current mobile layout and segmented switcher styles; add attachment controls and Markdown/report styles without overlapping floating controls. |
| `server/app/admin_main.py` | Include both `student_platform_router` and any needed admin/router additions, but avoid duplicate student feedback route ownership. |
| `server/app/services/student_learning_service.py` | Keep seed/profile/chapter grouping; add optional experiment mastery recommendation signal and compatibility barriers. |

## Risks / Trade-offs

- Duplicate feedback route → Mitigation: route ownership is a required task and test; no second `POST /api/student/feedback` handler should remain.
- Old H5 route assumptions sneak back in → Mitigation: conflict resolution requires preserving current `LearningRoute` states and mobile QA must cover entry/chapter/point flows.
- Attachment support bypasses feature flags or identity hardening → Mitigation: port attachment logic into `student_platform.py`, not around it.
- Experiment mastery migration unavailable in local DB → Mitigation: recommendation and analytics reads should degrade where optional tables are absent, matching existing compatibility barriers.
- Large admin analytics merge creates type drift → Mitigation: backend response schemas, admin API types, and admin UI usage are merged together and tested.
- Frontend dependency/lockfile drift → Mitigation: update `package-lock.json` through npm after package changes, then run typecheck/build/tests.
- Mobile overlay overlap from new attachment controls → Mitigation: reuse `MobileFloatingOverlay`, `MobileButton`, and existing safe-area tokens; run 360/390/430 viewport QA.

## Migration Plan

1. Create integration branch from `origin/main`.
2. Merge `origin/pr/2` into it and resolve conflicts with the strategy above.
3. Add migrations `017` and `018` unless numbering changes before implementation.
4. Run backend tests before and after frontend integration to catch route and schema regressions.
5. Run frontend dependency install/update, then typecheck/build/tests.
6. Run mobile viewport QA.
7. Push integration branch and open a PR against `main`.

Rollback: revert the integration merge commit or close the integration PR. Because the migrations are additive, rollback before deployment is straightforward; after deployment, rollback must account for any created `student_experiment_mastery` and `feedback_attachments` rows.

## Open Questions

- Should the unified student feedback endpoint continue accepting JSON temporarily, or can student-web switch fully to multipart `FormData` immediately?
- Should PR2's `PageFeedback.tsx` be discarded after porting logic, or kept as an unused reference component for tests? Preferred answer: discard or do not add it to avoid duplicate UI ownership.
- Should experiment mastery influence the default recommended profile immediately, or only after enough evidence exists? Preferred answer: use it as an optional tie-breaker with seed/pretest fallback.
