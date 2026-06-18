## Context

This change starts immediately after commit `d0998a1 Add student bottom tab navigation shell`.

The completed `student-h5-bottom-tab-navigation` change established the current product behavior:

```text
Authenticated Student H5
├─ 学习
│  ├─ 周期表章节入口
│  ├─ 当前章节：性质通识 / 实验视频
│  └─ 实验点详情
├─ 实验
│  ├─ 实验资源总览
│  ├─ 实验组
│  └─ 实验详情
├─ 问答
│  └─ AI 学习助手整页 tab
├─ 测评
│  ├─ 完成学习后测
│  └─ 后测报告 / AI 错题讲解
└─ 我的
   ├─ 学生身份
   ├─ 反馈表单（含截图）
   └─ 退出登录
```

The implementation is now correct enough to preserve, but difficult to continue developing:

- `apps/student-web/src/App.tsx` is about 2,900 lines and contains auth, onboarding, app shell, learning, periodic table, experiments, assistant, feedback, assessment, markdown helpers, formatting helpers, and route state.
- `apps/student-web/src/styles.css` is about 2,600 lines and contains global, authenticated shell, periodic-table, learning, experiment, assistant, feedback, and assessment styles.
- `apps/student-web/src/api.ts` is about 580 lines and mixes transport primitives, auth token helpers, API types, app config, learning, experiments, assistant, feedback, and assessment requests.
- `apps/student-web/src/mobile/primitives.tsx` still exposes floating overlay primitives even though authenticated AI/feedback floating controls were intentionally removed.
- `apps/student-web/src/periodic.ts` is a generated periodic-table data module and should remain stable even if rendering logic moves.

The important constraint: this refactor exists to make later student frontend work safer. It should not change the student-visible product behavior that was just verified by:

- `npm run typecheck --prefix apps/student-web`
- `npm run test:e2e --prefix apps/student-web`
- `npm run build --prefix apps/student-web`
- `STUDENT_H5_QA_MOCK=1 npm run qa:mobile --prefix apps/student-web`
- `openspec validate student-h5-bottom-tab-navigation --strict`

## Goals / Non-Goals

**Goals:**

- Make `App.tsx` a small composition/root file instead of the owner of all student frontend behavior.
- Introduce feature module boundaries that match the current bottom-tab information architecture.
- Keep each future student feature change close to the files it owns.
- Preserve existing backend API paths, request payloads, feature flags, auth token behavior, assistant stream behavior, and feedback submission behavior.
- Preserve current mobile UX: bottom tab shell, full-page assistant tab, profile feedback, periodic-table learning entry, experiment navigation, posttest handoff, disabled feature flag behavior, and common phone viewport support.
- Move CSS toward feature-owned files while preserving current visual output and shared mobile tokens.
- Keep QA as the main safety rail, especially mobile viewport QA for 360x780, 390x844, and 430x932.
- Remove or quarantine obsolete floating overlay helpers only when no live path depends on them.

**Non-Goals:**

- No redesign of the student H5 UI.
- No conversion to React Router unless a later change proves the nested route state cannot remain simple.
- No Taro, uni-app, React Native, native mini-program package, or WebView bridge work.
- No backend refactor, migration, or endpoint rename.
- No change to OpenSpec behavioral requirements from the completed bottom-tab work.
- No test weakening to make the refactor easier.
- No broad admin-web refactor.

## Decisions

### 1. Split By Product Feature, Not By React Component Size Alone

Target structure:

