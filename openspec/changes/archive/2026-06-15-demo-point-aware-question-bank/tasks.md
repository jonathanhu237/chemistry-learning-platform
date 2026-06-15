## 1. Demo Evidence Pack

- [x] 1.1 Extract `EXP_19_1_01` formal experiment metadata, bound canonical chunks, and linked theory chunks into a local demo context.
- [x] 1.2 Read the canonical source text manually and draft 4-8 candidate assessment points for `19-1-01`.
- [x] 1.3 Mark each assessment point as `accepted`, `needs_evidence`, or `reject`, with source chunk ids and reviewer notes.

## 2. Per-Question Review

- [x] 2.1 Select a small sample of existing draft questions for `EXP_19_1_01` across choice, true/false, and fill-blank types.
- [x] 2.2 Review each sampled question one by one against the original source text, including stem, answer, options, and explanation.
- [x] 2.3 Assign question-level primary and secondary point bindings only when the evidence supports them.
- [x] 2.4 For single-choice questions, assign option-level links for correct evidence, distractor misconceptions, unrelated distractors, or uncertain options.
- [x] 2.5 Mark each question as `keep`, `rewrite`, or `reject`, and flag low-quality patterns such as equation-recitation, pure terminology recall, weak options, or unsupported explanation.

## 3. Demo Artifacts

- [x] 3.1 Create `artifacts/point-aware-question-demo/EXP_19_1_01/assessment_points.json`.
- [x] 3.2 Create `artifacts/point-aware-question-demo/EXP_19_1_01/reviewed_questions.json`.
- [x] 3.3 Create `artifacts/point-aware-question-demo/EXP_19_1_01/review_report.md` with a readable summary, examples, rejected/rewrite reasons, and open issues.
- [x] 3.4 Ensure demo artifacts are separate from production tables and do not mutate published or draft question bank data.

## 4. Validation

- [x] 4.1 Verify every accepted point has at least one source chunk id and reviewer note.
- [x] 4.2 Verify every reviewed question has a quality decision and source audit decision.
- [x] 4.3 Verify no final binding is justified by keyword matching alone.
- [x] 4.4 Run `openspec validate demo-point-aware-question-bank --strict`.

## 5. Demo Revision: Existing Video Points And Rewrites

- [x] 5.1 Replace demo-owned `EXPPOINT_*` bindings with existing experiment video point keys from the formal experiment video candidates.
- [x] 5.2 Keep the objective item types as single choice, true/false, and machine-gradable fill blank; forbid AI-based answer grading in this demo.
- [x] 5.3 Add mobile fill-blank constraints and mark reagent-combination blanks for rewrite.
- [x] 5.4 Add concrete proposed rewritten questions for every `rewrite` decision.
- [x] 5.5 Re-run JSON and OpenSpec validation.
