## Context

The authenticated student H5 app currently keeps app navigation in React component state inside `StudentAppShell`. It has tab state plus nested route-like state:

```text
activeTab = learn | experiments | assistant | assessment | profile
learningRoute = entry | chapter | point
experimentRoute = overview | group | detail
assessmentRoute = home | posttest | summary
```

This made the first bottom-nav iteration possible, but it now conflicts with the desired mini-program mental model:

- Root tabs should be stable top-level destinations.
- Page-local actions should not silently switch the active bottom tab.
- Shared detail pages should be opened from several roots, hide the bottom navigation, and return to the source root.
- The AI chat page should be reachable both as the center AI destination and as contextual AI from home or learning without changing tab identity.
- The codebase needs page boundaries that are easy to optimize independently.

The project is React + Vite H5, not a native WeChat mini-program package. We should emulate the mini-program route stack in the SPA: tab roots behave like tabBar pages, and second-level pages behave like non-tabBar pages opened by `navigateTo`.

## Goals / Non-Goals

**Goals:**

- Introduce a real route model using `@tanstack/react-router`.
- Define five first-level root tabs: `home`, `learn`, `ai`, `assessment`, `profile`.
- Define P0 second-level pages:
  - chapter learning
  - experiment point/video detail
  - AI chat
  - assessment session
  - assessment report
  - feedback
- Make detail pages hide the bottom navigation.
- Preserve source-aware back behavior for shared detail pages.
- Reorganize frontend modules so root pages, detail pages, shared feature components, and app shell concerns are separate.
- Remove the current state-driven shell/page structure rather than wrapping it with a router compatibility layer.
- Keep backend APIs unchanged for P0.

**Non-Goals:**

- No native WeChat mini-program rewrite.
- No Taro, uni-app, or React Native migration.
- No P1 page expansion yet, including experiment group detail, dedicated mistake review, atom full-screen page, or settings detail.
- No requirement to perfectly reproduce native iOS/Android edge-swipe animations in P0.
- No new backend tables or migrations.
- No redesign of admin pages.

## Decisions

### 1. Use `@tanstack/react-router`

Use `@tanstack/react-router` for the student H5 router.

Rationale:

- Current `@tanstack/react-router` supports the project's Node range (`>=20.19`).
- It gives typed params/search, nested layouts, route matching, and history integration.
- We need source-aware detail routes, not only component toggles.
- Latest React Router currently requires a higher Node baseline; React Router v7 is viable but less compelling than TanStack for typed search/context in this app.
- `wouter` is too thin for the planned route stack and page organization.

Alternative considered: keep a custom reducer/router. Rejected because browser back, refresh, deep links, layout nesting, and typed page params would become long-term custom infrastructure.

### 2. Split Roots And Details

The route tree should distinguish first-level root tabs from second-level task pages.

Recommended route shape:

```text
/
  authenticated app layout
    /home
    /learn
    /ai
    /assessment
    /profile
    /chapter/$profileId
    /point/$experimentId
    /ai/chat
    /assessment/session/$sessionId
    /assessment/report/$sessionId
    /feedback/new
```

Root routes show or may transiently compress the bottom navigation. Detail routes hide it by default.

The center `AI` root is an AI center, not the only way to open chat:

```text
/ai                 AI root: new chat, history, suggested prompts
/ai/chat            shared detail page: actual conversation surface
```

Similarly:

```text
/learn              learning root: chapter selection, periodic table, search
/chapter/$profileId shared detail page: current chapter learning content
```

### 3. Source-Aware Back Behavior

When a root opens a detail page, the current history entry should preserve the source naturally through browser history. Search parameters may also carry explicit source metadata when needed:

```text
/chapter/halogens-17?from=home
/ai/chat?from=learn&context=...
/assessment/session/abc?from=chapter
```

The preferred P0 behavior is:

- opening a detail page pushes a route;
- browser back, Android back, WebView back, and explicit page back all return to the previous root/detail entry;
- the bottom navigation returns when the visible route is a root route;
- no page-local action calls `setActiveTab`.

Explicit `from` search is useful for analytics, fallback back buttons, and direct deep-link display copy, but it should not replace browser history.

### 4. Navigation Visibility Is Route-Driven With Root Scroll Enhancements

Navigation visibility has two levels:

- Route-level visibility: root routes are eligible for the bottom navigation; detail routes hide it.
- Interaction-level visibility: root routes may hide or compress the bottom navigation while scrolling down and restore it when scrolling up or returning from detail.

P0 must implement route-level visibility. Root scroll auto-hide can be implemented in the same shell if simple, but it must not blur route identity:

```text
Root route + scrolling down     -> nav may collapse/hide
Root route + scroll up/idle     -> nav reappears
Detail route                    -> nav hidden regardless of scroll
Detail back to root             -> nav restores quickly
```

This mirrors common app behavior: hiding navigation for more content is acceptable on roots, but detail pages are a stronger mode with no tab bar.

### 5. Reorganize Frontend By Route Boundary

