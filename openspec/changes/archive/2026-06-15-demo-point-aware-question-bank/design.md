## Context

The current imported draft bank contains 2,310 objective questions, but the questions are only linked to formal experiments and source chunks. They do not have bindings to the existing experiment video points, and single-choice options cannot explain which point or misconception a wrong answer represents.

The demo is intentionally small: it covers only `EXP_19_1_01` (`19-1-01 氯、溴、碘的置换次序`). The aim is to prove the review workflow and data shape before expanding to all 77 formal experiments.

## Goals / Non-Goals

**Goals:**
- Build a point-aware demo for one formal experiment.
- Reuse the experiment video points already defined under the formal experiment.
- Review a small question sample one by one, against source text.
- Produce question-level and option-level point bindings where justified.
- Flag questions that are too trivial, under-evidenced, or unsuitable for learning analytics.
- Produce a concrete replacement question for every rewrite decision.

**Non-Goals:**
- Do not rebuild the full question bank.
- Do not publish or replace student-facing questions.
- Do not use keyword matching as the final binding method.
- Do not require UI changes for this demo.
- Do not force every old question to survive; rejection and rewrite are valid outcomes.

## Decisions

### Decision: Use existing experiment video points as the binding target

The demo SHALL use the existing video points produced from `formal_experiments.metadata.video_candidates` as the final binding target. The reviewer SHALL NOT invent a separate `EXPPOINT_*` catalog for final question bindings.

Binding targets for `EXP_19_1_01`:

- `candidate-1-034a8366`: `氯水 + KBr 溶液 + CCl₄`
- `candidate-2-1e180c68`: `氯水 + KI 溶液 + CCl₄`
- `candidate-3-9b8be606`: `溴水 + KI 溶液 + CCl₄`

Method and conclusion concepts such as `CCl4 observation layer` or `oxidation order` MAY be recorded as coverage tags, but they SHALL NOT replace the existing video point key as the final analytics binding.

### Decision: Manual review is the authority

Keyword, embedding, or string matching MAY suggest candidate points, but the final output SHALL be made by reading each question and its cited source. The review record must explain why the binding is accepted, rejected, or uncertain.

### Decision: Store option-level links for single-choice questions

For single-choice questions, the correct option and distractors can bind to different points or misconceptions. This supports later analytics where a wrong selected option can attribute weakness more specifically than the whole question.

Example output shape:

```json
{
  "question_id": "cf9095ea-ef93-4241-a31d-38e200cf80bd",
  "review_status": "rewrite",
  "quality_flags": ["too_basic"],
  "primary_point_keys": ["candidate-1-034a8366", "candidate-2-1e180c68", "candidate-3-9b8be606"],
  "coverage_tags": ["ccl4_observation_layer"],
  "option_links": [
    {"label": "A", "point_key": "candidate-1-034a8366", "role": "distractor_misconception"},
    {"label": "B", "point_key": "candidate-1-034a8366", "role": "correct_evidence"},
    {"label": "C", "point_key": "candidate-1-034a8366", "role": "distractor_misconception"},
    {"label": "D", "point_key": null, "role": "unrelated_distractor"}
  ],
  "proposed_question": {
    "question_type": "single_choice",
    "stem": "在氯水、KBr 溶液和 CCl₄ 的实验中，加入 CCl₄ 后重点观察有机层颜色，主要是为了判断哪件事？",
    "answer": {"value": "B"}
  },
  "source_audit": {
    "canonical_chunk_ids": ["expchunk_00199_8240477bff"],
    "evidence_sufficient": true,
    "review_note": "The source supports CCl4 as part of the designed halogen displacement experiments; the existing question is answerable but too shallow as a final diagnostic item."
  }
}
```

### Decision: Low-quality questions are rewritten or rejected

The demo review SHALL not preserve questions only because they are valid JSON. Low-quality patterns include direct formula recitation, direct equation-writing, pure terminology recall, one-step obvious facts, answers not grounded in cited evidence, and questions whose options do not diagnose different points.

Every `rewrite` decision SHALL include a concrete `proposed_question` object with deterministic answer data.

### Decision: Fill blanks stay objective and mobile-friendly

The demo SHALL keep only single choice, true/false, and fill-blank question types. Fill-blank questions SHALL remain machine-graded by accepted answers; the demo SHALL NOT depend on AI semantic grading for correctness.

Mobile-suitable fill blanks SHOULD ask for a short token or phrase such as one ion, one substance, one relation word, or one observation word. A fill blank SHALL be marked for rewrite when the expected answer is a long reagent combination, full equation, multi-clause explanation, or anything that would be awkward to type on a phone.

### Decision: Demo output remains separate from production data

The demo SHALL write review artifacts only. A later full change can decide whether to introduce new database tables for question-to-video-point links, or to stage links in question metadata first.

## Risks / Trade-offs

- Manual review is slower than automated matching -> scope the demo to one experiment and use it to estimate full effort.
- Canonical experiment chunks sometimes omit detailed observed phenomena -> mark evidence as insufficient instead of hallucinating; allow optional theory or local supplement evidence only when explicitly cited.
- Old questions may mostly be too basic -> treat old bank as candidate material, not as a required survivor set.
- Option-level links add schema complexity -> prove the value in the demo before making a full migration.

## Demo Output

The implementation task should produce a review artifact shaped like:

```text
artifacts/point-aware-question-demo/EXP_19_1_01/
  assessment_points.json
  reviewed_questions.json
  review_report.md
```

The report should be readable by the product owner before any full-scale spec is proposed.
