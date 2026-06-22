## 1. Backend Status Contract

- [x] 1.1 Add stable missing learning field keys and labels for experiment principle, phenomenon explanation, and safety note in the catalog node status helper.
- [x] 1.2 Preserve coarse `needs_content` behavior while making primary reasons list only the fields that are actually missing.
- [x] 1.3 Extend point status payloads additively so frontend code can read missing-field keys without parsing Chinese status copy.
- [x] 1.4 Extend directory descendant aggregates to include every filterable point state, including `ready`, `draft`, and `published`.
- [x] 1.5 Add directory descendant missing-field counts for principle, phenomenon, and safety.
- [x] 1.6 Extend chapter summary responses with point-level missing-field counts.

## 2. Frontend Filter Semantics

- [x] 2.1 Update catalog tree API TypeScript types for structured missing-field keys and missing-field count maps.
- [x] 2.2 Add focused status filter values for missing principle, missing phenomenon explanation, and missing safety note.
- [x] 2.3 Update filter chip rendering so coarse filters remain primary and focused missing-field filters render as lower-emphasis chips with counts.
- [x] 2.4 Update `matchesCatalogNodeStatusFilter` so direct points use `primary_state` and missing-field keys, while directories use descendant status and missing-field counts.
- [x] 2.5 Fix `待发布` and `已发布` filters so non-zero summary counts keep matching ancestor directories visible even before descendants are loaded.
- [x] 2.6 Keep text search rules unchanged and ensure status filters narrow search results using the same matcher as the tree.

## 3. Point Content Editor

- [x] 3.1 Rehome experiment principle into the `学生可见内容` section with `实验原理`, `现象解释`, and `安全提示` as peer required fields.
- [x] 3.2 Keep `化学方程式` and `文字描述` as input modes inside `实验原理`.
- [x] 3.3 Keep the existing equation input, preview, AI assist, candidate adoption, and save payload behavior intact while moving the section hierarchy.
- [x] 3.4 Add compact inline missing-field guidance near `学生可见内容` that lists only the missing fields.
- [x] 3.5 Add field-target links or equivalent focus behavior from the inline missing summary to the relevant fields.
- [x] 3.6 Tune CSS so the new student-visible content group remains compact and visually aligned with the current workbench design language.

## 4. Autosave and Hydration Safety

- [x] 4.1 Treat principle mode changes as node-scoped local transitions with a sequence or pending guard.
- [x] 4.2 Allow switching to an empty equation or text mode without reverting after autosave or query invalidation.
- [x] 4.3 Keep the destructive confirmation flow when switching away from non-empty principle content.
- [x] 4.4 Prevent stale detail hydration from overwriting the active node's newer principle mode while a save is pending or newer than the payload.
- [x] 4.5 Reset pending mode-switch guards when the selected catalog node changes.

## 5. Verification

- [x] 5.1 Add backend contract tests for missing one, two, and three learning fields.
- [x] 5.2 Add backend contract tests for directory descendant `ready`, `draft`, `published`, and missing-field aggregate counts.
- [x] 5.3 Add frontend mapper tests for `缺内容`, missing-field filters, `待发布`, and `已发布`.
- [x] 5.4 Add frontend content editor tests or contract assertions for the new `学生可见内容` grouping and inline missing guidance.
- [x] 5.5 Add focused coverage for principle mode switching to an empty mode without visual reversion.
- [x] 5.6 Run focused backend catalog tests.
- [x] 5.7 Run focused teacher frontend tests and typecheck.
- [x] 5.8 Run `openspec validate refine-catalog-content-readiness-filters --strict`.
