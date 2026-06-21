## Context

The authenticated student H5 surface is currently implemented mostly inside `apps/student-web/src/App.tsx`.

Current shape:

```text
App
├─ brand-rail: SYSU / chemistry college / element experiment
├─ login / password / pretest surfaces
└─ LearningSurface
   ├─ route: entry | chapter | point | posttest | summary
   ├─ app-config polling
   ├─ LearningEntryPanel
   ├─ LearningHomePanel
   │  ├─ learning-topbar: student id/name/logout
   │  ├─ LearningChapterHeader
   │  ├─ ChapterViewSwitcher: facts / experiments
   │  ├─ facts or experiment-point content
   │  ├─ StudentAiChat floating overlay
   │  └─ StudentFeedbackFab floating overlay
   ├─ ExperimentDetailPanel
   ├─ PosttestPanel
   └─ PosttestSummaryPanel
```

Important constraints already present in specs and code:

- The student app remains React + Vite H5, not a native mini-program rewrite.
- `getStudentAppConfig()` already exposes assistant and feedback feature flags.
- `streamStudentAssistantAsk()` already supports student assistant streaming with optional context.
- `submitStudentFeedback()` already supports authenticated feedback with optional image attachment.
- Backend assistant context supports `learning_home`, `learning_profile`, `learning_point`, `experiment_group`, and `experiment_detail`, so a global assistant tab can use `learning_home` without a new backend route.
- Existing mobile QA expects floating `.ai-chat-toggle` and `.feedback-toggle`; those checks must be rewritten.
- Admin has a full learning assistant workbench at `apps/admin-web/src/features/learning-assistant/LearningAssistantPage.tsx` with status chips, starter choices, chat turns, a composer, streaming status, source summaries, and diagnostics. The student version should borrow the page-as-workbench idea, but not the admin-only diagnostics density.

The product direction from exploration:

```text
Authenticated Student H5 App
├─ 学习
│  ├─ 周期表入口
│  ├─ 当前/推荐章节
│  ├─ 章节详情：性质通识 / 实验视频
│  └─ 实验点详情
├─ 实验
│  ├─ 实验资源 / 点位总览
│  └─ 实验详情
├─ 问答
│  └─ AI 学习助手 full-page chat
├─ 测评
│  ├─ 课前摸底 / 学习后测入口
│  └─ 报告 / 错题讲解
└─ 我的
   ├─ 学生信息
   ├─ 反馈（含截图）
   ├─ 修改密码 / 退出登录
   └─ 后续可承接班级、进度、设置
```

## Goals / Non-Goals

**Goals:**

- Make the authenticated student H5 feel like a mobile app with a stable bottom navigation bar.
- Remove global floating AI and feedback controls from the authenticated app shell.
- Put AI in a dedicated `问答` tab based on the admin learning assistant's workbench concept, adapted to phone width and student needs.
- Put feedback in `我的`, with screenshot upload as the expected way to report page-specific problems.
- Keep chapter-local controls, especially `性质通识 / 实验视频`, visually tied to the current chapter instead of treating them as global navigation.
- Preserve existing backend APIs and feature switches.
- Update tests and mobile viewport QA to verify the new navigation model.

**Non-Goals:**

- No Taro, uni-app, React Native, or WeChat native mini-program package.
- No new database tables or migrations.
- No broad redesign of admin pages.
- No automatic screenshot capture of the current page.
- No replacement of chemistry-specific learning content with a generic mobile UI library.
- No new public backend route unless implementation finds an unavoidable gap.

## Decisions

### 1. Authenticated Shell Owns App-Level Navigation

Create a student app shell for authenticated pages, with bottom tabs as the only global navigation surface. The large brand rail remains appropriate for login/onboarding but not for every authenticated page.

Recommended route model:

```ts
type StudentTab = "learn" | "experiments" | "assistant" | "assessment" | "profile";

type LearningRoute =
  | { screen: "entry" }
  | { screen: "chapter"; profileId: string; ... }
  | { screen: "point"; profileId: string; ... };

type StudentAppRoute = {
  tab: StudentTab;
  learning: LearningRoute;
  assessment?: AssessmentRoute;
  experiment?: ExperimentRoute;
};
```

Rationale: the current `LearningRoute` is useful for chapter/point depth, but it is too narrow to represent app-level destinations. Keeping nested route state avoids introducing React Router solely for this refactor.

Alternative considered: keep one page and add a sticky header only. Rejected because it does not solve the user's app-wide concern, does not remove floating controls, and leaves AI/feedback as afterthoughts.

### 2. Bottom Nav Is Stable, Safe-Area Aware, And Phone-Sized

The bottom bar uses five touch targets when all features are enabled:

- `学习`
- `实验`
- `问答`
- `测评`
- `我的`

Use familiar icons from the existing icon library. The bar is fixed to the bottom safe area, reserves page padding, and never overlaps forms, posttest actions, video controls, or point cards.

Feature flags affect entries:

- If assistant entry or student AI capability is disabled, `问答` is not available as an entry.
- If the current tab becomes unavailable after app-config refresh, route back to `学习` and show a small non-blocking status message.
- If feedback is disabled, the feedback section in `我的` is hidden or replaced with a disabled explanation; no stale client submission should succeed.

