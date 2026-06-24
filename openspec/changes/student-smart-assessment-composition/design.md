## Context

Current assessment behavior:

```text
Student opens /assessment
        |
        v
Start existing posttest
        |
        |- Finds experiments opened after the latest completed posttest
        |- Samples published questions from those experiments
        `- Fails when there is no eligible learning activity
```

Relevant existing assets:

- `experiment_questions`: published question bank with catalog point placement metadata.
- `experiment_question_attempts`: graded attempt history that can store assessment attempt kinds.
- Catalog tree point nodes: the student-visible point placement under root/first-level experiment entries.
- `platform_settings`: existing global learning behavior settings.
- Class ownership and registration settings patterns in class management.
- `student_experiment_mastery`: pre-release experiment-level mastery storage that can be migrated or replaced.

New product shape:

```text
Student opens /assessment
        |
        |- Smart assessment
        |  `- System composes from the full point-backed question bank
        |
        `- Custom assessment
           `- Student chooses root experiments and question count
```

Product decision: the smallest diagnostic unit is the catalog `point_node_id`. Experiments remain the student-facing entry and report grouping layer, but they are no longer the factual mastery grain.

## Decisions

### 1. Smart Assessment Is Separate From Posttest

Create a dedicated assessment session concept initially backed by the smart-assessment session table:

```text
student_smart_assessment_sessions
|- id
|- student_id / class_id
|- status
|- assessment_mode = "smart" | "custom"
|- strategy_snapshot
|- selected_experiment_ids
|- selected_point_node_ids
|- question_ids
|- mastery_before
|- report
|- created_at
`- completed_at
```

Rationale: existing posttest is scoped to recently learned activity. Smart assessment has a different entry point, strategy, report explanation, and admin configuration. Keeping it separate prevents "posttest" from becoming a catch-all.

Custom assessment should use separate student API routes but reuse this session lifecycle and completion/report mechanics. The table name can remain `student_smart_assessment_sessions` for the first implementation to avoid broad migration churn; `assessment_mode` distinguishes system-composed and student-selected papers.

### 2. Point Mastery Is The Fact Source

Add point-level mastery storage:

```text
student_point_mastery
|- student_id
|- class_id
|- point_node_id
|- experiment_id
|- canonical_point_id
|- mastery_prob
|- mastery_score
|- evidence_count
|- last_evidence_kind
|- metadata
|- created_at
`- updated_at

primary key: student_id + point_node_id
```

Experiment mastery is not written as a separate fact. It is derived for display and analytics by aggregating descendant point mastery under the root/first-level experiment.

Recommended display aggregation:

```text
experiment mastery score = average measured descendant point score
coverage = measured descendant points / total descendant question-backed points
```

Untested points do not receive a visible fake score. A point with no row or `evidence_count = 0` is shown and composed as untested. Internally, the first BKT update can use `prior = 0.5`; that prior is not a student-visible mastery score.

Because the app is not yet released, the old `student_experiment_mastery` table does not need long-term compatibility. Migration may replace it with `student_point_mastery`. Existing rows with a reliable `point_node_id` can be migrated to that point; rows without point identity should not be exploded across every point in an experiment because that would create fabricated evidence.

### 3. Eligible Assessment Questions Must Be Point-Backed

Smart and custom assessment may only draw questions that are:

```text
published
+ student-visible
+ bound to at least one valid point_node_id
```

Questions without point placement may remain in the question bank, but they are not eligible for assessment composition because they cannot be attributed to point mastery or explained in reports.

If a question is bound to multiple valid point nodes, a graded answer updates every bound point in `student_point_mastery` using the same result. The first version does not split evidence weights across points.

### 4. Smart Assessment Composes By Point

Smart assessment does not ask the student to choose a range. Its candidate range is the full published, point-backed question bank.

Composition order:

```text
1. Resolve effective strategy for the student's class.
2. Load all eligible point-backed candidates from the full question bank.
3. Build point pools and root-experiment grouping from catalog placement.
4. Split target question count into untested-point and measured-point quotas.
5. Select untested points from points with no scored evidence.
6. Select measured points using point mastery tickets.
7. Select at most one question per selected point.
8. Enforce max questions per root/first-level experiment where possible.
9. Backfill from eligible remaining points/questions if a quota or group underfills.
```

The unit of weighting is the point. The experiment cap is only a diversity constraint so one root experiment cannot dominate the paper.

Default constraints:

```text
max_questions_per_point = 1
max_questions_per_experiment = effective teacher setting
```

`max_questions_per_point = 1` can be a fixed first-version rule. If the question bank lacks enough eligible points, backfill may relax coverage only after exhausting one-question-per-point candidates and must record warning metadata.

### 5. Teacher-Facing Strategy Parameters

Effective strategy fields:

```text
SmartAssessmentStrategy
|- enabled
|- question_count
|- untested_ratio_percent
|- weak_tendency_percent
|- max_questions_per_experiment
`- curve parameters hidden behind defaults
```

Teacher-facing semantics:

- `untested_ratio_percent` means untested point quota, not untested experiment quota.
- `max_questions_per_experiment` means maximum questions under one root/first-level experiment.
- Students do not control smart-assessment strategy or range.
- Composition must read the effective settings; the untested ratio must not be hard-coded.

Recommended defaults remain:

```text
question_count = 10
untested_ratio_percent = 20
weak_tendency_percent = 70
max_questions_per_experiment = 2
```

Admins can set global defaults. Teachers can override strategy for classes they own or are allowed to manage. Students only use the resolved effective strategy.

### 6. Weak Tendency Uses Point Draw Tickets

The UI should explain the model as tickets, not as opaque probability math.

Every measured point receives a base ticket count. Lower point mastery scores add extra tickets when weak tendency is enabled:

```text
weakness = ((100 - mastery_score) / 100) ^ curve
tickets = 1 + weak_bias * max_bonus * weakness

