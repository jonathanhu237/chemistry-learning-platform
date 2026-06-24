## Why

The student H5 app currently mixes chat, bot, sparkle, and atom pictograms across AI and chemistry-learning surfaces. This makes the student-facing AI identity feel inconsistent, especially now that the AI root has become a first-class bottom-tab experience.

## What Changes

- Standardize the `apps/web-student` AI visual identity so the Atom pictogram represents student AI entry points, AI actions, and assistant identity states.
- Standardize the `apps/web-student` student-facing assistant name to `Atom 学习助手` and replace visible `问 AI` / `问AI` ask-entry copy with `问问Atom`.
- Replace non-AI student-web Atom icon affordances that would conflict with the new AI identity, such as the element-search input and generic element/learning empty states.
- Keep ordinary search affordances represented by the Search icon and experiment/chemistry content affordances represented by chemistry-appropriate icons such as `FlaskConical`.
- Preserve existing teacher/admin AI iconography and behavior; this change is scoped to `apps/web-student` only.
- No backend API, routing, permissions, or assistant behavior changes are introduced.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `student-h5-ai-assistant`: Define Atom as the student H5 AI visual identity and assistant product name across root AI, contextual AI actions, assistant messages, AI disabled states, and AI prompt/result affordances.
- `student-h5-mobile-design-system`: Reserve the student-web Atom pictogram for AI identity and require non-AI search, experiment, and element states to use clearer alternate icons.

## Impact

- Affected code is limited to `apps/web-student`.
- Expected touch points include student bottom navigation, home feed ask action, point detail ask action, assessment assistant actions, AI root/detail empty states, assistant message metadata, video-library AI prompt rows, and periodic-table search.
- Focused validation should cover student app tests and OpenSpec strict validation.
