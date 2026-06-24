## Why

The student H5 bottom navigation currently uses a tall icon-plus-label treatment with active background blocks, which consumes vertical phone space and makes the Atom destination feel like another ordinary tab. The product now needs a more compact, Xiaohongshu-like bottom navigation where Atom is the centered branded core entry while ordinary destinations stay quiet and space-efficient.

## What Changes

- Redesign the authenticated student root bottom navigation into a shorter compact bar.
- Keep the five existing root destinations and route identities unchanged: home, learn, ai/Atom, assessment, and profile.
- Render ordinary destinations as text-forward compact tabs with subtle active state rather than large active background blocks.
- Render the centered Atom destination as a green rounded rectangular/squircle brand control with a white Atom icon.
- Preserve safe-area handling, touch targets, keyboard-aware Atom composer behavior, root/detail route visibility rules, and accessibility labels.
- Update regression tests to protect the compact bar height, centered Atom treatment, route order, and detail-route hidden-navigation behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `student-h5-mobile-design-system`: Define the compact bottom navigation visual, height, safe-area, touch-target, and Atom-centered branded control requirements.
- `student-h5-route-stack-navigation`: Clarify that the five root destinations remain unchanged while Atom is visually centered and elevated as the primary assistant destination.

## Impact

- Affected frontend code: `apps/web-student/src/app/shell/StudentBottomNav.tsx`, `apps/web-student/src/mobile/tokens.css`, and `apps/web-student/src/styles/app-shell.css`.
- Affected tests: student shell contract tests and authenticated student E2E tests that assert bottom navigation structure and keyboard/detail route behavior.
- No backend API, database, dependency, or route-path changes are expected.
