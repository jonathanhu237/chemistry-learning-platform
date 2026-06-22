## Why

The natural equation editor now lets teachers type or paste reaction text, but review is still split into "system understanding" and a separate "AI suggestions" block. Teachers do not care whether a candidate came from the parser or AI; they care whether the rendered chemical reaction looks correct enough to adopt.

This change unifies parser and AI feedback into a row-centered review flow where each reaction line shows rendered candidates in context, and adopting a candidate feels like choosing a chemical equation rather than copying ordinary text.

## What Changes

- Replace the separate AI suggestion list with row-attached correction candidates inside the reaction review panel.
- Render every adoptable candidate as a chemical reaction using the same equation renderer as saved/previewed equations; raw candidate text is not the primary teacher-facing surface.
- Merge deterministic parser suggestions and AI suggestions into a single candidate area per affected row, with source labels such as `系统校对`, `AI 校对`, or `系统 + AI`.
- Keep one global AI action for the equation editor: `AI 校对全部` when input exists, and `AI 生成候选` when the editor is empty.
- Add optional per-row AI assistance for rows that are invalid, warning, or need confirmation.
- Move formula tokens, parser warnings, AI rationale, and raw replacement text into compact secondary details so routine teacher review stays visual and fast.
- Ensure accepting a rendered candidate updates the multiline input row and immediately re-runs backend preview; it must not save or publish content by itself.
- Normalize AI candidates through the backend before they are displayed so the frontend does not present unverified plain-text suggestions as trusted formulas.

## Capabilities

### New Capabilities

- `teacher-equation-review-suggestions`: Row-centered review, rendered equation candidates, unified parser/AI suggestions, and explicit teacher adoption behavior for catalog point reaction equations.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: The point content form's chemical equation mode must review and adopt rendered reaction candidates inline instead of showing parser and AI suggestions as separate text-heavy sections.

## Impact

- `apps/web-teacher/src/features/catalog-tree/CatalogNodeContentPanel.tsx`
- `apps/web-teacher/src/features/catalog-tree/catalogTree.css`
- `apps/web-teacher/src/features/catalog-tree/catalogTreeContracts.test.ts`
- `apps/web-teacher/src/features/catalog-tree/catalogTreeMappers.test.ts`
- `apps/web-teacher/src/api/catalogTree.ts`
- `server/app/domains/catalog_tree/equations.py`
- `server/app/catalog_tree_schemas.py`
- `server/app/api/admin/admin_catalog_tree.py`
- `server/tests/test_catalog_point_equations.py`
- No new message queue, editor framework, or chemistry drawing dependency is required.
