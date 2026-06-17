## Why

The student H5 learning page is entered after a student chooses a family or chapter from the periodic-table learning entry, but the current composition still behaves partly like a cross-family browsing page. This blurs the product model: the page should teach the currently selected family/chapter, let students inspect individual elements inside that family, then drive them into experiment-point learning and assessment.

This change captures the corrected learning-page architecture before implementation so the context survives later refactors: family/chapter selection belongs to the periodic-table entry; the chapter page belongs to one current family; element chips switch per-element facts; family-wide properties summarize common trends; experiment points remain the core task.

## What Changes

- Reframe the student H5 element learning surface as a current family/chapter page reached from the periodic-table entry, not as a place to browse sibling families.
- Replace prominent sibling-family tabs on the chapter page with current-family context, a clear return/switch-chapter affordance, and within-family element selection.
- Add a page composition contract for:
  - current family/chapter identity,
  - selected element facts,
  - family-wide common properties and trends,
  - property-driven experiment-point groups,
  - point detail learning,
  - completion-to-assessment handoff.
- Extend the student learning profile payload/seed contract so display facts can distinguish family-level content from per-element content and optional licensed reference media.
- Preserve the product-specific chemistry learning UI and the existing phone-first H5 constraints.
- Preserve existing experiment-point, AI assistant, feedback, and assessment behavior while reorganizing the learning page around the corrected hierarchy.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-experience`: clarify the element chapter learning-page composition, periodic-table entry relationship, current-family page model, per-element fact switching, family-wide property content, and experiment-point learning priority.
- `student-h5-learning-flow`: clarify that the learning entry may select a family/chapter before opening the element chapter page, and that the page continues into point detail and post-learning assessment.
- `student-h5-mobile-design-system`: clarify mobile composition rules for this specific chapter page, including removal of cross-family top tabs from the page-level primary navigation and preservation of touch-first element chips and point cards.

## Impact

- Student frontend:
  - `apps/student-web/src/App.tsx`
  - `apps/student-web/src/styles.css`
  - `apps/student-web/src/mobile/*`
- Student API and schemas:
  - `apps/student-web/src/api.ts`
  - `server/app/student_learning_schemas.py`
  - `server/app/routers/student_learning.py`
  - `server/app/services/student_learning_service.py`
- Seed/resources:
  - `data/seed/student_learning/element_profiles.json`
  - production resource validation for student learning profiles
- Testing and QA:
  - student-web typecheck/build
  - mobile viewport QA at 360, 390, and 430 CSS-pixel widths
  - backend tests or targeted validation for the student learning payload

This change does not require CI/release workflow changes and does not introduce a native mini-program package; the target remains mobile-browser H5/WebView.
