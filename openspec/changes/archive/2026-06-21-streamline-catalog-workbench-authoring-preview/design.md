## Context

The current catalog workbench grew from several adjacent needs:

- authoring the learning point itself;
- binding the point to an existing video;
- maintaining related experiments;
- inspecting node status, validation, ES indexing, and AI/RAG evidence;
- manually configuring how a student card might look.

Those needs are not equal. The product primitive for a point is still:

```text
one point = learning content + one experiment video + related experiment learning chain
```

The lower workbench should therefore be an authoring surface, not a mixed authoring/debug/status dashboard. Diagnostics still matter, but they are observation and repair surfaces. Student-card configuration is worse: it introduces a second authoring model that is not part of the point primitive and is now considered unused product surface. It should be removed from the data model, not merely hidden.

The existing student H5 point page already renders the true learning experience through `ExperimentPointPage -> CatalogPointDetailPanel`. The teacher preview should reuse that experience as much as possible. However, the normal student app uses a student token and student-only endpoints, and protected video URLs are also tokenized with the student token. A teacher cannot safely preview by simply opening `web-student` with a teacher session.

## Goals / Non-Goals

**Goals:**

- Make the selected-node lower workbench contain only editable configuration surfaces.
- For point nodes, keep exactly `内容`, `视频`, and `相关实验` as primary tabs.
- For directory nodes, keep only `内容` as the primary tab.
- Remove manual student-card configuration from teacher UI, frontend form models, backend schemas, read models, and database columns.
- Derive student card/list display from real catalog and point content instead of stored card-presentation overrides.
- Replace the disabled student preview button with `预览学习卡片`.
- Provide a teacher-authorized preview of the real student point/detail experience inside a standard phone mockup shell.
- Allow teachers to switch between a small set of standard phone presets for preview confidence, without exposing freeform responsive-debug controls.
- Keep `节点状态`, `AI 上下文`, and `高级` reachable as secondary diagnostic surfaces, preferably from a header `高级` / `更多` entry and outside the main tab strip.
- Ensure preview mode is read-only and does not create student learning/progress side effects.
- Simplify related experiments from a form-card editor into a compact ordered list that visually behaves like the existing catalog tree.
- Remove teacher-authored related-experiment short display names from the authoring model and student-facing read models.

**Non-Goals:**

- This change does not redesign the catalog tree hierarchy or point identity model.
- This change does not remove teacher-only notes; teaching notes remain authoring metadata.
- This change does not remove related experiments, ES indexing, AI/RAG evidence, or node status.
- This change does not make student preview a general student impersonation feature.
- This change does not require preserving legacy student-card field values; the user has explicitly declared those fields useless.
- This change does not turn the teacher console into the student console; preview is a constrained inspection flow.

## Decisions

### Decision 1: Split the selected-node editor into authoring and inspection

The lower tab strip becomes the authoring surface:

```text
Point node
  内容       edit title, teaching note, principle, phenomenon explanation, safety note
  视频       bind/manage the one experiment video relationship
  相关实验   order/edit related learning chain

Directory node
  内容       edit directory title and teaching note only
```

`节点状态`, `AI 上下文`, and `高级` move behind a secondary header action:

```text
Header
  [预览学习卡片] [归档] [发布/取消发布] [高级/更多]

高级/更多
  节点状态
  AI 上下文
  高级调试
```

The diagnostic surfaces should open in an auxiliary inspection window or a dedicated secondary route. This keeps routine authoring uncluttered while preserving repair tools.

Alternative considered: keep all tabs and reorder them. Rejected because the main problem is not order; the problem is that read-only/debug surfaces are presented as first-class configuration.

### Decision 2: Delete manual student-card configuration fields

Manual card configuration fields should be removed from live database and API contracts:

```text
catalog_nodes
  remove student_description
  remove card_image_asset_id
  remove card_icon_key
  remove card_accent
  remove card_layout
  remove card_presentation
  remove point_card_presentation
```

Frontend forms and mappers should remove corresponding fields:

