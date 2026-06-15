## 1. Backend Point Analytics

- [x] 1.1 Fix the weak-point endpoint so it loads point-aware attempts before aggregating `point_items`.
- [x] 1.2 Verify the endpoint still returns legacy weak question/KP rows and point-aware rows together.

## 2. Question Bank UI

- [x] 2.1 Update admin web types for point-aware metadata, option links, and weak-point responses.
- [x] 2.2 Change the question bank page from chapter-first navigation to experiment-first navigation using existing bank summary data.
- [x] 2.3 Add question filters for type, point, status, and keyword while preserving the current two-pane admin style.
- [x] 2.4 Update question list columns to show primary points, evidence status, and multi-point state.
- [x] 2.5 Expand the question detail modal to show full point-aware evidence, source refs, option diagnostic links, and deterministic fill-blank aliases.

## 3. Analytics UI

- [x] 3.1 Update the class weak-point card to prioritize point-aware weak experiment points and keep legacy weak rows as secondary context.
- [x] 3.2 Replace raw student report JSON with readable weak point, attempt, and timeline sections.

## 4. Validation

- [x] 4.1 Run frontend typecheck/build for the admin web app.
- [x] 4.2 Run `openspec validate adapt-point-aware-question-bank-frontend --strict`.
