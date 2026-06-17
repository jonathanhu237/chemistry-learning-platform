## Why

The current student H5 chapter page mixes element/common-property learning with experiment-point video tasks in one long vertical flow, and it still implies that chemical property sections must drive experiment grouping. On a phone-sized H5/WebView, this makes the page too long and makes the learning logic feel forced: students need a quick way to switch between "understand this family/element" and "watch/learn the related experiment points".

This change refines the just-completed current-family chapter model into a clearer two-page composition inspired by mature mobile UI patterns: an Apple-style segmented control for switching between two sibling views inside the same chapter, with theory/facts on one side and chapter experiment-point videos on the other.

## What Changes

- Recompose the current family/chapter learning page into two switchable in-page views:
  - A: element facts and family-wide common properties;
  - B: chapter experiment-point video learning.
- Add a phone-first sticky segmented switcher, visually and behaviorally similar to iOS segmented controls, so students can switch between A/B quickly without returning to the periodic-table entry.
- Keep the current chapter/family identity and within-family element chips shared above or near the segmented switcher.
- Remove the forced "property section -> experiment-point group" browsing model from the primary learning flow.
- Render the experiment/video view by chapter learning structure:
  - current chapter/family,
  - parent experiment,
  - point card,
  - video availability and question count.
- Keep chemical property sections as theory/common-property content in the facts view only, not as required experiment grouping.
- Preserve AI chat, global feedback, point detail, completion-to-posttest, authentication, app feature switches, and protected media behavior.
- Preserve the H5/mobile-browser deployment path; do not introduce a native WeChat mini-program, Taro, uni-app, React Native, or CI/release workflow change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-experience`: replace property-driven experiment grouping with a two-tab chapter composition where facts/common properties and experiment-point videos are sibling views.
- `student-h5-learning-flow`: clarify that chapter learning remains within one selected family/chapter while students switch between facts and experiments, then continue into point detail and post-learning assessment.
- `student-h5-mobile-design-system`: add a concrete mobile interaction contract for a sticky segmented chapter switcher, including touch target, safe-area, floating overlay, and scroll-position behavior.

## Impact

- Student frontend:
  - `apps/student-web/src/App.tsx`
  - `apps/student-web/src/styles.css`
  - `apps/student-web/src/mobile/*`
  - `apps/student-web/scripts/mobile-viewport-qa.mjs`
- Student API and schemas:
  - `apps/student-web/src/api.ts`
  - `server/app/student_learning_schemas.py`
  - `server/app/services/student_learning_service.py`
- Seed/resources:
  - `data/seed/student_learning/element_profiles.json` remains the explicit display-facts source.
  - Existing `property_sections` may remain for A-page theory content.
  - Experiment grouping should be derived from current chapter/parent experiment/point data, not from property section selection.
- Verification:
  - student-web typecheck/build
  - backend tests or targeted student learning payload tests
  - production resource validation
  - mobile viewport QA at 360x780, 390x844, and 430x932 CSS pixels
