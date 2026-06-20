# student-web-frontend-maintainability Specification

## Purpose
Define maintainability boundaries for the student H5 frontend so future student-side product changes can land in focused app, feature, shared, and style modules without regressing the verified mobile bottom-tab learning experience.
## Requirements
### Requirement: Student frontend feature module boundaries
The student H5 frontend SHALL organize catalog navigation, point detail, authenticated shell, and onboarding code into feature-oriented modules with explicit ownership boundaries.

#### Scenario: Student app shell owns route orchestration
- **WHEN** the catalog route migration is implemented
- **THEN** app-level route providers, authenticated layout, disabled-route redirect behavior, and finish-learning assessment handoff MUST be owned by app-level modules
- **AND** feature modules MUST NOT each create independent app-level navigation state.

#### Scenario: Feature modules own their own panels
- **WHEN** a developer edits assistant, feedback, assessment, catalog navigation, point detail, periodic-table, learning, auth, or pretest behavior
- **THEN** the primary React components for that behavior MUST live under the corresponding feature module or a clearly shared module
- **AND** `apps/student-web/src/App.tsx` MUST remain a composition/root file rather than the owner of feature internals.

#### Scenario: Shared modules are intentionally limited
- **WHEN** helper logic is shared across feature modules
- **THEN** it MUST live under a shared or app-level module with a clear name
- **AND** feature-private helpers MUST remain inside their feature module to avoid recreating a hidden monolith.

### Requirement: Behavior-preserving modularization
The student H5 frontend modularization SHALL preserve the student-visible behavior completed by the bottom-tab navigation change.

#### Scenario: Authenticated shell behavior is preserved
- **WHEN** modularization is complete
- **THEN** authenticated students MUST still see the bottom-tab destinations `学习`, `实验`, `问答` when enabled, `测评`, and `我的`
- **AND** tab switching MUST preserve nested learning state where practical and MUST NOT log the student out.

#### Scenario: Learning behavior is preserved
- **WHEN** modularization is complete
- **THEN** the periodic-table learning entry, recommended chapter cues, area selection, family selection, current chapter facts, experiment video list, experiment point detail, and finish-learning flow MUST behave as before the refactor.

#### Scenario: Assistant and feedback behavior is preserved
- **WHEN** modularization is complete
- **THEN** the student assistant MUST remain a full `问答` tab with default `learning_home` context and optional chapter/experiment/point context handoff
- **AND** feedback MUST remain inside `我的` with screenshot add, change, remove, and authenticated submit behavior.

#### Scenario: Assessment behavior is preserved
- **WHEN** modularization is complete
- **THEN** completing learning MUST still navigate to the post-learning assessment state
- **AND** submitting posttest answers MUST still render the report, AI summary, markdown, LaTeX, and wrong-answer explanation behavior covered by existing tests.

### Requirement: CSS ownership and cascade control
The student H5 frontend SHALL move styles toward feature-owned CSS files without changing the existing mobile visual contract.

#### Scenario: Styles are split by stable ownership
- **WHEN** styles are split out of `apps/student-web/src/styles.css`
- **THEN** global base styles, app shell styles, auth styles, learning styles, periodic-table styles, experiment styles, assistant styles, feedback styles, and assessment styles MUST have explicit files or sections
- **AND** shared mobile tokens MUST remain available to all feature styles.

#### Scenario: CSS split preserves current visuals
- **WHEN** feature CSS files are introduced
- **THEN** existing class names and cascade order SHOULD be preserved where practical
- **AND** the refactor MUST NOT intentionally redesign colors, spacing, typography, bottom navigation, periodic table, assistant, feedback, or assessment surfaces.

#### Scenario: Bottom interactions remain unobstructed
- **WHEN** modularized styles render at 360x780, 390x844, or 430x932 CSS-pixel viewports
- **THEN** bottom navigation MUST NOT block chat composer, feedback submit, finish-learning action, posttest submit, video controls, or other primary student actions.

