## Context

Current assessment behavior:

```text
Student opens /assessment
        │
        ▼
Start existing posttest
        │
        ├─ Finds experiments opened after the latest completed posttest
        ├─ Samples published questions from those experiments
        └─ Fails when there is no eligible learning activity
```

Existing data that should be reused:

- `student_experiment_mastery`: per-student, per-experiment mastery with `mastery_score`, `mastery_prob`, and `evidence_count`.
- `experiment_questions`: published question bank tied to formal experiments.
- `experiment_question_attempts`: graded attempt history that can store `attempt_kind = "smart_assessment"`.
- `platform_settings`: existing global learning behavior settings.
- class ownership and registration settings patterns in class management.

## Decisions

### 1. Smart Assessment Is Separate From Posttest

Create a dedicated smart-assessment session concept:

```text
student_smart_assessment_sessions
├─ id
├─ student_id / class_id
├─ status
├─ strategy_snapshot
├─ selected_experiment_ids
├─ question_ids
├─ mastery_before
├─ report
├─ created_at
└─ completed_at
```

Rationale: existing posttest is scoped to recently learned experiments. Smart assessment has a different entry point, strategy, report explanation, and admin configuration. Keeping it separate prevents "posttest" from becoming a catch-all.

### 2. Compose By Experiment First, Then Question

Composition order:

```text
1. Resolve effective strategy for the student class
2. Split target question count into untested and measured quotas
3. Select untested experiments from the untested pool
4. Select measured experiments using mastery-based tickets
5. Select questions inside selected experiments
6. Backfill from eligible candidates when an experiment or pool lacks enough questions
```

The unit of weighting is the experiment because mastery is experiment-level. Question selection happens after experiments are selected so experiments with larger question banks do not dominate the paper.

### 3. Untested Means No Answer Evidence

Untested experiments are not mapped to a default mastery score.

```text
Untested experiment
├─ no student_experiment_mastery row
└─ or evidence_count = 0

Measured experiment
└─ student_experiment_mastery row with evidence_count > 0
```

The first version intentionally ignores whether the student opened, watched, or viewed the experiment. "Untested" means no scored evidence.

### 4. Teacher-Facing Strategy Parameters

Effective strategy fields:

```text
SmartAssessmentStrategy
├─ enabled
├─ question_count
├─ untested_ratio_percent
├─ weak_tendency_percent
├─ max_questions_per_experiment
└─ curve parameters hidden behind defaults
```

Recommended defaults:

```text
question_count = 10
untested_ratio_percent = 20
weak_tendency_percent = 70
max_questions_per_experiment = 2
```

Admins can set global defaults. Teachers can override strategy for classes they own or are allowed to manage. Students only use the resolved effective strategy.

### 5. Weak Tendency Uses Draw Tickets

The UI should explain the model as tickets, not as opaque probability math.

Every measured experiment receives a base ticket count. Lower mastery scores add extra tickets when weak tendency is enabled:

```text
weakness = ((100 - mastery_score) / 100) ^ curve
tickets = 1 + weak_bias * max_bonus * weakness

weak_bias = weak_tendency_percent / 100
```

Teacher intuition:

```text
weak_tendency = 0%
  → measured experiments are approximately balanced

weak_tendency = 100%
  → low mastery experiments receive many more tickets
```

Example with `curve = 2`, `max_bonus = 9`, and `weak_tendency = 100%`:

```text
mastery 20: 1 + 9 * 0.8^2  = 6.76 tickets
mastery 50: 1 + 9 * 0.5^2  = 3.25 tickets
mastery 80: 1 + 9 * 0.2^2  = 1.36 tickets
mastery 95: 1 + 9 * 0.05^2 = 1.02 tickets
```

The exact defaults can be tuned during implementation, but the product contract is:

- low mastery receives more draw opportunity,
- high mastery remains possible,
- no hard threshold such as 59 vs 60 is required.

### 6. Untested Ratio Is A Separate Quota

Untested experiments do not enter the mastery curve. Their ratio controls a reserved paper quota:

```text
10-question paper
untested_ratio_percent = 20

2 questions from untested experiments
8 questions from measured experiments using mastery tickets
```

If the untested pool cannot fill the quota, the measured pool backfills. If the measured pool cannot fill, available published experiment questions backfill while preserving no-answer exposure.

### 7. Admin Preview Is Part Of The Feature

The feature must make the strategy understandable before it is saved.

Admin global settings and class settings should show:

```text
Strategy curve
mastery score → relative draw tickets

Class preview
current class mastery data → estimated experiment/source distribution
```

Recommended presentation:

```text
┌─────────────────────────────────────────┐
│ Smart Assessment Strategy               │
├─────────────────────────────────────────┤
│ Untested ratio: 20%                     │
│ Weak tendency: 70%                      │
│ Max questions per experiment: 2         │
│                                         │
│ mastery 100 ─╮                          │
│ mastery  80 ───╮                        │
│ mastery  60 ─────╮                      │
│ mastery  40 ─────────╮                  │
│ mastery  20 ─────────────╮              │
│ mastery   0 ─────────────────╮          │
└─────────────────────────────────────────┘
```

Use "relative draw tickets" for the strategy curve, not final probability. Final probability depends on the class's actual experiment set, mastery distribution, question availability, and untested ratio.

### 8. Student Report Explains The Paper

Before or during a smart assessment, students should see a concise explanation:

```text
本次智能组卷优先覆盖 mastery 较低的实验，并包含 2 道未测实验题。
```

After submission, the report should include:

- score and correct rate,
- selected experiment summaries,
- group composition summary,
- mastery before/after changes for involved experiments,
- wrong answers and explanations where existing report patterns allow them.

### 9. Open Session Reuse

If a student has an in-progress smart assessment session, starting smart assessment returns that same session. This avoids repeated clicks or refreshes changing the paper.

### 10. Backfill Rules

The paper should prioritize reaching the configured total question count:

```text
Pool quota underfilled
        │
        ▼
Backfill from eligible remaining experiments/questions
        │
        ▼
Preserve no-answer exposure and record warnings in strategy_snapshot
```

Backfill warnings should be visible in admin preview and stored in session metadata for diagnosis.

## Risks / Trade-offs

- Ticket curves can feel arbitrary if not visualized; the preview is required to maintain teacher trust.
- Class overrides add complexity to settings ownership; reuse existing class-management access checks.
- Untested ratio can create papers that include content students have not learned; this is intentional when configured, but the UI must label it as exploration.
- Reusing `experiment_question_attempts` keeps mastery updates consistent, but reports must distinguish `smart_assessment` attempts from pretest and posttest.
- If a class has sparse mastery evidence, the measured pool may be small; backfill and preview warnings are important.
