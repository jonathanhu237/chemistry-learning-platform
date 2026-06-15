## Why

The current 2,310-question experiment bank is valid as draft data, but it is not suitable as the default production bank as-is: questions are experiment-linked but not bound to existing experiment video points, many items are too shallow, and fill-blank questions can be awkward for phone input. The completed `EXP_19_1_01` demo proves the desired workflow: review existing questions one by one, bind them to experiment video points, audit canonical evidence, and rewrite unsuitable items with concrete replacements.

## What Changes

- Review the existing 2,310-question experiment bank question by question rather than discarding it and generating an unrelated lower-count bank.
- Preserve an old question only when it passes source audit, point binding, answer-shape, and mobile-suitability review.
- Rewrite shallow or phone-unfriendly questions with concrete replacement questions; reject only when the item cannot be supported, and provide a replacement so per-experiment coverage is not lost.
- Use existing experiment video points from `formal_experiments.metadata.video_candidates` as the primary question binding target.
- Allow each question to bind to one or more video point keys and coverage tags.
- Add option-level point and misconception links for single-choice questions.
- Keep the student-facing types limited to `single_choice`, `true_false`, and `fill_blank`.
- Keep fill-blank grading deterministic and phone-friendly; long reagent combinations, full equations, and free-form reasoning SHALL be rewritten as single-choice/true-false or short-token fill blanks.
- Require canonical experiment evidence first, with theory chunks only as supporting evidence when explicitly cited.
- Require every kept, repaired, or rewritten question to include source audit metadata, reviewer decision, point bindings, and deterministic answer data.
- Treat the old 2,310-question bank as the primary review source, but not as content that can survive without review.
- Produce a full reviewed artifact and import path that can replace the default bank only after validation passes.

## Capabilities

### New Capabilities

- `experiment-video-point-question-binding`: Defines full-bank question-to-video-point bindings, option-level links, coverage tags, source audits, and review decisions.

### Modified Capabilities

- `experiment-question-bank-management`: Replace the default bank seeding contract with a reviewed point-aware version of the existing bank and stricter objective question quality rules.
- `class-learning-analytics`: Consume question-level and option-level video point links so incorrect answers can be attributed to experiment points and misconceptions.

## Impact

- Backend question bank import and validation scripts.
- Question storage schema or metadata shape for `primary_point_keys`, `coverage_tags`, `option_links`, `source_audit`, and review lineage.
- Admin question bank browsing and detail display may show video point links and review/source status.
- Student grading remains deterministic; no AI-based correctness grading is introduced.
- Learning analytics can aggregate by experiment, video point, option-level misconception, and chapter/KP where available.
- No live bank replacement should occur until the full regenerated artifact passes strict validation and is explicitly imported.
