## Context

The current implementation has three independent periodic-learning definitions:

- Student H5 owns a compact phone periodic table and profile-to-area helpers in `web-student`.
- Teacher resource overview owns a separate desktop periodic table and color metadata in `web-teacher`.
- Backend domains own chapter-to-area mappings in `normalization.py`, student learning home code, and learning-resource overview code.

The product intent is not to make teacher and student screens identical. The student screen is a phone-first learning entry, while the teacher overview is a desktop resource dashboard with more operational context and an extra `通识资源` area. The shared part is only the chemistry semantics: area IDs, labels, chapter membership, element membership, and color meaning.

The latest accepted taxonomy is:

1. `hydrogen` / `氢元素`
2. `p` / `p区元素`
3. `s` / `s区元素`
4. `ds` / `ds区元素`
5. `d` / `d区元素`
6. `f` / `f区元素`

`通识资源` remains teacher-only. The previous combined student option `氢和稀有气体` is removed as an area. Hydrogen becomes its own area; noble gases are displayed as p-area elements. CH22 can therefore be visible from both `hydrogen` and `p` learning contexts when it is the matching chapter for H and noble-gas content.

## Goals / Non-Goals

**Goals:**

- Preserve independent student and teacher UI rendering while aligning the taxonomy behind them.
- Move student learning-root recommendation guidance into a lower smart card instead of periodic-table badges or gold cell outlines.
- Keep `/learn` root as a periodic-table entry surface, with selected-area and chapter screens remaining detail routes.
- Open f-block learning to students by adding or exposing the CH21 learning profile and matching chapter entry.
- Fix teacher resource overview f-block placement to match the student-aligned La/Ac-starting row structure.
- Align student and teacher color semantics with a ptable-inspired palette at the area-token level.
- Add tests that lock the taxonomy and prevent the three current mappings from drifting again.

**Non-Goals:**

- Do not share the student and teacher periodic-table React components.
- Do not force student and teacher periodic tables to have the same dimensions, card layout, grid density, or interaction model.
- Do not add the teacher-only `通识资源` area to the student H5 learning entry.
- Do not introduce a new external periodic-table rendering library.
- Do not redesign chapter detail, catalog point detail, or atom-model detail pages beyond area/color inputs caused by this taxonomy change.

## Decisions

### Decision: Share semantic contracts, not UI components

Student H5 and teacher resource overview will each keep their own rendering components. The shared contract is limited to stable IDs, labels, color token values, chapter membership, and element membership.

Rationale: the two products serve different viewports and workflows. Sharing React components or grid geometry would make the phone UI and desktop dashboard constrain each other and would violate the existing teacher/student product-boundary discipline.

Alternative considered: extract a single neutral periodic-table model with element coordinates and have both UIs render from it. Rejected because it over-shares UI shape: teacher desktop can need denser labels and dashboard affordances, while student H5 needs tiny touch-first cells and phone spacing.

### Decision: Backend remains authoritative for chapter-area membership

Backend `CHAPTER_AREA_MAP` / area definitions will be updated so student learning home, resource overview grouping, analytics/question-area helpers, and teacher resource overview payloads agree on chapter semantics.

Rationale: chapter membership affects more than UI color. It affects recommendations, resource grouping, question coverage, learning analytics, and teacher dashboards.

### Decision: Element-area membership stays frontend-local per renderer but is tested

Student and teacher frontends can each keep product-specific periodic element placement because their shapes differ. Tests will assert the accepted semantic mapping:

- H maps to `hydrogen`.
- Noble gases map to `p`.
- Li/Be/Na/Mg/K/Ca/Rb/Sr/Cs/Ba/Fr/Ra map to `s`.
- Group 11/12 ds elements map to `ds`.
- d-block transition elements map to `d`.
- La-Lu and Ac-Lr map to `f`.

Rationale: element cell placement is a rendering concern, but element ownership is a semantic concern. Tests are the boundary between those concerns.

### Decision: Student recommendations move below the table

The student learning root will fetch the same learning data it already needs, but the periodic-table component will no longer receive or render recommendation badge props. A lower smart card will render recommended/continue-learning guidance and CTA actions.

Rationale: after the selected-area page split, recommendation on the table reads like selected state and crowds the compact grid. Moving it below uses the current empty lower half and makes the top section a pure selection tool.

### Decision: Teacher overview keeps general resources outside the element table

The teacher resource overview can still show `通识资源`, but it will be outside the periodic element-cell ownership. It can appear as a separate action/card/area in the desktop dashboard, not as part of the six student learning areas.

Rationale: `通识资源` is an operational resource bucket, not an element-region. Mixing it into the element table would make teacher and student semantics diverge again.

## Risks / Trade-offs

- [Risk] CH22 belongs to both `hydrogen` and `p` contexts after noble gases move into p. → Mitigation: represent selected-area chapter filtering as profile membership by element ownership, not as a single area string when necessary; tests must assert CH22 appears for hydrogen and p where expected.
- [Risk] Updating backend area IDs can affect assessment/question grouping. → Mitigation: keep area IDs stable for existing `p/s/ds/d/f` and add `hydrogen`; avoid deleting CH22 itself; update tests around pretest/recommendation gracefully.
- [Risk] Teacher and student color tokens may drift again if stored separately. → Mitigation: add contract tests that compare exported token values or stable source snippets for the six shared area IDs.
- [Risk] Adding CH21 student f profile without full experiment/media coverage may create empty entries. → Mitigation: allow a graceful chapter entry with empty/limited catalog content only if the same empty-state behavior already exists; validate profile completeness and avoid crashes.
- [Risk] Removing inline recommendation cues may reduce discoverability. → Mitigation: the lower smart card must remain visible in the learning root first scroll and include a clear CTA into the recommended chapter.

## Migration Plan

1. Update OpenSpec requirements and tasks for the accepted taxonomy.
2. Update backend area definitions and resource grouping.
3. Add or enable student CH21 f-block profile seed content.
4. Update student learning root, periodic table props/styles, area filtering, and mobile QA expectations.
5. Update teacher resource overview color metadata and f-block placement.
6. Add/adjust tests for taxonomy, color tokens, CH22 hydrogen/p behavior, student f availability, and teacher f-block layout.

Rollback is straightforward at the application level: revert the change commit. No destructive data migration is expected because chapter IDs remain stable and this change is primarily mapping, seed, and presentation logic.

## Open Questions

- Whether future learning reports should distinguish `hydrogen` as a standalone assessment weakness area or continue treating CH22 as a special chapter-level recommendation. The implementation should avoid hard-coding assumptions that make either future choice impossible.