```text
student_description
card_image_asset_id
card_icon_key
card_accent
card_layout
point_card_cover_image_asset_id
point_card_short_description
point_card_icon_key
point_card_accent
point_card_emphasis
```

Student card/list display becomes derived:

```text
Directory card
  title: directory title
  description: generated from structure if needed, or omitted
  icon/accent/layout: stable system defaults

Point card
  title: point title
  description: concise derived summary from learning content when available
  visual: bound video thumbnail when available, otherwise stable point default
  status/meta: binary video presence and learning availability
```

Alternative considered: hide the student-card tab but keep fields for compatibility. Rejected because the fields would keep leaking into schemas, tests, search docs, and mental models.

### Decision 3: Use teacher preview authorization instead of student impersonation

`预览学习卡片` should not open the normal student route with a teacher token. The normal student app clears non-student sessions, and student video media URLs require a student token. A direct open would either fail, ask the teacher to log in as a student, or encourage role leakage.

The preview flow should be:

```text
Teacher clicks 预览学习卡片
  -> teacher API creates a short-lived preview token for node_id
  -> teacher app opens a preview window with a standard phone mockup shell
  -> the phone screen loads the student preview route with the scoped token
  -> preview route validates token through preview API
  -> preview route renders the student point/detail component in read-only mode
```

Suggested API shape:

```text
POST /api/admin/catalog/nodes/{node_id}/preview-token
  auth: teacher/admin
  returns: { preview_url, token, expires_at }

GET /api/preview/catalog/points/{node_id}?preview_token=...
  auth: preview token only
  returns: StudentPointDetailResponse-compatible payload

GET /api/preview/media/{asset_id}/stream?preview_token=...
  auth: preview token only
  returns: protected preview media stream
```

The preview token should be scoped to:

- node id;
- teacher user id;
- purpose `catalog_point_preview`;
- short expiry;
- read-only endpoints only.

Alternative considered: create a fake student account/session for preview. Rejected because it would pollute learning analytics, pretest/posttest behavior, and role semantics.

### Decision 4: Reuse the real student rendering with preview-only disabled actions

The preview surface should use the same student point detail component or a thin wrapper around it. Preview mode should disable or hide mutating student actions:

- finish learning / start assessment;
- student AI chat launch;
- feedback submission;
- related-point navigation that would require a separate preview token, unless the preview flow explicitly mints one.

The component may show a small preview chrome outside the phone viewport, but the inside of the phone viewport should remain the student H5 composition.

Alternative considered: build a teacher-side mock preview from teacher detail data. Rejected because it would drift from the student H5 page and recreate the old problem of a fake student-card surface.

### Decision 5: Use `react-device-mockup` for the teacher preview shell

The teacher preview should not rely on hand-drawn phone CSS. The preview shell should use `react-device-mockup` or an equivalent maintained React device mockup component to render a standard phone frame. This dependency belongs in the teacher frontend preview shell, not in the core student learning page.

The preview shell should provide a small, curated device selector outside the phone viewport:

```text
Default: iPhone 15 Pro / modern island iPhone
Options: iPhone 14-style notch, iPhone SE-style legacy, Android phone
```

The selector is a preview preset, not a debugging console. The teacher should not get freeform drag resizing, arbitrary width/height inputs, network throttling, UA overrides, or DOM/debug controls in this flow. The selected preset may be remembered locally for teacher convenience.

The phone screen content should be an iframe or equivalent embedded route that loads the real student preview URL returned by the backend. The iframe must use the selected preset's screen dimensions, and the student route must remain read-only preview mode. If production deployment serves teacher and student apps from different origins, frame/CSP headers must explicitly allow only the expected internal preview origin.

Alternative considered: self-build a CSS phone shell. Rejected because the user wants a standard-looking phone preview and does not want visual correctness to depend on custom one-off CSS.

Alternative considered: give teachers a full responsive device toolbar. Rejected because the product need is confidence in standard phone display, not teacher-side responsive debugging.

### Decision 6: Treat diagnostics as independent inspection routes

`节点状态`, `AI 上下文`, and `高级调试` should be accessible through a header menu. They may use the existing panel components initially, but the route/window should communicate that these are inspection/repair tools, not point configuration.

