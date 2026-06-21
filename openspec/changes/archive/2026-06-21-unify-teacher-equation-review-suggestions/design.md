## Context

The previous natural equation work fixed the core authoring direction: teachers type or paste reaction text, the backend performs authoritative normalization, and AI/ES/RAG consume backend-generated structured records rather than frontend state. The remaining problem is the review model.

The current UI still exposes two different suggestion surfaces:

1. Parser preview rows under "系统理解为".
2. A separate "AI 建议" section below the preview.

That split makes teachers compare distant blocks and decide whether to copy text-like suggestions into chemistry content. It also makes parser and AI feel like competing systems, even though the backend already sends AI the point context, current input, and parser preview. The intended mental model is simpler: each input line is a reaction candidate, and all feedback for that line belongs next to that line.

Research references behind this direction:

- Code editors attach diagnostics and quick fixes to the affected line or problem context.
- Writing assistants attach suggestions to the selected/underlined text and provide accept/dismiss actions there.
- Chemistry formula editors emphasize natural input plus rendered notation; toolbar or AI assistance supports the editing surface but does not replace it.

## Goals / Non-Goals

**Goals:**

- Make the reaction review panel row-centered: one input line maps to one review row.
- Show teachers rendered chemical reaction candidates as the primary adoptable object.
- Merge deterministic parser suggestions and AI suggestions into the same per-row candidate area.
- Let teachers accept a rendered candidate without needing to understand whether it came from parser cleanup, balancing, or AI.
- Keep AI explicit and teacher-controlled: no automatic AI call on every keystroke.
- Ensure AI drafts are normalized by the backend before display so the UI never treats raw AI text as trusted chemistry notation.
- Reduce visual bulk by hiding diagnostics, raw text, formula token lists, and rationale behind compact details.

**Non-Goals:**

- Do not add a full chemical structure drawing editor.
- Do not make AI the authoritative parser or validator.
- Do not silently rewrite teacher input while typing.
- Do not autosave, publish, or index an accepted candidate without the normal point save flow.
- Do not expose RAG/chunk diagnostics or teacher-only AI internals to students.

## Decisions

### Decision 1: The review row is the unit of interaction

Each non-empty line in the multiline editor remains one reaction row. The preview UI should be organized around that row:

```text
实验反应式
[ multiline input ]

反应式检查                         [AI 校对全部] [重新检查]

1  2 NaNO2 + H2SO4 -> 2 HNO2 + Na2SO4        需确认
   系统识别：已规范大小写；疑似未配平

   推荐采用
   系统校对  2 NaNO2 + H2SO4 -> 2 HNO2 + Na2SO4    [采用这个反应式]
   AI 校对    2 NaNO2 + H2SO4 -> 2 HNO2 + Na2SO4    [采用这个反应式]

2  2 HNO2 -> N2O3 + H2O                       已识别
   无需修复
```

Alternative considered: keep a separate AI suggestions block. Rejected because it forces teachers to reconcile two sections and makes equations look like text suggestions.

### Decision 2: Adoptable candidates must be rendered formulas

Any candidate that has an "adopt" action must be displayed through the same chemistry rendering path used by canonical preview rows. The visible candidate should look like an equation, not a plain string.

Implementation implication: AI drafts should be normalized server-side into a candidate shape before reaching the UI:

```json
{
  "row_order": 3,
  "source": "ai",
  "raw_text": "2 N2O3 -> 2 NO + O2",
  "canonical_display": "2 N2O3 -> 2 NO + O2",
  "canonical_mhchem": "\\ce{2 N2O3 -> 2 NO + O2}",
  "validation_status": "valid",
  "rationale": "结合当前点位，建议补齐氧气产物以满足配平。"
}
```

The frontend may keep `raw_text` as the replacement value, but the teacher-facing control uses `canonical_mhchem` or `canonical_display`.

Alternative considered: render `draft_text` directly on the frontend. Rejected because AI text may contain casing, spacing, or invalid chemistry that has not passed the backend parser.

### Decision 3: Parser and AI are candidate sources, not separate sections

The row review model should combine:

- The current backend understanding of the teacher input.
- Deterministic backend correction/balancing suggestion, when available.
- AI-normalized suggestions attached by `row_order`, when available.

