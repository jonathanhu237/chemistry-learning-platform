## Context

The current OpenSpec inventory has 70 active main specs. Student-facing specs account for 19 of those specs and 183 requirements. Several completed student H5 iterations created narrow capability specs such as local AI history, home video feed, family catalog shell, and login lifecycle. Those specs were useful during implementation, but after archive they now duplicate or fragment broader product ownership areas.

There is also one obsolete empty capability directory, `student-h5-assistant-point-starter`, left behind after the AI root changed to direct composer-first chat.

## Goals / Non-Goals

**Goals:**

- Reduce student H5 spec fragmentation while preserving all durable requirements.
- Make touched specs readable from their `Purpose` section without consulting archived changes.
- Keep current product facts as the source of truth: direct AI composer, route-based learning catalog, home video discovery, unified authentication lifecycle, and preview-scoped touch emulation.
- Leave an audit trail through this housekeeping change.

**Non-Goals:**

- Do not change application code or runtime behavior.
- Do not rewrite archived historical changes.
- Do not modify the active `refine-student-back-arrow-geometry` change.
- Do not attempt to redesign teacher, backend, catalog, or production specs beyond the small governance rule.

## Decisions

### Decision 1: Consolidate obvious small specs into owning capabilities

`student-h5-login` is folded into `student-h5-authentication` because both describe the same account lifecycle. `student-ai-chat-history` and `student-h5-assistant-mobile-starter` become one `student-h5-ai-assistant` capability because local history, direct root chat, contextual chat, and optional starter behavior are one assistant surface. `student-h5-home-video-feed` and `student-h5-video-library-search` become one `student-h5-video-discovery` capability because both govern how students discover experiment video/point learning content.

Alternative considered: keep all implementation-era specs and only add better Purpose text. Rejected because it leaves future work with the same multi-spec lookup burden.

### Decision 2: Extract catalog browsing into a durable learning-catalog capability

The family catalog shell is no longer a temporary UI shell; it is the durable catalog browser model for chapter/family learning. Catalog-specific requirements from the family shell, learning experience, and learning flow move into `student-h5-learning-catalog`, while general route, point detail, and app-shell rules stay in their existing capabilities.

Alternative considered: move the family shell into the already-large `student-h5-learning-experience`. Rejected because that spec is already a broad learning-content container and would become harder to scan.

### Decision 3: Remove obsolete point-starter specs and mobile-design requirements

The default AI root no longer exposes a mandatory point-selection starter. Contextual point chat enters from source pages or future optional controls. The empty `student-h5-assistant-point-starter` capability and stale point-starter design-system requirements are removed.

Alternative considered: keep them as future placeholders. Rejected because placeholders with normative `SHALL` language can conflict with the current direct chat shell.

### Decision 4: Do not normalize every legacy `TBD` purpose in this pass

This pass updates all specs it touches and the governance spec. Large unrelated teacher/backend specs keep their existing purpose text so the cleanup stays scoped and reviewable.

## Risks / Trade-offs

- [Risk] Moving requirements across files could accidentally drop product rules. -> Mitigation: use mechanical block migration, run `openspec validate --specs --strict`, and compare requirement counts before and after.
- [Risk] Renamed or merged specs may surprise someone searching by old capability name. -> Mitigation: preserve requirement titles and archived historical records; choose new names that match product ownership.
- [Risk] A concurrent change is touching OpenSpec. -> Mitigation: exclude `openspec/changes/refine-student-back-arrow-geometry/**` entirely.

## Migration Plan

1. Create merged target specs for authentication, AI assistant, video discovery, and learning catalog.
2. Remove obsolete or absorbed source specs.
3. Remove stale AI point-starter mobile-design requirements.
4. Update Purpose text on touched specs.
5. Validate all main specs in strict mode.
6. Archive this housekeeping change after tasks are complete.
