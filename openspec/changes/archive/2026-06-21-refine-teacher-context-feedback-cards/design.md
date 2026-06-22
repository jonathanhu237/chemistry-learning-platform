## Context

The teacher catalog editor already exposes video binding, static fallback evidence diagnostics, and RAG probe diagnostics in the selected point workspace. The current presentation uses full-width Ant Design `Alert` components for friendly hints, which visually reads like system warnings and takes too much vertical space for routine teacher workflows.

## Goals / Non-Goals

**Goals:**

- Replace broad friendly hints with compact, purpose-built cards that match the editor surface.
- Make the video upload route visible as a shortcut without implying upload happens inside the point editor.
- Present static fallback evidence as a state lifecycle so teachers can see current status and possible transitions.
- Rename dynamic RAG probe language to real RAG search across visible teacher UI.

**Non-Goals:**

- No backend state model changes.
- No changes to RAG retrieval, ES indexing, media upload, or publication behavior.
- No student-facing UI changes.

## Decisions

- Use feature-local React markup and CSS rather than a new shared notification component.
  - Rationale: the patterns are specific to the catalog editor and can be stabilized before extracting shared UI.
  - Alternative considered: theme Ant Design `Alert`; rejected because the interaction should no longer read as an alert.
- Drive the static evidence lifecycle from existing status strings.
  - Rationale: current backend already exposes `pending`, `running`, `available_static_fallback`, `missing_fallback_evidence`, `stale_fallback_evidence`, `failed`, and related states.
  - Alternative considered: add a backend lifecycle field; rejected because it would add API churn for a presentation-only refinement.
- Keep diagnostic details visible only in the teacher AI context panel.
  - Rationale: chunk IDs, scores, and RAG stages are teacher diagnostics and must remain outside student surfaces.

## Risks / Trade-offs

- Status names may expand later, causing an unknown state to render generically. Mitigation: default unknown statuses to a neutral lifecycle state and keep raw detail visible in the status tag.
- Hand-built state graph CSS can become cramped on small screens. Mitigation: use wrapping flex layout and compact nodes rather than a fixed-width diagram.
- Renaming visible UI from probe to search may hide implementation language from developers. Mitigation: keep internal API names unchanged and only rename teacher-facing copy.