Move from feature-only panels mounted by `StudentAppShell` to route-first pages that compose feature components.

Recommended structure:

```text
apps/student-web/src/
  app/
    router/
      router.tsx
      routeTypes.ts
      navigation.ts
    shell/
      AuthenticatedAppLayout.tsx
      StudentBottomNav.tsx
      DetailPageFrame.tsx
      routeVisibility.ts
  routes/
    home/
      HomeRootPage.tsx
    learn/
      LearnRootPage.tsx
      ChapterStudyPage.tsx
      ExperimentPointPage.tsx
    ai/
      AiRootPage.tsx
      AiChatPage.tsx
    assessment/
      AssessmentRootPage.tsx
      AssessmentSessionPage.tsx
      AssessmentReportPage.tsx
    profile/
      ProfileRootPage.tsx
      FeedbackPage.tsx
  features/
    learning/
    experiments/
    assistant/
    assessment/
    feedback/
```

Route pages own loading route params, shell visibility, page-level layout, and handoff decisions. Feature components remain reusable content blocks.

### 6. Replace The Existing Shell And Directory Shape

This refactor should be structural, not a compatibility wrapper.

The existing `StudentAppShell` is allowed to be used as a temporary reference during implementation, but the target architecture must remove its role as the owner of all authenticated navigation. The final implementation should not keep parallel navigation systems such as:

```text
TanStack route tree
+ StudentAppShell activeTab
+ learningRoute / experimentRoute / assessmentRoute screen state
```

The same applies to the directory structure. Current feature folders may keep reusable UI, formatting helpers, API-facing components, and domain utilities, but route ownership must move into route page modules. A root page or detail page should be easy to find and edit without reading a monolithic shell.

Rationale:

- The current structure encodes the wrong mental model: tabs and detail screens are peers inside one component.
- Keeping it would make future page-specific optimization difficult.
- It would preserve the exact coupling this change is meant to remove.

Alternative considered: add TanStack Router only at the edge and keep `StudentAppShell` mostly intact. Rejected because it would produce two routers: URL routes outside and old tab/screen state inside.

### 7. P0 Detail Pages

P0 detail pages are:

| Detail page | Primary component source | Opened from |
| --- | --- | --- |
| chapter learning | `LearningHomePanel` | home recommendation, learn root chapter list |
| experiment point/video detail | `ExperimentDetailPanel` | chapter learning, home recent item |
| AI chat | `StudentAiChatPanel` | home, learn, AI root, point detail, report |
| assessment session | `PosttestPanel` | chapter complete, point complete, assessment root |
| assessment report | `PosttestSummaryPanel` | assessment submit, assessment root, home recent report |
| feedback | `StudentFeedbackForm` | profile root, error/support entry |

`LearningEntryPanel` becomes the learning root content. `AssessmentHomePanel` becomes the assessment root content but will likely need richer entry/report state later.

### 8. Keep APIs Stable For P0

P0 should reuse:

- `getStudentLearningPage`
- `getStudentLearningHome`
- `getStudentExperimentGroup`
- `getStudentExperimentDetail`
- student assistant streaming APIs
- student pretest/posttest APIs
- student feedback APIs
- student app config APIs

Backend changes should be limited to ensuring the SPA fallback serves direct nested student H5 routes such as `/chapter/halogens-17` and `/ai/chat`.

## Risks / Trade-offs

- Route refactor could regress existing learning flow -> migrate one route boundary at a time and keep current feature components reusable.
- Direct deep links may lack in-memory context -> encode durable identifiers in params/search and let detail pages fetch their own data.
- AI context can be too large for URL search -> pass compact context keys in URL and keep larger prompts in route state only when safe; support fallback global context.
- Browser back and explicit back can diverge -> implement a single navigation helper for detail pages.
- Bottom nav auto-hide can feel unstable -> route-level hide/show is P0; scroll-based root hide should be restrained and tested at phone widths.
- TanStack Router adds dependency and concepts -> isolate router setup under `app/router` and keep route pages plain React.
- Existing tests expect state-driven tabs -> update tests around URLs, root/detail visibility, bottom nav presence, and back behavior.

## Migration Plan

1. Add `@tanstack/react-router` and create the authenticated route layout.
2. Create the route-page folder structure for root and detail pages.
3. Add root routes for `home`, `learn`, `ai`, `assessment`, and `profile`.
4. Add P0 detail routes and a shared detail frame with explicit back handling.
5. Move `StudentBottomNav` out of `StudentAppShell` and make it route-aware.
6. Remove `activeTab` and nested route state as the source of authenticated navigation.
7. Convert current feature panels into route page compositions.
8. Delete or decompose obsolete shell code and route-like types after parity is reached.
9. Ensure detail pages hide bottom navigation and root pages restore it.
10. Update tests and mobile QA for route stack behavior.
11. Validate direct refresh/deep link fallback in the FastAPI student SPA serving path.

Rollback is frontend-local: keep backend APIs unchanged, and revert route setup plus page composition if needed.
