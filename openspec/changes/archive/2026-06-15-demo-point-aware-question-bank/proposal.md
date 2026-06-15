## Why

The current experiment question bank is experiment-linked but not point-aware: questions have source chunks yet no stable experiment point bindings, no option-level bindings, and no reliable basis for learning analytics. Before rebuilding the full bank, we need a small, inspectable demo that proves the manual review workflow and data shape are correct.

## What Changes

- Create a limited point-aware question bank demo for `EXP_19_1_01` only.
- Reuse the existing experiment video points from formal experiment `video_candidates`; do not introduce a separate demo-only point catalog for final bindings.
- Define how one question can bind to one or more existing video points.
- Define how single-choice options can bind to existing video points, point evidence, or misconceptions.
- Require manual, per-question review against canonical source text; keyword matching may only propose candidates and SHALL NOT decide final bindings.
- Mark low-quality questions, including direct equation-recitation, reagent-combination fill blanks, or trivial fact recall, for rewrite or rejection.
- Require every rewrite decision to include a concrete proposed rewritten question, not only a direction.
- Keep fill-blank questions machine-gradable and mobile-friendly; do not use AI grading for correctness in this demo.
- Keep the demo outside published student-facing bank data until explicitly promoted by a later full change.

## Capabilities

### New Capabilities
- `experiment-assessment-point-binding`: Defines bindings from questions/options to existing experiment video points, plus manual review rules for analytics-ready questions.

### Modified Capabilities
- `experiment-question-bank-management`: Adds a small demo workflow for point-aware question generation/review without changing the full default question bank yet.

## Impact

- Data model planning for video-point-aware question bindings.
- Question bank generation and import workflow planning.
- Future analytics attribution for incorrect answers.
- No production data mutation in this demo proposal.