```text
apps/student-web/src
├─ app/
│  ├─ App.tsx
│  ├─ StudentAppShell.tsx
│  ├─ appConfig.ts
│  └─ routes.ts
├─ features/
│  ├─ auth/
│  │  ├─ LoginPanel.tsx
│  │  ├─ PasswordPanel.tsx
│  │  └─ authUtils.ts
│  ├─ pretest/
│  │  ├─ AssessmentPanel.tsx
│  │  └─ pretestFallback.tsx
│  ├─ learning/
│  │  ├─ LearningEntryPanel.tsx
│  │  ├─ LearningHomePanel.tsx
│  │  ├─ LearningChapterHeader.tsx
│  │  ├─ LearningFactsView.tsx
│  │  ├─ LearningExperimentsView.tsx
│  │  └─ learningFormat.ts
│  ├─ periodic-table/
│  │  ├─ PeriodicTable.tsx
│  │  ├─ PeriodicElementCell.tsx
│  │  └─ periodicHelpers.ts
│  ├─ experiments/
│  │  ├─ ExperimentsOverviewPanel.tsx
│  │  ├─ ExperimentGroupPanel.tsx
│  │  ├─ ExperimentDetailPanel.tsx
│  │  └─ experimentFormat.ts
│  ├─ assistant/
│  │  ├─ StudentAiChatTab.tsx
│  │  ├─ StudentAiChatPanel.tsx
│  │  ├─ AssistantSourceSummary.tsx
│  │  └─ assistantContext.ts
│  ├─ feedback/
│  │  ├─ StudentFeedbackForm.tsx
│  │  └─ feedbackTypes.ts
│  └─ assessment/
│     ├─ PosttestPanel.tsx
│     ├─ PosttestSummaryPanel.tsx
│     └─ assessmentFormat.ts
├─ shared/
│  ├─ api/
│  │  ├─ client.ts
│  │  ├─ auth.ts
│  │  ├─ learning.ts
│  │  ├─ assistant.ts
│  │  ├─ feedback.ts
│  │  └─ assessment.ts
│  ├─ markdown/
│  ├─ mobile/
│  └─ utils/
├─ styles/
│  ├─ base.css
│  ├─ app-shell.css
│  ├─ auth.css
│  ├─ learning.css
│  ├─ periodic-table.css
│  ├─ experiments.css
│  ├─ assistant.css
│  ├─ feedback.css
│  └─ assessment.css
└─ periodic.ts
```

Rationale: this mirrors how the student app is now navigated and how future requests are likely to arrive. A “split by component size” approach would scatter related state and formatting helpers across arbitrary files.

Alternative considered: introduce React Router and route files first. Rejected for the first refactor because the current nested state is functional and the risk is not routing capability; the risk is ownership and file size.

### 2. Extract Lowest-Risk Modules First

Recommended order:

```text
1. shared pure helpers and route/config types
2. assistant feature
3. feedback feature
4. assessment feature
5. experiments feature
6. periodic-table feature
7. learning feature
8. auth/pretest surfaces
9. styles split and obsolete primitive cleanup
10. optional API domain split
```

Rationale:

- Assistant and feedback have clear boundaries after the bottom-tab migration.
- Assessment is fairly self-contained but touches AI markdown helpers.
- Experiments and learning share finish-learning/posttest handoff, so they should be split after shared route types exist.
- Periodic table has many chemistry-specific helpers and should move as one feature to avoid a half-split state.
- Auth/pretest are stable and less urgent; moving them later prevents early churn around the app root.

Alternative considered: split CSS first. Rejected because CSS class ownership follows component ownership; splitting CSS before JSX usually creates confusing temporary ownership.

### 3. Keep `App.tsx` As The Integration Point Until The End

During migration, `App.tsx` may temporarily import extracted modules. It should shrink gradually, not be rewritten wholesale.

Target responsibility for `App.tsx`:

- restore login session,
- choose top-level `ViewState`,
- mount login/password/pretest/authenticated shell,
- pass authenticated user and logout handler into `StudentAppShell`.

Target responsibility for `StudentAppShell`:

- own `StudentTab`,
- own nested route state for learning, experiments, and assessment,
- own app config polling and disabled-tab redirects,
- provide tab-level context handoff into assistant,
- orchestrate finish-learning/posttest handoff.

Rationale: this creates a stable seam before moving deeper feature internals.

Alternative considered: move all state into a global context/provider first. Rejected because there is not yet enough repeated state access to justify global indirection.

### 4. Treat CSS Split As A Mechanical Refactor With Visual QA

The first CSS split should preserve selectors and visual output. It should not rename every class.

Suggested import order in `main.tsx` or a single `styles/index.css`:

