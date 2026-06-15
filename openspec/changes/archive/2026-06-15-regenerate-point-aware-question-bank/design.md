## Context

The current imported bank has 2,310 objective questions across 77 formal experiments. It passes structural validation, but it is not point-aware: questions do not bind to the experiment video points used by the admin resource workflow, single-choice options do not carry diagnostic links, and many fill blanks ask for phone-unfriendly chemical formulas, reagent combinations, or low-value recall.

The completed `demo-point-aware-question-bank` change validated a better shape on `EXP_19_1_01`: bind to existing video point keys, review source evidence manually, keep only deterministic objective types, and include a concrete replacement for each rewrite decision.

## Goals / Non-Goals

**Goals:**
- Review the existing 2,310-question default-bank candidate for all 77 formal experiments question by question.
- Keep high-quality old questions when they can be source-audited and bound to existing experiment video points.
- Rewrite or replace old questions that are too shallow, unsupported, or unsuitable for phone input.
- Use existing experiment video points as the primary analytics binding target.
- Preserve deterministic grading for `single_choice`, `true_false`, and `fill_blank`.
- Keep fill blanks suitable for phone input.
- Add question-level and option-level point links for learning analytics.
- Produce importable artifacts only after strict validation passes.
- Keep source audit and review lineage for every accepted question.

**Non-Goals:**
- Do not add AI semantic grading for student answers.
- Do not introduce new student-facing question types in this change.
- Do not require teachers to hand-create or upload the default bank through the admin UI.
- Do not discard the old 2,310 questions wholesale or replace them with an unrelated lower-count bank.
- Do not bind questions by keyword matching alone.

## Decisions

### Decision: Existing video points are the canonical experiment points

Each formal experiment already exposes video points through `metadata.video_candidates`, and the admin media workflow stores `point_key` / `point_title` on media bindings. The regenerated bank SHALL bind to those point keys.

Alternative considered: create a separate `experiment_assessment_points` catalog. This was rejected for the first full pass because it duplicates the resource model and risks making videos, questions, and analytics disagree.

### Decision: Coverage tags are secondary, not binding targets

Concepts such as `ccl4_observation_layer`, `oxidation_order`, `safety_observation`, or `reagent_role` are useful for review and coverage audits. They SHALL be stored as coverage tags, but the primary binding remains one or more existing video point keys.

### Decision: Full review is old-question-first and point-aware

The production workflow SHALL start from the old reviewed-bank candidate, not from a blank page:

```text
old question
  -> formal experiment
  -> existing video points
  -> canonical experiment chunks
  -> keep / rewrite / reject review
  -> concrete replacement when needed
  -> reviewed import artifact
```

This preserves useful old question work while fixing the current problem where a question belongs to an experiment but cannot be attributed to the specific experimental point that taught or diagnosed it.

### Decision: Fill blanks stay deterministic and short

Fill blanks are allowed only when accepted answers are short enough for phone input and can be normalized deterministically. Long reagent combinations, full equations, and free-form explanations SHALL be rewritten as single-choice or true/false.

Examples of acceptable fill blanks:
- one ion or formula: `I-`, `I2`, `CCl4`
- one short concept: `氧化性`, `还原性`
- one relation word: `强于`
- one observation word: `褪色`, `变蓝`

### Decision: Single-choice options carry diagnostic links

Single-choice questions SHALL store option-level links where meaningful. Correct options can reference the supporting point key; wrong options can reference a misconception, adjacent experiment, adjacent point, or `unrelated_distractor`. This gives class analytics a sharper signal than question-level correctness alone.

### Decision: Import validates before replacing the default bank

The regenerated bank SHALL be produced as an external artifact first. Import SHALL validate schema, point keys, source evidence, answer shape, type counts, duplicate risk, and phone-suitability before any database mutation. Replacement SHALL be an explicit backend/admin operation, not an automatic side effect of generation.

## Risks / Trade-offs

- Manual review is slower than pure generation -> use a structured review artifact and strict validators so review can be batched and audited.
- Some experiments may have few or broad video points -> allow questions to bind to multiple point keys and mark coverage gaps explicitly.
- Canonical chunks may omit detailed phenomena -> allow supporting theory chunks, but require source audit notes when evidence is inferred rather than directly stated.
- Option-level links add schema complexity -> allow initial storage in JSON metadata if migrations are not ready, while specs still require the data to be queryable for analytics.
- Replacing the bank can disrupt existing attempt references -> import should version the bank and preserve old question ids until a migration/retirement policy is chosen.

## Migration Plan

1. Produce a reviewed full-bank artifact outside production tables from the existing 2,310-question bank.
2. Run strict validation and produce an audit report.
3. Import into a staging status or new bank version.
4. Compare counts, coverage, and sample rendered questions in admin.
5. Explicitly promote the new version as the default bank.
6. Keep the old bank archived or disabled for rollback until new attempts stabilize.

Rollback: switch the active bank version back to the previous bank and keep regenerated artifacts for diagnosis.

## Open Questions

- Final accepted count should stay close to the existing 2,310-question bank. Rejected items should receive replacements unless evidence is genuinely missing.
- Storage can start as question metadata or use normalized link tables. The chosen implementation must still make analytics queries reliable.
- Some experiments may need supplemental phenomenon evidence beyond canonical chunks; those cases should be reported rather than silently filled.
