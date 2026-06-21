## Why

Teacher-facing catalog editor hints currently rely on wide system-style alerts that look visually heavy and inconsistent with the authoring workflow. The video binding and AI context panels need calmer, purpose-built UI so teachers can recognize shortcuts, evidence state, and real RAG search results without reading explanatory alert blocks.

## What Changes

- Replace the video binding upload notice with a compact video resource shortcut card positioned in the panel header area.
- Replace static fallback evidence explanation alerts with a state-transition card that highlights the current evidence lifecycle state.
- Rename dynamic RAG probe UI to real RAG search and remove redundant explanatory copy.
- Keep diagnostics teacher-only and preserve existing backend contracts; this is a frontend presentation refinement only.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: refine teacher editor feedback presentation for video shortcuts, static evidence lifecycle state, and real RAG search diagnostics.

## Impact

- Affected code: `apps/web-teacher/src/features/catalog-tree/*`.
- Affected users: teacher console catalog editors.
- No API, database, seed, or infrastructure changes.