Alternative considered: keep `问答` visible but disabled. This preserves tab count, but contradicts existing specs that say disabled entries are hidden after config refresh. Hidden/redirect is the safer first implementation.

### 3. Header Becomes Mobile App Context, Not Institutional Branding

Each tab gets a compact top app header. It may show:

- current destination title,
- student identity or a short greeting,
- contextual secondary action such as logout only inside `我的`,
- current chapter summary inside learning detail pages.

The chapter page should not scroll into a state where only `性质通识 / 实验视频` remains visible with no chapter context. The segmented switcher can stay sticky, but it must be visually attached to a compact current-chapter header or context strip.

Alternative considered: keep the full SYSU brand header on all authenticated pages. Rejected because it consumes the first viewport and reads like a desktop landing page, not a mobile app.

### 4. AI Becomes A Full `问答` Tab

Refactor `StudentAiChat` into:

```text
StudentAiChatPanel   pure chat/workbench content
StudentAiChatTab     page/tab wrapper with default context
ContextHandoff       optional learning/point context prefill
```

The student `问答` tab should borrow from the admin learning assistant:

- clear page title and status,
- starter prompts or context choices,
- chat turn list,
- streaming progress,
- composer fixed within the tab content,
- compact source/evidence summary.

It must not carry over admin-only diagnostics such as raw JSON traces, policy internals, or dense inspector panels unless later explicitly requested.

Default assistant context:

```ts
{
  context_type: "learning_home",
  context_title: "AI 学习助手",
  context_summary: "学生端全局课程问答入口"
}
```

When launched from chapter or point context, the tab may receive optional context and present it as a dismissible context chip, while still letting the student ask general course questions.

### 5. Feedback Moves To `我的`

Refactor `StudentFeedbackFab` into:

```text
StudentFeedbackForm  pure form with screenshot attachment
ProfileTab           student info + feedback + account actions
```

Feedback is not a current-page floating widget. If students encounter a page problem, they can open `我的`, describe the issue, and attach a screenshot. The form may include a route/page hint if available, but the product no longer depends on a per-page feedback entry.

Rationale: this removes two competing global controls from the learning page and gives feedback a predictable account/support home.

Alternative considered: keep floating feedback but hide it under bottom nav. Rejected because it continues the overlap problem and keeps the app feeling like patched web pages.

### 6. `实验` And `测评` Can Start As Thin Tabs

The first implementation does not need new backend contracts.

- `实验` can surface existing experiment resources and point groups from current learning payloads or `getStudentLearningHome()`, then navigate into existing experiment group/detail components.
- `测评` can host pretest/posttest entry, current learning completion handoff, and report entry points, reusing existing posttest and summary panels.

The key requirement is navigational clarity, not a complete new content model in one step.

### 7. Tests Must Change From Floating Controls To App Navigation

Update e2e and mobile QA expectations:

- bottom nav is visible after login and on authenticated tabs,
- tab labels fit 360/390/430 CSS-pixel widths,
- `问答` opens a full-page assistant surface,
- `我的` exposes feedback with screenshot attachment,
- no `.ai-chat-toggle` or `.feedback-toggle` is expected on learning pages,
- chapter switcher remains local and does not overlap bottom nav,
- assessment actions remain reachable above the tab bar.

## Risks / Trade-offs

- Active learning state may reset when switching tabs -> keep nested route state in the app shell and avoid remounting learning route unnecessarily.
- Hidden assistant tab can change bottom-nav item widths -> design the nav as equal-width over the available item count and test at 360px.
- Chat composer and mobile keyboard can conflict with fixed bottom nav -> assistant tab must reserve bottom padding and use keyboard-aware layout rules.
- Moving feedback to `我的` may reduce immediacy -> screenshot attachment and optional route metadata preserve enough reporting context without a floating widget.
- Reusing admin assistant patterns could make the student UI too dense -> borrow structure and behavior, not admin diagnostics.
- `实验` and `测评` tabs may be initially thinner than `学习` -> make them honest entry surfaces and avoid placeholder marketing content.

## Migration Plan

1. Create the authenticated app shell and bottom nav while keeping existing login, password, and pretest onboarding outside the shell.
2. Move current learning entry/chapter/point/posttest/summary flows under the `学习` and `测评` tabs without backend changes.
3. Split AI chat into panel/tab components and remove authenticated floating AI entry.
4. Split feedback into form/profile components and remove authenticated floating feedback entry.
5. Update CSS tokens for bottom nav, safe-area padding, and compact tab headers.
6. Update tests and mobile QA scripts.
7. Remove obsolete floating overlay CSS once no authenticated surface uses it.

Rollback is straightforward because backend APIs remain unchanged: revert the frontend shell refactor and restore the previous floating component wrappers if needed.

## Open Questions

- Should `实验` initially list all available experiment resources, only current/recommended chapter experiments, or both with filtering?
- Should `测评` show posttest only after a chapter is completed, or always show current assessment state and guidance?
- Should the bottom nav include a disabled placeholder for `问答` when AI is disabled, or fully hide it as current feature-switch specs imply?
- Should profile feedback store an explicit `page_path` from the last active tab, or only use `/student/profile/feedback` plus screenshot and free text?