The UI may show source labels, but the adoption action is identical:

```text
推荐采用
[系统校对]  rendered equation  [采用这个反应式]
[AI 校对]  rendered equation  [采用这个反应式]
```

If parser and AI produce the same normalized candidate, the UI should de-duplicate and merge the source label to `系统 + AI`.

Alternative considered: use tabs for "系统建议" and "AI 建议". Rejected because tabs still make teachers choose a system before choosing the equation.

### Decision 4: AI action is contextual and singular

The top action should be a single primary AI action:

- When the editor has input: `AI 校对全部`
- When the editor is empty but point context exists: `AI 生成候选`

Rows with warning or invalid status may also expose a local action such as `让 AI 修这行`. That action should be visually near the row status, not in a distant toolbar.

Alternative considered: keep separate buttons for "AI 修正" and "AI 生成反应式". Rejected because both are the same user intent: ask AI for adoptable reaction candidates based on current context.

### Decision 5: Details are secondary

Teachers routinely need to know whether the rendered reaction is correct. They rarely need formula token lists, raw parser warnings, or AI reasoning. Therefore:

- The row headline shows the rendered current understanding and status.
- The candidate area shows rendered candidates and adopt actions.
- Formula tokens, raw replacement text, parser warnings, and AI rationale live under `查看详情` or a compact expandable area.

Alternative considered: always show `识别到：...`, warnings, and rationale. Rejected because it creates visual noise and makes the review feel like debugging rather than teaching content authoring.

### Decision 6: Adoption updates the input, then preview re-validates

Accepting a candidate should:

1. Replace the corresponding multiline input row when `row_order` is known.
2. Append as a new line only when the candidate is explicitly an unmatched generated candidate.
3. Clear or refresh stale candidates for affected rows.
4. Trigger backend preview again.
5. Leave final persistence to the existing save button.

This keeps the backend as the authority and avoids storing stale frontend candidate objects.

Alternative considered: persist accepted candidate objects directly. Rejected because it bypasses the existing save normalization boundary.

### Decision 7: Empty input is a different state

When no reaction text exists, the UI should not show an empty review panel. It should show a compact empty state:

```text
还没有反应式
AI 可以根据当前点位内容生成候选反应式，生成后仍需老师采纳。
[AI 生成候选]
```

Generated candidates from empty input should appear in the same review panel as unmatched candidates, still rendered and teacher-accepted.

Alternative considered: reuse the row review layout with no rows. Rejected because it looks broken and does not explain the available next action.

## Risks / Trade-offs

- [Risk] Backend-normalizing AI candidates adds one more validation step and may filter out useful but imperfect AI output. -> Mitigation: show filtered/unusable output only as a non-adoptable detail if needed; never make invalid AI text adoptable.
- [Risk] De-duplicating parser and AI suggestions can hide source nuance. -> Mitigation: merge source labels and keep rationale in details.
- [Risk] Per-row AI actions can clutter the panel. -> Mitigation: show them only for warning/invalid/needs-confirmation rows, or behind a row action menu on narrow screens.
- [Risk] Replacing input rows after adoption can surprise teachers if the raw text changes too aggressively. -> Mitigation: use explicit button text `采用这个反应式` and re-run preview immediately so the effect is visible.
- [Risk] Rendering candidate equations requires normalized mhchem/display fields from the backend. -> Mitigation: update assist response contracts and tests before changing the UI.

## Migration Plan

1. Keep existing saved `reaction_equations` data unchanged.
2. Extend assist responses to include normalized candidate fields while preserving existing `draft_text` compatibility during the transition.
3. Update the frontend mapper to build a row-centered review model from preview rows plus assist candidates.
4. Remove the separate AI suggestion section after row-attached candidates are working.
5. Rollback is UI-only: fall back to the current natural editor preview and assist response shape; saved point content remains compatible.

## Open Questions

- Should unmatched AI-generated candidates appear below all rows as `候选补充反应式`, or should the first empty generated candidate create a temporary row immediately?
- Should `采用全部` be available only when all candidates are row-aligned and valid, or removed entirely to keep teacher review deliberate?
- Should row-level AI calls send only the target row plus point context, or all rows so AI can preserve reaction sequence consistency?