### Requirement: API and domain helper ownership
The student H5 frontend SHALL separate domain helper ownership while adopting the new catalog-node backend contracts.

#### Scenario: Backend contracts move to catalog nodes
- **WHEN** API code is updated for catalog tree and point detail routes
- **THEN** request URLs, request payload shapes, response handling, authentication token behavior, media URL behavior, feedback attachment behavior, and assistant streaming behavior MUST match the new catalog-node contracts
- **AND** legacy experiment group/detail APIs MUST NOT remain as live compatibility exports.

#### Scenario: API modules are split by domain
- **WHEN** API modules are split or reorganized
- **THEN** auth, learning profiles, catalog tree, point detail, assistant, feedback, media, and assessment ownership MUST be clear
- **AND** route pages MUST import through the appropriate domain API surface.

#### Scenario: Formatting helpers move near their domain
- **WHEN** pure formatting helpers are extracted or updated
- **THEN** family/chapter formatting helpers MUST live near learning or periodic-table modules
- **AND** catalog node formatting helpers MUST live near catalog modules
- **AND** assessment answer formatting helpers MUST live near assessment modules.

### Requirement: Obsolete floating overlay cleanup
The student H5 frontend SHALL remove or quarantine obsolete floating overlay code after authenticated floating AI and feedback usage has been removed.

#### Scenario: No authenticated floating AI or feedback paths remain
- **WHEN** modularization is complete
- **THEN** authenticated student pages MUST NOT render `.ai-chat-toggle`, `.feedback-toggle`, `.ai-chat-fab`, or `.feedback-fab`
- **AND** repository search MUST confirm no live student authenticated path depends on those controls.

#### Scenario: Shared overlay primitives are handled deliberately
- **WHEN** `MobileFloatingOverlay` or related floating overlay state helpers are no longer used by student authenticated pages
- **THEN** they MUST either be removed or moved into a clearly named future overlay/sheet primitive module
- **AND** the decision MUST be documented in implementation notes or final task review.

### Requirement: Refactor verification gates
The student H5 frontend modularization SHALL keep behavior tests and mobile viewport QA as mandatory gates.

#### Scenario: Core verification runs
- **WHEN** modularization implementation is complete
- **THEN** `npm run typecheck --prefix apps/student-web` MUST pass
- **AND** `npm run test:e2e --prefix apps/student-web` MUST pass
- **AND** `npm run build --prefix apps/student-web` MUST pass.

#### Scenario: Mobile viewport QA runs
- **WHEN** modularization implementation is complete
- **THEN** student mobile viewport QA MUST pass for 360x780, 390x844, and 430x932 CSS-pixel viewports
- **AND** the QA MUST still cover bottom tabs, assistant tab, profile feedback attachment behavior, chapter switcher, experiment point detail, and assessment handoff.

#### Scenario: Feature-disabled configuration remains covered
- **WHEN** assistant or feedback feature flags are disabled
- **THEN** tests MUST confirm the assistant tab and profile feedback entry are hidden, disabled, or redirected according to current app-config behavior
- **AND** this behavior MUST remain covered after component extraction.

#### Scenario: OpenSpec and git hygiene are verified
- **WHEN** modularization implementation is complete
- **THEN** `openspec validate student-web-frontend-modularization --strict` MUST pass
- **AND** `git diff --check` MUST report no whitespace errors.

### Requirement: Recursive catalog UI ownership
The student H5 frontend SHALL implement recursive catalog pages through reusable catalog feature components rather than hardcoded level-specific pages.

#### Scenario: Directory depth changes
- **WHEN** a chapter catalog has one, two, or more directory levels
- **THEN** the same route/page pattern MUST render each directory level
- **AND** implementation MUST NOT create separate hardcoded pages for third-level, fourth-level, or fifth-level directories.

#### Scenario: Point detail opens from multiple sources
- **WHEN** a point detail opens from chapter catalog, nested catalog, search, related links, or recent learning
- **THEN** the point detail feature MUST reuse the same component path
- **AND** source-aware return behavior MUST be handled by route/search context rather than duplicated component state.
