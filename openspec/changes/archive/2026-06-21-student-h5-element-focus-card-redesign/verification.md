## Verification

- `python -m pytest server/tests/test_student_learning.py::test_student_learning_profile_seed_is_valid server/tests/test_student_learning.py::test_student_learning_profile_seed_has_element_card_copy server/tests/test_student_learning.py::test_element_badges_expose_card_copy_and_preserve_detail_fields server/tests/test_student_learning.py::test_element_badges_allow_missing_card_copy_during_mapping_migration`
- `python -m pytest server/tests/test_student_learning.py`
- `python scripts\validate_production_resources.py --write-manifest`
- `python scripts\validate_production_resources.py`
- `npm run typecheck` from `apps/student-web`
- `npm run test:e2e` from `apps/student-web`
- `npm run build` from `apps/student-web`
- `STUDENT_H5_QA_MOCK=1 npm run qa:mobile` from `apps/student-web`
- `openspec validate student-h5-element-focus-card-redesign --strict`

## Mobile QA

`npm run qa:mobile` used the mock student API against `http://127.0.0.1:5173` and passed:

- 360x780 CSS pixels (`small-phone`)
- 390x844 CSS pixels (`regular-phone`)
- 430x932 CSS pixels (`large-phone`)

Covered flows include root navigation, video-library entry, chapter page, redesigned selected-element focus card, element detail, point detail, contextual AI, assessment handoff, feedback attachment, and direct detail routes.

The chapter page check also verifies that no header-level `问 AI` action is rendered on the selected family/chapter page; contextual AI remains covered from point detail and assessment/report surfaces.

## Remaining Risk

- Mobile QA used the mock API and local browser automation. Real device/WebView chrome can still differ slightly, but the checked phone viewport contract, horizontal overflow checks, focus-card text constraints, touch target checks, and first experiment-point visibility all passed.
