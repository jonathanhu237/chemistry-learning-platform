## Why

The catalog point workbench still mixes authoring controls with observation and diagnostics. Teachers need the selected-node workspace to stay focused on the three things that actually configure a learning point: learning content, one experiment video, and related experiments.

The current `学生卡片` panel is a misleading extra authoring model. Its fields are not part of the point primitive, duplicate information already visible in the real student flow, and make the teacher think they must hand-design cards instead of maintaining the learning object.

## What Changes

- Simplify the selected-node workbench main tab bar:
  - Point nodes keep only `内容`, `视频`, and `相关实验`.
  - Directory nodes keep only `内容`.
- Move `节点状态`, `AI 上下文`, and `高级` out of the main configuration tabs into a secondary `高级` / `更多` entry from the selected-node header.
- Replace the disabled `预览学生端` button with `预览学习卡片`.
- Add a teacher-authorized mobile preview flow that opens the real student point/detail experience in a phone-sized window or equivalent preview shell.
- Use a standard device mockup component such as `react-device-mockup` for the teacher preview shell, with a small set of selectable phone presets instead of a hand-drawn custom phone frame.
- Preview mode MUST reuse the student H5 point/detail rendering and student API shape where practical, but MUST be authorized by teacher/admin credentials and MUST NOT require switching to a student account.
- Preview mode MUST NOT create student learning events, start assessments, submit feedback, open real AI chat sessions, or mutate student progress.
- **BREAKING** Remove manual student-card configuration from the catalog data model and APIs:
  - Remove directory card fields: `student_description`, `card_image_asset_id`, `card_icon_key`, `card_accent`, `card_layout`, and `card_presentation` where they only exist for manual student-card presentation.
  - Remove point-card override fields stored in `point_card_presentation`, including short description, cover image, icon key, accent, and emphasis.
  - Remove teacher UI, form hydration, payload mapping, tests, and read-model dependencies for those fields.
- Student directory and point cards will derive display from canonical catalog content:
  - Directory cards derive from directory title, child/descendant structure, and stable system defaults.
  - Point cards derive from point title, learning content summary where available, binary video presence, and bound video thumbnail where available.
- Keep node status and AI/RAG diagnostic data available, but treat it as read-only diagnostics rather than primary authoring configuration.

## Capabilities

### New Capabilities
- `teacher-catalog-student-preview`: Defines teacher-authorized preview of the real student catalog point/detail surface, including mobile window behavior, preview authentication, non-mutating preview constraints, and reuse of student H5 rendering.

### Modified Capabilities
- `teacher-experiment-catalog-editor`: Refocuses the right editor workbench so the main configuration tabs only contain content, video, and related-experiment authoring, with diagnostics moved to secondary surfaces.
- `experiment-catalog-tree`: Removes manual student-card presentation fields from the catalog tree data model and read/write API contracts.
- `student-h5-learning-experience`: Changes student catalog card behavior so cards are derived from real catalog/point content instead of teacher-authored card-presentation overrides.

## Impact

- Backend schema/migrations:
  - Drop obsolete catalog-node student-card presentation columns and remove their seed/import handling.
  - Update catalog node create/update payload schemas, normalization helpers, read models, and tests.
- Teacher frontend:
  - Remove `CatalogStudentCardPanel` and related tab routing.
  - Remove form fields and mappers for manual student-card presentation.
  - Add a header-level `预览学习卡片` action and secondary `高级` / `更多` diagnostics entry.
  - Add a teacher preview window/shell that wraps the real student preview route in a standard phone mockup with constrained device presets.
- Student frontend:
  - Add or adapt a preview route/shell that can render the point detail in a mobile-sized context with teacher preview authorization.
  - Derive directory and point cards from existing catalog content and video metadata.
- Auth/API:
  - Add a short-lived teacher preview token or equivalent preview authorization path.
  - Ensure preview endpoints do not accept student mutations and do not expose teacher-only diagnostics.
- Tests and QA:
  - Update contract tests for removed fields.
  - Add visual/interaction coverage for the simplified workbench tabs, preview learning-card flow, and diagnostics access.
