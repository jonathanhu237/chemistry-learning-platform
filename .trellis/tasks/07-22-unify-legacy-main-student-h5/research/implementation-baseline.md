# Implementation baseline

Recorded before product-code changes on 2026-07-22.

## Git safety point

- `main` / `origin/main`: `e113b2ed0b122f96c28b8b421ceb5441c236f84e`
- `legacy`: `9a3d3559d23d062e353a914a49e86aa2f0206536`
- merge base: `3096f82d6b282d6a637910960c3123a2c7963d20`
- ahead counts (`main`, `legacy`): `11`, `117`
- safety tag: `pre-legacy-reconciliation-20260722-e113b2e`

The user-owned modification at `artifacts/catalog_outline_seed_validation_report.json` was copied outside the repository to `/tmp/chemistry-learning-platform-pre-legacy-artifact-20260722-e113b2e.json`. Both copies had SHA-256 `8e6d89e5f3ca6facf2f1118de3e5add2e476f4e3eb9a4726e5a3a91205cd8b85` at the safety point.

## Pre-existing validation state

- Backend: `711 passed`, `2 failed`, `14 skipped`.
  - `test_runtime_consumer_import_boundaries`: `assessments/reports.py` already imports the disallowed assistant provider module.
  - `test_question_workbench_generates_draft_from_prebound_catalog_evidence`: the local effective configuration reports textbook RAG disabled, so the fixture receives HTTP 409.
- Teacher typecheck: passed.
- Student typecheck: passed after installing the lockfile dependencies with `npm ci`; the initial attempt only failed because `node_modules/tsc` was absent.

These two backend failures are baseline defects/environment state, not reconciliation regressions. The final gate should either fix them when naturally touched or continue to report them explicitly.

## Merge preview risk

`git merge-tree --write-tree --messages main legacy` reports 21 explicit conflicts. Its automatic tree also performs non-conflicting destructive changes, including switching the canonical entrypoints to `LegacyStudentApp` / `LegacyTeacherApp` and deleting retained modern components, scripts, tests, dependencies, and visual assets. Conflict-marker resolution alone is therefore insufficient; the reviewed current runtimes are protected baselines.
