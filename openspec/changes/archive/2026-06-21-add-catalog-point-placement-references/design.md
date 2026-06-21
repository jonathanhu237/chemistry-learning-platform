## Context

The current catalog implementation models the student/teacher tree as `chapter -> directories -> points`, with `experiment_catalog_nodes.id` serving both as the visible tree node id and the learning point identity. That was correct while each experiment appeared in one place, but the new canonical outline contains the same real experiment under more than one chapter/path.

Local data inspection after the outline seed replacement found 32 duplicate point-title groups, covering 68 point rows and 36 surplus independent identities. Examples include:

- `Na2SiO3 + CO2` appearing under both chapter 16 and chapter 17 silicon/boron paths.
- `Al2(SO4)3 + NH3·H2O + NaOH` appearing in both chapter 17 and chapter 18 paths, and under multiple subdirectories within those chapters.
- `BeSO4 + NH3·H2O + NaOH` with the same multi-path pattern.

The product intent is simple: the same experiment should be discoverable from different chapter directories and search contexts. Teachers and students should not need to decide which copy is "real." If a teacher edits that experiment from any location, every visible occurrence should reflect the same content, videos, evidence state, and question-bank identity.

The previous `separate-catalog-directory-point-nodes` change intentionally removed legacy `shortcut` and true multi-parent behavior. This change should not resurrect that model. The better fit is a placement/membership model similar to YouTube playlist items, Google Drive's single-parent tree plus shortcuts, Notion linked views, and Apple alias deletion semantics: visible entries can appear in many locations, but the shared object is single-source.

## Goals / Non-Goals

**Goals:**
- Separate visible catalog placement identity from canonical experiment point identity.
- Keep the catalog tree a strict tree: every visible node has at most one parent and no true multi-parent node ids.
- Let one canonical experiment point appear under multiple chapter/directory paths through point placements.
- Make the teacher UI feel like "reuse/add this experiment to another directory" or "synchronized copy," not like an internal shortcut/reference model.
- Ensure editing shared point content, videos, AI evidence state, question bindings, and assessment identity from any placement affects the canonical experiment point.
- Ensure deleting one placement removes only that location, while final-placement deletion or canonical archival follows explicit reference-count rules.
- Index one student search document per published placement so the same canonical experiment is searchable from each relevant chapter/path.
- Preserve source placement breadcrumbs and route return behavior when opening point detail.
- Migrate current point-node references and duplicate outline leaves deterministically, with manual review for ambiguous duplicate groups.
- Re-import the full corrected experiment outline after the canonical point/placement architecture is implemented so the active database baseline contains the complete visible tree: 176 directories, 393 point placements, 569 visible catalog nodes, and no placeholder content for chapter 21.

**Non-Goals:**
- Do not reintroduce `node_kind = shortcut`, `hybrid`, or hidden shortcut-compatible API contracts.
- Do not implement true multi-parent catalog nodes.
- Do not merge same-title points automatically without a reviewed mapping rule; identical titles can still be different experiments in future data.
- Do not regenerate question banks or AI evidence in this change; migrate identity ownership and mark stale where needed.
- Do not make directories searchable standalone video-library results.
- Do not add a free-form visual graph of point reuse; the product surface remains the existing tree/editor experience.

## Decisions

### Decision 1: Use canonical points plus catalog placements

Introduce a canonical experiment point layer and make catalog point rows placements that target that layer.

Proposed conceptual model:

```text
experiment_catalog_nodes
  directory node: parent/path/order/card metadata
  point placement node: parent/path/order/card metadata + target_point_id

experiment_catalog_points
  canonical experiment point: shared title/summary/lifecycle identity

experiment_catalog_point_content
experiment_catalog_point_media_bindings
experiment_catalog_point_evidence_state
experiment_catalog_point_evidence_bindings
question/assessment/analytics/feedback point refs
  reference canonical_point_id
```

The catalog node id remains the durable tree placement id. The canonical point id becomes the durable learning identity.

Alternative considered: add `canonical_node_id` to `experiment_catalog_nodes` and let one point node remain the "original." Rejected for the main design because it leaks a primary/reference distinction into deletion, movement, permissions, and teacher mental model. It is acceptable as a temporary migration compatibility layer only if the implementation hides it behind canonical-point APIs and finishes by separating canonical identity from placement identity.

### Decision 2: Keep `directory` and `point` node kinds only

Point placements remain `node_kind = 'point'` because they render as point/video learning entries in the tree. The distinction between a placement and the canonical point is expressed by `target_point_id`, not by adding a new visible node kind.