```css
@import "./base.css";
@import "./app-shell.css";
@import "./auth.css";
@import "./learning.css";
@import "./periodic-table.css";
@import "./experiments.css";
@import "./assistant.css";
@import "./feedback.css";
@import "./assessment.css";
```

Shared mobile tokens remain in `mobile/tokens.css`. Existing class names can stay until modules are stable.

Rationale: selector churn is high-risk and low-value in the same change that moves components.

Alternative considered: CSS Modules. Deferred. CSS Modules can be valuable later, but introducing them while moving every component would multiply diff size and risk.

### 5. API Split Is Optional And Must Preserve Transport Semantics

`api.ts` can be split only after feature components are separated. If split, preserve these invariants:

- `getAuthToken` / `setAuthToken` behavior stays stable.
- `api()` request error handling stays stable.
- `studentMediaUrl()` stays stable.
- `streamStudentAssistantAsk()` streaming behavior stays byte-for-byte compatible where practical.
- exported types remain importable through a compatibility barrel during the migration.

Rationale: frontend modularity can be achieved before splitting the API file. Splitting API too early creates broad import churn.

Alternative considered: leave `api.ts` forever. Acceptable for the first implementation if component/style split already reduces most friction.

### 6. Tests Must Guard Behavior, Not File Shape

The e2e and mobile QA must remain product-behavior oriented:

- login and pretest fallback,
- bottom tab visibility and disabled feature flags,
- periodic-table recommendation and selection behavior,
- chapter facts/experiments switcher,
- experiment point detail,
- assistant context handoff,
- profile feedback with screenshot add/remove/submit,
- finish-learning to posttest to report,
- 360x780 / 390x844 / 430x932 no-overlap checks.

Implementation should avoid tests that assert exact component file names. File organization is the refactor target; behavior is the stable contract.

## Risks / Trade-offs

- **Risk: Moving code changes behavior accidentally** → Mitigation: use small extraction commits or task checkpoints, run typecheck/e2e/build/mobile QA after each major feature extraction.
- **Risk: Import cycles after splitting route and feature modules** → Mitigation: define route types and shared helpers in `app/routes.ts` or `shared` before moving feature panels.
- **Risk: CSS split changes cascade order** → Mitigation: preserve original selector names and import order; use visual/mobile QA after CSS split.
- **Risk: Too many barrel exports hide ownership** → Mitigation: use barrels only for stable feature public APIs; keep internal helpers imported by explicit path inside a feature.
- **Risk: API split causes broad churn** → Mitigation: defer API split or keep `api.ts` as a compatibility barrel that re-exports domain modules.
- **Risk: The refactor becomes an excuse to redesign UI** → Mitigation: tasks explicitly forbid product behavior changes and require unchanged e2e/mobile QA behavior.
- **Risk: Obsolete floating overlay primitives are removed before hidden consumers are found** → Mitigation: search repository-wide before deletion; remove only after `rg` confirms no live imports.

## Migration Plan

1. Start from a clean worktree after commit `d0998a1`.
2. Create shared route/config/helper files without moving UI behavior.
3. Extract assistant and feedback features first, keeping tests green.
4. Extract assessment, experiments, periodic-table, and learning in that order.
5. Extract auth/pretest after the authenticated shell is stable.
6. Split styles by feature once component ownership is clear.
7. Optionally split API by domain or leave a compatibility barrel.
8. Remove obsolete floating overlay primitives only after repository-wide verification.
9. Run the full verification suite and review final diff by module boundary.

Rollback strategy: because this is behavior-preserving and frontend-only, rollback is a git revert of the refactor commit(s). No database or backend migration rollback is expected.

## Open Questions

- Should the implementation use a single `styles/index.css` that imports feature CSS, or import feature CSS from each feature entry file? The safer first option is `styles/index.css` to preserve cascade control.
- Should `api.ts` be split in this change or deferred to a follow-up? The safer first option is to defer unless component extraction reveals import pain.
- Should obsolete `MobileFloatingOverlay` primitives be deleted or moved to a future `shared/mobile/overlays.tsx`? The answer should be based on repository-wide usage after feature extraction.
