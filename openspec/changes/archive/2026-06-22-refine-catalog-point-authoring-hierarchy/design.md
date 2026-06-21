## Context

The teacher catalog editor is a two-pane workbench: the left tree chooses a chapter node, and the right panel maintains the selected directory or experiment point. Recent improvements already separated routine authoring into `内容`, `视频`, and `相关实验`, with diagnostics in modals. The remaining friction is that the selected-point header and content tab still blur object identity, authoring fields, preview tools, publication state, and destructive lifecycle actions.

The current header renders preview, diagnostics, archive, and publish/unpublish in one button row. The current point content tab still renders `多目录共享实验` and `点位名` inside the content form, even though those are point identity/status concepts. Backend status summaries already expose a richer `primary_state`, `core_readiness`, `visibility`, and `async_consumption` model, but the header does not yet use that model to choose a single next action.

## Goals / Non-Goals

**Goals:**

- Make the selected-point header responsible for point identity, shared-experiment reuse state, current status, and one state-machine-driven primary action.
- Move `预览学生端`, diagnostics, unpublish, and archive into a `更多` menu so routine authoring has a calmer Apple-like hierarchy.
- Move point title editing to the header, with the content form preserving title data silently for save compatibility.
- Normalize the point content tab around one section title and consistent field visual weight.
- Align status semantics so `student_available` requires both the catalog placement and shared point content to be published.
- Allow teacher preview to inspect non-published point states, while still excluding truly unavailable archived shared content unless explicitly supported.

**Non-Goals:**

- Redesigning the left catalog tree.
- Changing media upload or related-experiment workflows.
- Adding a new design system dependency.
- Changing database schema.
- Reworking the student-facing point page layout.

## Decisions

### Decision 1: Header owns point identity

The selected-point header will show the point title, path, active shared-experiment placement count, and a small shared-experiment identity note. The content form will no longer expose `点位名` as a normal content field.

Rationale: point title is the object name a teacher selected; it behaves like a document title in Apple productivity apps, not like body content. Keeping it in the header also satisfies the existing `Point title is a single visible authoring concept` contract.

Alternative considered: keep the point title as the first content form field. Rejected because it makes identity and body fields look equal and repeats the title already visible in the header.

### Decision 2: One primary action, everything else in more

The header will render at most one primary state action. The more menu will contain preview, status, diagnostics, advanced debug, and lower-frequency lifecycle actions. Destructive actions will be visually grouped at the bottom of the menu and still use confirmation.

Rationale: mature systems treat grouped buttons as related actions. Here preview, diagnostics, archive, and publish are different classes of work. A single primary action gives teachers a clear next step and avoids a crowded toolbar.

Alternative considered: split publish/unpublish/archive into a second toolbar row. Rejected because it still presents lifecycle tools as equal to routine authoring.

### Decision 3: Main action is derived from status priority

The header primary action will be computed from the resolved node status, content status, video readiness, and placement visibility. Priority:

1. `archived` -> `恢复点位`
2. `blocked` -> `查看问题`
3. missing content -> `编辑内容`
4. content complete but shared content not published -> `发布学习内容`
5. missing video -> `绑定视频`
6. placement not published -> `发布到学生端`
7. ES/RAG sync failure -> `查看同步`
8. fully published -> no primary button; show state only

Rationale: this follows the teacher's natural workflow from identity repair, to content, to video, to student visibility, to post-publish monitoring.

Alternative considered: publish whenever `node.status !== published`. Rejected because it conflates shared content publication with catalog placement publication and can hide missing video/content work.

Primary action behavior:

| Action | Behavior |
| --- | --- |
| `恢复点位` | Calls the existing node restore mutation for the selected placement, then refreshes the selected node detail. |
| `查看问题` | Opens the node status diagnostics surface focused on blocking conditions; it does not mutate data. |
| `编辑内容` | Opens a focused content task window that reuses the point content authoring form model, highlights missing required fields, and saves through the existing point-content save mutation; it does not call AI or auto-fill content by itself. |
| `发布学习内容` | Publishes the saved shared point content. If implementation detects unsaved form edits, it should open the focused content task window and require saving before publishing rather than publishing stale data. |
| `绑定视频` | Opens the existing video picker window for the selected point. If no ready asset exists, the window should show the video-resource entry point; it does not upload or bind automatically without a teacher selecting a media asset. |
| `发布到学生端` | Calls the node publication mutation for the selected catalog placement after content/video readiness is satisfied by the UI state machine. |
| `查看同步` | Opens the node status diagnostics surface focused on ES and AI/RAG sync conditions; retry actions remain inside diagnostics. |
| Fully published | Shows status only; unpublish and archive remain in the secondary menu with confirmation. |

### Decision 4: Navigation primary actions open task windows

Primary actions that do not directly mutate lifecycle state must still open a surface where the teacher can complete the task immediately.

- `编辑内容` opens a modal or drawer with the same required learning fields as the content tab: teacher note, principle mode/content, phenomenon explanation, and safety note. The first missing required field receives focus or an inline error highlight. Saving in the window uses the same point-content save mutation as the content tab and then refreshes the selected node detail.
- `绑定视频` opens the existing `选择视频素材` picker window rather than merely switching tabs. The picker remains explicit: the teacher chooses one ready media asset before any binding mutation runs.
- `查看问题` and `查看同步` open the diagnostics modal on the relevant section.

Rationale: a header primary action should either perform the state transition or open a contained task surface. Merely switching tabs creates a "magic button" feel without delivering a complete interaction.

Alternative considered: switch tabs and scroll/focus. Rejected because it still makes the teacher hunt inside the page and does not feel like a concrete command.

### Decision 5: Preview is state-agnostic inspection

`预览学生端` moves into the more menu and should be available for every non-structurally-blocked point state that can be rendered. Preview output may show missing content/video placeholders, because teachers use it to inspect current state before publishing.

Rationale: preview does not advance lifecycle state. It is a utility that should not compete with the next action.

Alternative considered: only show preview after published. Rejected because teachers need to inspect drafts before publishing.

### Decision 6: Content tab uses plain grouped form hierarchy

The content tab title will match the tab label (`内容`). The form will use consistent labels and helper text for teacher note, principle mode/content, phenomenon explanation, and safety note. Equation editor panes remain visually heavier because they are a real editor/preview workbench, but the surrounding section labels should be restrained and consistent.

Rationale: Apple-like editing surfaces reduce decoration and let content carry the weight. The current mix of warning-colored teacher note, identity banner, and heavy sub-cards makes unrelated concerns compete.

Alternative considered: wrap every field in separate cards. Rejected because nested cards make the form feel heavier and lengthen the visual scan path.

## Risks / Trade-offs

- [Risk] Removing the visible point title form item could break save payloads that expect `point_title`. -> Keep the field hydrated internally and synchronize edits from the header into the same form value.
- [Risk] Previewing drafts can be confused with student availability. -> Add copy/status in preview and keep `student_available` semantics strict.
- [Risk] A single primary action could hide available power-user actions. -> Keep them in the more menu with explicit labels.
- [Risk] Dirty worktree contains unrelated media/ES changes. -> Keep this change scoped to catalog editor and status/preview code paths.

## Migration Plan

1. Add status/action mapping helpers and tests.
2. Refactor `CatalogEditorHeader` action rendering and title edit affordance.
3. Refactor `CatalogNodeContentPanel` to remove identity copy from the content flow and align field hierarchy.
4. Tighten backend status summary and preview handling.
5. Run focused frontend tests, backend preview/status tests, typecheck, and OpenSpec validation.
