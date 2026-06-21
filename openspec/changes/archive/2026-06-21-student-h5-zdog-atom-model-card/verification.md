## Verification Evidence

- `python -m pytest server/tests/test_student_learning.py::test_student_learning_profile_seed_is_valid`
  - Passed. The active profile seed now validates required teaching facts and first-scope RSC physical fact fields.
- `npm run test --prefix apps/student-web -- src/features/atom-viewer/learningAtomAdapter.test.ts`
  - Passed. Covers noble-gas shorthand, explicit/spaced d configurations, fallback shell derivation, and physical/teaching fact separation.
- `npm run typecheck --prefix apps/student-web`
  - Passed.
- `npm run test:e2e --prefix apps/student-web`
  - Passed. Covers student app core flow, bottom navigation, assistant/profile tabs, chapter entry, atom model card presence, element chip switching, experiment handoff, and assessment/report flow.
- `npm run build --prefix apps/student-web`
  - Passed. Production bundle includes the integrated Zdog viewer; no iframe or standalone prototype server is required.
- `STUDENT_H5_QA_MOCK=1 STUDENT_H5_URL=http://127.0.0.1:5183 npm run qa:mobile --prefix apps/student-web`
  - Passed for 360x780, 390x844, and 430x932 viewports.
  - QA checks atom model card visibility, element chip switching, orbital mode reachability, no horizontal overflow, and nonblank canvas pixels in a real browser.
- `openspec validate student-h5-zdog-atom-model-card --strict`
  - Passed.
- `git diff --check`
  - Passed with line-ending warnings only.

## Rollback Notes

- The standalone prototype at `C:\Users\38122\Documents\zdog` is not referenced at runtime.
- New seed/API fields are optional on the frontend type and nullable in the backend schema, so older consumers can ignore them.
- The previous selected-element fact panel can be restored by reverting `LearningFactsView` integration and the `atom-viewer` feature files without changing the underlying learning page contract.