Suggested teacher routes:

```text
/experiments/diagnostics/:nodeId?panel=status
/experiments/diagnostics/:nodeId?panel=ai-context
/experiments/diagnostics/:nodeId?panel=advanced
```

If a browser blocks `window.open`, the app can fall back to a modal or drawer, but the product model remains secondary inspection.

Alternative considered: keep diagnostics below the authoring tabs in collapsible sections. Rejected because they would still compete visually with authoring and make the workbench feel like a monitoring page.

### Decision 7: Directory authoring loses student-card copy

Directory nodes are navigation structure, not student-card design objects. With `student_description` removed, directory content authoring should focus on:

- directory title;
- teaching note, if useful for teacher/admin context;
- publication/archive actions through the header.

Student directory pages and cards should still render gracefully with title and child entries. Optional generated text can be derived from child counts or omitted.

Alternative considered: keep a directory student description in `内容`. Rejected because the user explicitly identified student-card configuration as not useful, and keeping only one field would preserve the same authoring burden.

### Decision 8: Related experiments use a compact tree-like ordered list

The `相关实验` panel should feel like a small ordered navigation list, not a nested form editor. The current card-heavy design gives every related experiment a border, a visible drag handle, up/down buttons, delete button, and optional display-name input. That makes the secondary task look heavier than the point content itself.

The target model is closer to the catalog sidebar tree:

```text
相关实验                                  默认 2   手动 0   重置默认

Br2在水 / 四氯化碳 / KI水溶液中的溶解性        同目录默认        ...
I2在水 / 四氯化碳 / KI水溶液中的溶解性         同目录默认        ...

搜索并添加相关实验...
```

Interaction rules:

- Each related experiment is a single compact row, not a card with embedded form controls.
- The whole row is the draggable object. There is no always-visible `⋮⋮` / six-dot / grip handle.
- There are no always-visible up/down reorder buttons.
- During drag, the source row becomes visually subdued, a lightweight drag preview follows the pointer, and a thin drop indicator line appears between rows, matching the tree movement language.
- Hover/focus may show a quiet row background and secondary actions, but must not shift layout.
- Row height should stay close to the catalog tree row rhythm, roughly 36-44px, with stable title truncation and no nested cards.
- The right side may show a compact source tag such as `同目录默认`, `已调整默认`, or `手动添加`.
- Destructive or less-common actions belong in a `...` row menu or hover-only quiet icon, not in a permanent button cluster.
- Keyboard/accessibility fallback may exist in the `...` menu, but those commands should not be visually primary.
- The panel copy should not teach the drag mechanism in visible prose. The drag interaction, row preview, and drop indicator should make ordering understandable.

Add/remove rules:

- The related-experiment panel itself should not render an inline search box, search results region, or manual save button.
- After the ordered list, render one dashed placeholder row/slot that visually reads as "add another experiment" without becoming a second configuration panel.
- Clicking the dashed placeholder opens a modal/window catalog tree picker using the same lightweight directory-tree language as the catalog workspace.
- The picker loads root nodes for the selected chapter and lazily loads children when directories expand; only point nodes may be selected as related experiments.
- Selecting a point adds it to the ordered list and immediately persists the related-link payload.
- Removing a row, reordering by drag/drop, using menu reorder fallback actions, and resetting to same-directory defaults all immediately persist the related-link payload.
- Duplicate target points and the currently edited point must be disabled or ignored in the picker.
- The panel should not rely on prominent instructional text to explain saving. The absence of a save button is intentional because each edit auto-saves.

Short display-name rule:

Teacher-authored related-experiment short display names are removed. Students should see the real target experiment title. The related-experiment editor should not expose a `显示名称`, `短名称`, or equivalent per-link label field.

Backend/read-model implications:

- Related-link write payloads should no longer accept a student-facing display label.
- Related-link read models should not use a stored label to override `target_title`.
- The obsolete related-link label columns should be removed with a destructive migration from both legacy and catalog related-link tables; fresh schema baselines must not recreate them.
- Stale client-sent label-like fields must be stripped before persistence and must not affect teacher preview, student H5, search documents, AI context, or video-library search text.
- Related link ordering, hidden/default override state, and manual additions remain supported.

