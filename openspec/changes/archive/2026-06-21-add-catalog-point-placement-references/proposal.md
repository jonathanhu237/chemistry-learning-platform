## Why

The canonical outline now contains the same real experiment under multiple chapter paths, but the current catalog model treats every leaf point node as an independent learning identity. This duplicates videos, point content, evidence, question bindings, analytics, and search state for what teachers and students expect to be one shared experiment.

We need a directory-tree experience where an experiment can appear in multiple chapters and be searchable from each chapter context while still behaving like one synchronized experiment entity when edited.

## What Changes

- Introduce canonical experiment point entities that own point learning content, video bindings, AI evidence bindings, question-bank identity, assessment identity, analytics, and feedback context.
- Reframe catalog leaf points as placement/reference entries: each visible point row appears under exactly one directory parent but points to exactly one canonical experiment point entity.
- Keep the student and teacher directory trees as ordinary trees; do not reintroduce true multi-parent nodes or legacy `shortcut` node kinds.
- Make reuse user-friendly in the teacher UI: teachers add or reuse the same experiment in another directory without needing to understand "canonical" versus "reference" internals.
- Add explicit teacher-side safety messaging when editing a reused experiment: changes to shared experiment content, videos, and evidence-impacting fields affect every catalog placement.
- Define deletion semantics similar to reference counting: removing one visible placement does not delete the canonical experiment; final deletion or archival of the canonical experiment is allowed only when no active placements remain or through an explicit cascade/archive workflow.
- Index student video-library search one document per published placement so the same experiment can be found under different chapter paths, while each result carries both source placement identity and canonical experiment identity.
- Resolve student point detail from the selected placement path to the shared canonical experiment content, preserving source breadcrumbs and return behavior.
- Update seed and migration behavior so duplicate/same-title catalog leaves can be represented as multiple placements targeting one canonical experiment where product-reviewed mapping rules identify them as the same experiment.
- After the canonical point/placement architecture is in place, import the complete corrected experiment directory from `docs/实验目录_整理版.md` into the database as the active baseline: 176 visible directories, 393 visible point placements, 569 visible catalog tree nodes, chapter 21 empty, and reviewed canonical grouping for duplicate experiments.
- **BREAKING** Stored rows that currently treat catalog point node id as the sole canonical point identity must migrate to the new canonical-point plus placement identity model.

## Capabilities

### New Capabilities
- `catalog-point-placement-references`: Defines canonical experiment point entities, catalog placements, shared edit semantics, reference-count deletion behavior, and placement-aware search/detail resolution.

### Modified Capabilities
- `experiment-catalog-tree`: Point identity changes from "catalog point node id is the point identity" to "catalog placement id locates the tree entry; canonical experiment point id owns shared learning identity."
- `teacher-experiment-catalog-editor`: The catalog editor must support reuse/add-to-directory flows, shared-content edit warnings, placement removal, and canonical experiment archival rules.
- `student-h5-route-stack-navigation`: Point routes must preserve source placement context while resolving shared canonical point content.
- `experiment-video-point-question-binding`: Question bindings must bind to canonical experiment points while preserving placement/chapter context for browsing and reporting.
- `experiment-question-bank-management`: Teacher question-bank browsing and AI entry points must display canonical point identity with placement-aware chapter/path context.
- `hybrid-bge-rag-retrieval`: Catalog-node evidence refresh must target canonical experiment points while search/detail contexts may originate from placements.

## Impact

- Database schema and migrations for canonical experiment point entities, placement references, foreign keys, uniqueness rules, deletion/archive guards, and migration mapping from existing point nodes.
- Backend catalog tree services, student read models, search document builders, evidence state/binding jobs, media binding services, question-bank services, assessment context, analytics, and feedback references.
- Admin/teacher catalog editor APIs and UI for reuse, synchronized editing, placement removal, validation, search preview, and reference-count visibility.
- Student H5 routes and point detail payloads: responses must include both source placement id/path and canonical point id.
- Elasticsearch indexing: one searchable document per published placement, with canonical point id included in the document source and route target.
- Seed generation and final import from `docs/实验目录_整理版.md`: duplicate experiment leaves require product-reviewed canonical grouping rules rather than automatic title-only dedupe, and the target database must end with the corrected full outline imported under the new architecture.
- Validation and smoke tests for duplicate placement groups, final-placement deletion rules, ES/search behavior, student detail resolution, and migration safety.