Student-facing clients should not show a "reference" badge. Teacher-facing clients may show reuse context such as "Used in 3 directories" and a list of locations.

Alternative considered: add `node_kind = 'reference'`. Rejected because it would revive the same branching surface that the previous change removed, and it would ask teachers to understand an implementation term.

### Decision 3: Teacher copy means synchronized reuse by default

Teacher UI actions should use product language:

- "Create new experiment" creates a canonical point and its first placement.
- "Add to another directory" or "Reuse existing experiment" creates another placement targeting an existing canonical point.
- "Copy as independent experiment" is an explicit future-capable action only if product needs a fork; it must create a new canonical point and must not be the default.

When a reused experiment is selected, the editor should show a compact warning before shared fields: changes to experiment content, videos, and evidence-impacting fields affect every location. The editor should also show the placement list so teachers understand why the same experiment appears elsewhere.

Alternative considered: label every non-primary placement as a reference. Rejected because the user experience should not require deciding which occurrence is primary.

### Decision 4: Split shared fields from placement fields

Shared canonical fields:
- experiment title and canonical summary;
- point content title, principle, reaction equations, phenomenon explanation, safety note, teacher-only content note;
- video/media bindings;
- related experiment links unless explicitly changed later;
- AI evidence state/bindings;
- question-bank bindings, assessment point identity, analytics identity, feedback identity.

Placement-local fields:
- chapter id, parent directory, display order, publication state, breadcrumbs/path;
- student card display overrides that are explicitly placement-level;
- placement teacher note or placement usage note if the UI needs directory-specific authoring context.

The initial implementation should minimize local overrides. If a local title override is allowed, the API must make it clear whether the displayed title is canonical or overridden. Otherwise teachers will think content failed to synchronize.

### Decision 5: Deletion follows reference-count semantics, with archival safety

Removing a placement archives/removes only that catalog location. It does not delete shared videos, content, evidence bindings, questions, assessments, analytics, or feedback tied to the canonical point.

When the last active placement is removed, the system may archive the canonical experiment point after explicit confirmation, or it may block the action and ask the teacher to archive the experiment. Physical deletion should remain a retention/cleanup concern, not the normal UI action.

Canonical archival must disable or remove student search documents for all placements and prevent new student detail access. Historical analytics and question records should remain auditable.

Alternative considered: automatically hard-delete the canonical point after the last placement disappears. Rejected because point content may have question/evidence/media/analytics references and accidental final removal would be destructive.

### Decision 6: Student detail resolves placement to canonical content

Point detail routes should be placement-aware:

```text
/point/{placement_node_id}
  -> load placement node and breadcrumbs
  -> resolve target canonical_point_id
  -> load shared content/videos/related points
  -> return placement context plus canonical identity
```

The response should include both placement and canonical identifiers. Existing fields such as `canonical_node_id` and `source_node_id` can be bridged during migration, but the contract should move toward explicit names such as `placement_node_id` and `canonical_point_id`.

Direct canonical-only routes may be useful for admin tools, but student routes should prefer placement routes so breadcrumbs and back navigation stay meaningful.

### Decision 7: Search indexes one document per placement

The video-library search document id should be the placement node id. Each document should include:

- `placement_node_id`;
- `canonical_point_id`;
- chapter id/title;
- placement catalog path and ancestor directory context;
- canonical point content;
- canonical video metadata;
- route target using the placement node id;
- canonical point grouping metadata for future result grouping.

This intentionally allows the same canonical experiment to appear multiple times in global search if the placement paths are materially different. A future UI may group results by canonical point, but the index must preserve placement-level context.

Content or video changes on a canonical point must enqueue upserts for every active published placement. Placement path/publication changes should enqueue only the affected placement document.

### Decision 8: Evidence, questions, and media bind to canonical points

Media bindings, AI evidence state/bindings, question bank point references, assessment context, analytics learning identity, and feedback point identity should move from catalog node id to canonical point id.

Placement context can still be stored as source metadata where a user action occurred from a specific route. For example, a student assessment attempt can record canonical point id for learning identity and source placement id/path for chapter context.

Related points should target canonical point ids. When rendering a related point link, the student API should resolve a suitable published placement for the current chapter if one exists, otherwise fall back to a stable default published placement.

### Decision 9: Seed/migration uses reviewed canonical grouping

The seed generator must continue preserving the full chapter directory tree. For leaf bullets, it must produce placements. It must produce or reference canonical point entities through a reviewed grouping map.

Grouping rules:

- Singleton leaves create one canonical point with one placement.
- Reviewed duplicate groups create one canonical point with multiple placements.
- Ambiguous same-title leaves remain separate canonical points until product/data review maps them.
- The 30 example content mappings should bind to canonical points through their selected placement mappings.
- The known corrected sibling points `NaClO + MnSO4` and `NaClO + 品红溶液` must remain distinct canonical points and distinct sibling placements.

Existing migrations should produce an audit table/report that shows old placement node ids, new placement node ids if changed, canonical point ids, duplicate group decisions, and any conflicts in content/media/evidence/question references.

### Decision 10: Final import is part of the change, not a follow-up

After the new canonical point/placement schema and migration rules are in place, this change must run the corrected outline import against the target development database and leave the active catalog in the new shape. The implementation is not complete if it only creates architecture support while leaving the old independent point-node seed in place.

The final visible catalog baseline must satisfy:

- 569 active visible catalog nodes derived from `docs/实验目录_整理版.md`;
- 176 active visible directory nodes;
- 393 active visible point placements;
- chapter 21 has no directory, placement, or placeholder node for "暂无对应实验内容";
- every visible point placement targets exactly one canonical experiment point;
- every canonical experiment point has at least one active placement unless explicitly archived;
- the canonical point count is derived from the reviewed grouping map and reported in validation;
- the 30 sample content examples bind through their reviewed placement mappings to canonical experiment points;
- no legacy independent point identity remains as the authoritative seed baseline.

The importer should be idempotent for a clean development reset and deterministic for repeated runs against the same baseline. If the reviewed grouping map changes, the import validation must show which canonical grouping decisions changed.

## Risks / Trade-offs

- [Risk] The migration touches many point-reference tables. -> Mitigation: add a migration inventory and validation query for every table that currently stores `node_id` or `point_node_id`.
- [Risk] Teachers may not realize editing one reused experiment changes all locations. -> Mitigation: show reuse count, locations, and a shared-content warning in the editor before shared fields.
- [Risk] Title-only dedupe can merge experiments that should remain separate. -> Mitigation: require reviewed grouping rules and keep ambiguous groups separate.
- [Risk] Search may show repeated results for the same canonical experiment. -> Mitigation: preserve placement documents first, then optionally add UI grouping by canonical point after search behavior is validated.
- [Risk] Final-placement deletion can accidentally hide useful canonical content. -> Mitigation: require explicit confirmation or block final removal until the teacher chooses archive/keep.
- [Risk] Backward compatibility fields such as `canonical_node_id` can confuse new code. -> Mitigation: introduce explicit `canonical_point_id` and `placement_node_id` in new contracts while bridging legacy fields during migration.
- [Risk] Related links may need a placement target to render correctly. -> Mitigation: store canonical targets and resolve display placement at read time using same-chapter preference and fallback rules.

## Migration Plan

1. Inventory all current point identity references in database schema, backend services, frontend types, tests, seed scripts, ES documents, and OpenSpec/docs.
2. Add canonical experiment point storage and placement targeting fields while keeping existing reads compatible.
3. Create canonical points for existing point nodes and migrate singleton references to canonical ids.
4. Apply reviewed duplicate grouping for current outline duplicates; preserve full tree placements and map duplicates to shared canonical points.
5. Migrate shared point content, media bindings, evidence state/bindings, question references, assessment context, analytics, and feedback to canonical point ids.
6. Update catalog read/write APIs so point placement routes resolve canonical content.
7. Update teacher UI for reuse/add-to-directory, shared-content warnings, placement lists, placement removal, and final-placement archival rules.
8. Update student H5 route/detail/search flows to preserve placement context and canonical identity.
9. Run the corrected outline importer after the schema/data migration so the active database contains the complete new visible tree and canonical grouping baseline.
10. Rebuild video-library ES documents as one document per published placement.
11. Run data validation, OpenSpec strict validation, backend/frontend tests, seed validation, import validation, and ES smoke checks.

Rollback for application code is normal git rollback. Database rollback is data-sensitive; migrations should preserve mapping/audit tables and avoid hard deletes during the initial deployment. Canonical archival should be reversible until a later cleanup process removes orphaned physical resources.

## Open Questions

- What exact teacher-facing label should we use: "复用到此目录", "添加到其他目录", or "同步副本"?
- Should the initial release allow local placement title overrides, or should all placement titles mirror the canonical experiment title?
- When a teacher removes the last placement, should the default action archive the canonical experiment after confirmation or block and require a separate archive action?
- Should global search show multiple placement results by default, or group same-canonical results after the first implementation proves the index shape?
- Which duplicate groups beyond exact same-title matches are chemically the same experiment and need reviewed canonical grouping?
