## Context

The student H5 now has smart and custom assessment entry points backed by `student_smart_assessment_sessions`. The domain already enforces one open assessment per student through a partial unique index on `student_id WHERE status = 'in_progress'`.

The point detail page currently exposes a "测一测" action, but it calls the shared smart-assessment start flow. That means a student who finishes a point can be routed into a full-bank smart paper instead of a focused check for the point just studied.

There is also no student-facing assessment status endpoint. The H5 only loads feature flags from `/api/student/app-config`, so the frontend cannot reliably decide whether a student has completed a smart baseline assessment or permanently dismissed the baseline prompt.

## Goals / Non-Goals

**Goals:**

- Add `assessment_mode = "point"` for point-scoped post-learning checks.
- Keep the existing one-open-assessment-per-student invariant.
- Add a student assessment status API for smart-baseline completion, open session continuation, and baseline prompt dismissal.
- Add a backend dismissal action that persists a student's "不再提醒" choice for the smart-baseline prompt.
- Add a first-entry H5 dialog for students who have not completed a smart assessment baseline.
- Route point detail "测一测" through point-scoped composition when no assessment is already open.
- Reuse the existing assessment session and report shell where possible.

**Non-Goals:**

- Do not add teacher-facing controls for point assessment question count in this change.
- Do not allow multiple simultaneous assessment sessions per student.
- Do not introduce a separate point-assessment table.
- Do not redesign the assessment report beyond labels and composition metadata needed for `point` mode.

## Decisions

### 1. Store point assessment in the existing session table

`student_smart_assessment_sessions.assessment_mode` will accept `smart`, `custom`, and `point`. Point assessments use existing `point_node_ids`, `source_placement_node_ids`, `question_ids`, `mastery_before`, `metadata`, and report fields.

Rationale: the existing lifecycle already supports open-session reuse, question lists, submission grading, BKT point mastery updates, and report storage. A new table would duplicate most behavior and complicate "one open assessment" enforcement.

### 2. Keep one open assessment per student

Point assessment start first calls the same open-session loader as smart/custom. If an open session exists, it returns that session instead of composing a point paper.

Rationale: the database already enforces this invariant. Preserving it avoids branching session recovery behavior and prevents students from accumulating several unfinished papers.

### 3. Compose point assessment by exact point placement

Point assessment start receives one `point_node_id`. It selects published, student-visible, point-backed questions whose assessment placement includes that point id. It targets 3 questions and allows underfilled papers down to 1 question. If no eligible question exists, the backend returns a conflict and does not create a session.

Rationale: the action is an immediate check after studying one point, not a broad experiment paper. Default 3 questions is short enough for the learning flow while still providing BKT evidence.

### 4. Add a dedicated assessment status API

Add:

```http
GET /api/student/assessment/status
POST /api/student/assessment/baseline-prompt-dismiss
POST /api/student/point-assessment/start
```

The status API returns whether the student has completed any `smart` assessment, whether an open assessment exists, the open session id/mode if present, and whether the student dismissed the smart-baseline prompt.

Rationale: `/api/student/app-config` is feature configuration, not student learning state. Assessment status has different semantics and will likely grow into badges/continuation affordances.

### 5. Persist baseline prompt dismissal as a student event

Use `student_events` with a dedicated event type such as `smart_baseline_prompt_dismissed`. The status API treats the presence of that event as permanent dismissal for that student.

Rationale: the app already has `student_events` for student-side behavior. This avoids a new preferences table for one persistent flag. A later reset feature can clear or supersede this event if product needs it.

### 6. Prompt priority in the H5 shell

The H5 shell fetches assessment status after authentication. It shows at most one dialog:

1. If there is an open assessment, prompt to continue it.
2. Else if no completed smart baseline and the prompt is not dismissed, prompt to take a smart assessment.
3. Else show no prompt.

The baseline dialog includes "去测评", "稍后", and "不再提醒". "不再提醒" calls the dismissal endpoint. The open-assessment prompt is not permanently dismissible.

Rationale: unfinished assessment recovery is state restoration; smart baseline is onboarding guidance. They should not share the same dismissal flag.

## Risks / Trade-offs

- **Point has too few questions** -> Allow underfilled 1-2 question sessions and surface warning metadata; return a clear conflict for 0 eligible questions.
- **Student expects point assessment but has an open smart/custom paper** -> Return the open session and show a frontend message before navigation so the student understands why the current paper is being continued.
- **`student_events` grows as a preference store** -> Limit this use to the baseline dismissal event; do not add broader preference semantics here.
- **Existing analytics still query legacy posttest tables** -> The status API must query `student_smart_assessment_sessions` directly for smart baseline completion.
