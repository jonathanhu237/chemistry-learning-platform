## 1. Source And Point Inventory

- [x] 1.1 Export the 77 published formal experiments with code, title, chapter bindings, metadata, and `video_candidates`.
- [x] 1.2 Resolve existing video point keys and titles for every formal experiment using the same backend key-generation logic as the admin video-point API.
- [x] 1.3 Join each formal experiment to canonical experiment chunks and available supporting theory chunks.
- [x] 1.4 Produce an inventory audit listing experiments with missing canonical evidence, missing video points, duplicate point titles, or stale point keys.

## 2. Artifact Schema And Validators

- [x] 2.1 Define the full regenerated question artifact schema with experiment id, question type, deterministic answer, point keys, coverage tags, option links, source audit, and review lineage.
- [x] 2.2 Implement validation for objective type constraints, answer shape, fill-blank phone suitability, and deterministic grading.
- [x] 2.3 Implement validation that every accepted question references existing video point keys for its formal experiment.
- [x] 2.4 Implement validation for source audit completeness and evidence sufficiency decisions.
- [x] 2.5 Implement validation for single-choice option links, including correct evidence, misconception, adjacent experiment, adjacent point, weak distractor, and unrelated distractor roles.

## 3. Full Generation And Review Workflow

- [x] 3.1 Create the generation prompt/schema that starts from formal experiment video points and canonical chunks rather than the old question bank.
- [x] 3.2 Generate a candidate batch for a small representative set of experiments beyond `EXP_19_1_01` to confirm the workflow scales across different experiment shapes.
- [x] 3.3 Review the representative batch question by question and revise the schema or rules if recurring quality issues appear.
- [x] 3.4 Generate the full 77-experiment candidate artifact.
- [x] 3.5 Review or batch-audit every candidate question for chemical correctness, source grounding, point binding, option quality, and phone suitability.
- [x] 3.6 Ensure every `rewrite` candidate has a concrete proposed replacement question before final acceptance.

Note: tasks 3.4-3.6 produced and audited a full point-coverage scaffold, not a production-quality default bank. See `artifacts/point-aware-question-bank/full_candidate_scaffold_quality_audit.md`.

## 4. Import And Bank Versioning

- [x] 4.1 Add or adapt backend import code so the regenerated artifact imports into a staging/default-bank version without partial publication.
- [x] 4.2 Store point bindings, coverage tags, option links, source audit, and review lineage in queryable database fields or metadata.
- [x] 4.3 Preserve the current bank as an archived or rollback version before promoting the regenerated bank.
- [x] 4.4 Expose imported point/source metadata in existing read-only question bank browsing and question detail views.

## 5. Analytics Integration

- [x] 5.1 Persist student answer events with question id, correctness, experiment id, and point keys for point-aware questions.
- [x] 5.2 Capture selected option labels for single-choice attempts so option-level diagnostic links can be used later.
- [x] 5.3 Add class analytics aggregation by experiment video point, incorrect rate, attempt count, and representative questions.
- [x] 5.4 Add weak-point reporting behavior for point-aware questions that do not have theory KP mappings.

## 6. Validation And Sign-Off

- [x] 6.1 Run the full regenerated artifact validator and produce a coverage/quality audit report.
- [x] 6.2 Verify zero accepted questions have unresolved point keys, missing source audit, unsupported evidence, non-deterministic answers, or phone-unfriendly fill blanks.
- [x] 6.3 Run backend tests covering import validation, point binding persistence, and analytics aggregation.
- [x] 6.4 Run frontend typecheck/build if admin metadata display changes are implemented.
- [x] 6.5 Run `openspec validate regenerate-point-aware-question-bank --strict`.

## 7. Old 2,310-Question Bank Review

- [x] 7.1 Create five self-contained review prompt files for parallel review of the old 2,310-question bank.
- [x] 7.2 Review chunk 1 (`19-1-01` through `19-3-02`, 450 questions) and write reviewed artifact plus report.
- [x] 7.3 Review chunk 2 (`19-3-03` through `19-6-01`, 450 questions) and write reviewed artifact plus report.
- [x] 7.4 Review chunk 3 (`19-6-02` through `20-1-01`, 450 questions) and write reviewed artifact plus report.
- [x] 7.5 Review chunk 4 (`20-1-02` through `20-2-07`, 450 questions) and write reviewed artifact plus report.
- [x] 7.6 Review chunk 5 (`20-2-08` through `20-3-14`, 510 questions) and write reviewed artifact plus report.
- [x] 7.7 Merge the five reviewed chunks into one reviewed old-bank artifact and validate source audit, point keys, option links, replacement coverage, and phone-friendly fill blanks.

Note: tasks 7.2-7.6 passed the five-chunk audit in `artifacts/point-aware-question-bank/reviewed_old_bank_chunks/five_chunk_review_audit.md`.