weak_bias = weak_tendency_percent / 100
```

Teacher intuition:

```text
weak_tendency = 0%
  -> measured points are approximately balanced

weak_tendency = 100%
  -> low mastery points receive many more tickets
```

Product contract:

- low point mastery receives more draw opportunity,
- high mastery remains possible,
- no hard threshold such as 59 vs 60 is required.

### 7. Untested Ratio Is A Separate Point Quota

Untested points do not enter the mastery curve. Their ratio controls a reserved paper quota:

```text
10-question paper
untested_ratio_percent = 20

2 questions from untested points
8 questions from measured points using mastery tickets
```

If the untested point pool cannot fill the quota, the measured pool backfills. If the measured pool cannot fill, available published point-backed questions backfill while preserving no-answer exposure where possible.

### 8. Custom Assessment Uses Experiment Selection, Point Coverage

Custom assessment is a separate student-selected mode, not a filter on smart assessment.

Student flow:

```text
/assessment
  |- 智能测评: 系统自动组卷
  `- 自主测评: 学生选择实验

/assessment/custom
  |- search published root/first-level experiments with eligible questions
  |- select one or more experiments
  |- choose question count from 5 / 10 / 15 / 20
  `- start custom assessment
```

Custom assessment v1 intentionally does not include:

- weak-point shortcut entry,
- untested/measured/weak filters,
- wrong-answer related experiment selection,
- point selection,
- student-facing strategy controls.

When the student selects experiments, the backend expands each selected root/first-level experiment to descendant point nodes and draws only from eligible questions under those points.

Sampling:

```text
1. Divide requested question count approximately evenly across selected experiments.
2. Within each selected experiment, prefer point coverage: at most one question per point first.
3. Stable-shuffle candidate questions inside each point.
4. If an experiment lacks enough eligible point questions, redistribute remaining slots to other selected experiments.
5. Return an underfilled paper with warnings if selected experiments cannot fill the requested count.
```

Custom assessment does not apply weak/untested mastery weighting. Its first promise is simple student control: "I choose which experiments to test."

### 9. Reports Group By Experiment, Diagnose By Point

Before or during a smart assessment, students should see a concise explanation:

```text
本次智能组卷优先覆盖掌握较弱的点位，并包含若干未测点位题。
```

After submission, the report should include:

- score and correct rate,
- experiment cards as the first layer,
- point mastery before/after changes inside each experiment,
- point coverage such as `已测点位 / 总点位`,
- composition summary,
- wrong answers and explanations where existing report patterns allow them.

Report shape:

```text
测评报告
  实验 A: 掌握度 78%, 已测 6/18, 薄弱 3
    点位 A-1: 82% ↑
    点位 A-2: 未测
    点位 A-3: 41% ↓
  实验 B: 掌握度 64%, 已测 4/12, 薄弱 2
```

Experiment mastery in the report is a derived display value from point mastery snapshots. It is not a separate write path.

### 10. Admin Preview Is Part Of The Feature

The feature must make the strategy understandable before it is saved.

Admin global settings and class settings should show:

```text
Strategy curve
point mastery score -> relative draw tickets

Class preview
current class point mastery data -> estimated point/source distribution
```

Recommended presentation:

```text
┌─────────────────────────────────────────┐
│ Smart Assessment Strategy               │
├─────────────────────────────────────────┤
│ Untested point ratio: 20%               │
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

Use "relative draw tickets" for the strategy curve, not final probability. Final probability depends on the class's actual point mastery distribution, question availability, untested ratio, and root-experiment caps.

### 11. Open Session Reuse

If a student has an in-progress smart assessment session, starting smart assessment returns that same session. This avoids repeated clicks or refreshes changing the paper.

The same first-version rule applies across assessment modes: a student may have only one in-progress assessment session at a time. Starting smart or custom assessment while any assessment session is open returns the existing session instead of creating a second paper. The first version does not add "abandon and start over".

### 12. Backfill Rules

The paper should prioritize reaching the configured total question count without losing point attribution:

```text
Pool quota underfilled
        |
        v
Backfill from eligible remaining point-backed questions
        |
        v
Preserve no-answer exposure and record warnings in strategy_snapshot
```

Backfill warnings should be visible in admin preview and stored in session metadata for diagnosis.

### 13. Custom Assessment Settings

Global and class settings should include custom assessment controls:

```text
CustomAssessmentSettings
|- enabled = true
|- default_question_count = 10
|- max_question_count = 20
`- max_questions_per_experiment = 3
```

Allowed student question count options are fixed to `5 / 10 / 15 / 20`; the UI hides options above `max_question_count`. The default question count must be one of the visible options.

## Risks / Trade-offs

- Point-level mastery is a schema change, but the app is pre-release, so replacing the experiment-level fact table is cleaner than carrying two mastery sources.
- Ticket curves can feel arbitrary if not visualized; the preview is required to maintain teacher trust.
- Class overrides add complexity to settings ownership; reuse existing class-management access checks.
- Untested ratio can create papers that include content students have not learned; this is intentional when configured, but the UI must label it as exploration.
- Reusing `experiment_question_attempts` keeps grading history close to existing assessment flows, but reports must distinguish `smart_assessment` and `custom_assessment` attempts from pretest and posttest.
- If a class has sparse mastery evidence, the measured point pool may be small; backfill and preview warnings are important.
