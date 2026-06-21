## Why

The current equation authoring flow still asks teachers to adapt to system-shaped controls: per-row cards, explicit check buttons, and a symbol popover. Real teachers are more likely to type or paste natural equations such as `CL2+H2=HCL`, `Cl2 + 2KBr -> 2KCl + Br2`, or Chinese descriptions, so the system must understand forgiving text first and use AI only as an explicit assistant.

## What Changes

- Replace the default multi-card equation input with a natural multiline reaction editor where each non-empty line is treated as one reaction candidate.
- Add debounced near-real-time backend preview so teachers see normalized chemistry notation while typing without manually clicking a primary check button.
- Make backend normalization tolerant of common human input patterns: missing spaces, `=` as reaction arrow, lowercase/uppercase mistakes, common Chinese substance names, and incomplete coefficients.
- Add backend-generated correction/balancing suggestions that teachers can explicitly adopt, without silently rewriting raw teacher input.
- Add an explicit AI-assisted action for generating, correcting, or completing equations from the current point context; AI output remains a draft candidate that must be accepted by the teacher and normalized by the backend before saving.
- Remove common-symbol popover as a primary interaction. Any shortcuts must be secondary, inline, and keyboard-friendly.
- Preserve the backend-authoritative structured records used by AI/ES/RAG; the frontend remains a natural input and preview surface.

## Capabilities

### New Capabilities

- `catalog-point-natural-equation-authoring`: Natural multiline equation input, tolerant backend normalization, debounced preview, correction suggestions, and explicit AI-assisted equation drafting for catalog point content.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: The point content editor must default to a natural, multiline, real-time equation authoring workflow instead of per-row equation cards and symbol-picker-first input.

## Impact

- `apps/web-teacher/src/features/catalog-tree/CatalogNodeContentPanel.tsx`
- `apps/web-teacher/src/features/catalog-tree/catalogTree.css`
- `apps/web-teacher/src/features/catalog-tree/catalogTreeContracts.test.ts`
- `apps/web-teacher/src/api/catalogTree.ts`
- `server/app/domains/catalog_tree/equations.py`
- `server/app/api/admin/admin_catalog_tree.py`
- `server/app/catalog_tree_schemas.py`
- `server/tests/test_catalog_point_equations.py`
- Possible future AI client integration for explicit equation suggestions; no new heavy chemistry drawing dependency is required.