Alternative considered: keep a small hover-only drag handle. Rejected for this surface because the list is short, the whole row can safely act as the draggable target, and the existing tree already demonstrates that row-level movement can be understandable without a visible grip.

Alternative considered: keep up/down buttons for discoverability. Rejected because they dominate the row visually. If needed, reorder commands can live in the secondary row menu for accessibility and precision fallback.

## Risks / Trade-offs

- [Risk] Dropping database columns is destructive. -> Mitigation: make the migration explicit and one-way; do not promise value preservation for fields declared unused. Keep rollback as application/database backup restore, not automatic field reconstruction.
- [Risk] Student catalog cards may look sparse after removing descriptions and accent fields. -> Mitigation: derive point summaries from real point content and use stable visual defaults; verify phone views visually before release.
- [Risk] Preview tokens could become a role-boundary bypass. -> Mitigation: scope tokens to one node, short expiry, read-only preview endpoints, and no diagnostics/teacher notes.
- [Risk] Reusing the student component might accidentally trigger student side effects. -> Mitigation: add explicit preview mode guards and tests for no assessment, no feedback, no AI chat mutation, and no progress recording.
- [Risk] The device mockup dependency could visually diverge from real browser dimensions. -> Mitigation: keep the dependency responsible only for the frame, map presets to explicit iframe viewport sizes, and verify screenshots with Playwright mobile viewports.
- [Risk] Moving diagnostics out of tabs may hide useful repair information. -> Mitigation: keep header summary cards and status badges visible; expose `高级/更多` from the selected-node header and allow direct panel deep links.
- [Risk] Removing card fields touches seed/import/search code beyond the visible UI. -> Mitigation: include backend contract tests, migration tests, frontend typecheck, and student H5 rendering tests in the task list.
- [Risk] Removing visible drag handles makes reorder less discoverable. -> Mitigation: use row hover feedback, subdued source row, cursor-following preview, and clear drop indicator; keep menu-based reorder commands as an accessibility fallback if needed.
- [Risk] Old related-link label columns may remain in existing databases or be recreated by baseline migrations. -> Mitigation: add a destructive drop migration plus migration contract tests proving fresh and upgraded schemas do not contain related-link title override columns.

## Migration Plan

1. Add migration to drop obsolete catalog-node card presentation columns.
2. Remove fields from backend schemas, normalization helpers, create/update payloads, common read-model serialization, seed/import code, ES/search document builders, and tests.
3. Update teacher frontend API types and mappers to remove student-card form values.
4. Remove `CatalogStudentCardPanel` and remove `student-card` from editor tab keys and tests.
5. Restrict primary editor tabs to content/video/related for points and content for directories.
6. Add the header `高级/更多` diagnostics menu and auxiliary diagnostic route/window using existing panel components where practical.
7. Add teacher preview token API and preview read endpoints.
8. Add teacher preview shell using a standard phone mockup with curated presets, loading the real student preview route in the phone screen.
9. Add student preview route/shell that renders the real point detail in phone viewport preview mode.
10. Update student catalog cards to derive presentation from real catalog/point content and video metadata.
11. Remove related-experiment short display names from teacher forms, frontend payload mapping, backend request schemas, and read-model title resolution.
12. Replace the related-experiment card editor with a compact tree-like sortable row list and compact search/add rows.
13. Run backend migrations/tests, frontend tests/typecheck, OpenSpec validation, and visual QA for teacher workbench plus mobile preview.

Rollback:

- Code rollback can restore old UI only if the database is restored from backup before the destructive migration.
- No automatic downgrade migration should attempt to reconstruct removed student-card values.

## Open Questions

- Should preview related-point navigation be disabled in the first implementation, or should each related click mint a new preview token for the target point?
- Should `预览学习卡片` be enabled for draft/unpublished points only when structure is valid, or should it show a controlled preview error for structurally invalid points?
- Should the auxiliary diagnostics surface open as a separate browser window by default, or as a route in the same tab with a clear back affordance?
