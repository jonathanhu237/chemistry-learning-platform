## Why

The experiment catalog tree is now the core learning object model, but the surrounding AI, ES, question-bank, and teacher-authoring flows still carry assumptions from the old experiment/point model. We need one context-preserving roadmap that turns catalog point nodes into the shared identity and context boundary for teacher authoring, student search, RAG evidence, and question generation.

This is needed now because the new catalog seed invalidates the old point evidence bindings and question bank, while the teacher UI still exposes only plain text equation entry and does not show the AI-consumable context that actually drives learning-assistant and future question-generation behavior.

## What Changes

- **BREAKING** Replace single-string equation principle authoring with multi-equation point authoring: teachers may enter one or more chemical reaction equations, while backend parsing and normalization become the only trusted source for AI/ES/RAG consumption.
- **BREAKING** Treat legacy `(experiment_id, point_key)` point evidence and old question-bank seed data as retired. New evidence and question generation must target catalog node ids or stable catalog seed keys.
- Preserve the full chapter catalog tree from the authoritative docs seed; directories remain navigation/grouping nodes and leaf nodes are experiment points.
- Keep teacher console features open to every teacher account; reserve `web-admin` for operational teacher-account management only.
- Add a teacher-facing AI context workbench on catalog point pages that shows point context, static evidence bindings, dynamic RAG probes, query strategy, and BGE/rerank diagnostics without leaking raw diagnostics to student pages.
- Introduce controlled, observable jobs for ES indexing and catalog-node RAG evidence refresh so frontend saves are not blocked by slow BGE rerank work.
- Gate question-bank regeneration on fresh catalog-node evidence readiness; until evidence exists, the old question bank is considered empty/invalid.
- Preserve and document the catalog editor UX decisions already reached: title-card workbench, chapter switching from the title area, modern tree drag/drop, refresh/expand behavior, and concise teaching-note semantics.

## Capabilities

### New Capabilities

- `web-console-role-boundaries`: Defines the split between `web-admin`, `web-teacher`, and `web-student`, including all-teacher feature access and operational teacher-account management.
- `catalog-point-chemical-equation-authoring`: Defines teacher entry of one or more chemical reaction equations and backend-owned parsing, validation, normalization, and AI/ES/RAG derivation.
- `catalog-point-ai-context-workbench`: Defines the teacher-side view and APIs for static point evidence, dynamic RAG probes, generated query strategy, and AI-consumable point context.
- `catalog-point-index-evidence-jobs`: Defines controlled job interfaces for ES document sync and catalog-node RAG evidence refresh/delete/retry flows.
- `catalog-node-question-generation-gate`: Defines reset/gating behavior for question banks after catalog migration and requires fresh catalog-node evidence before AI question generation.

### Modified Capabilities

- `teacher-experiment-catalog-editor`: Codifies the catalog/tree/workbench UI decisions and cleanup from the recent design pass as ongoing editor requirements.
- `experiment-catalog-tree`: Extends the catalog tree contract to make the authoritative docs seed, full directory preservation, leaf-point semantics, 30 sample-point mapping, and legacy seed cleanup explicit.

## Impact

- Frontend: `apps/web-teacher` catalog tree editor, point content panel, future AI context panel, account/menu visibility; `apps/web-admin` operational teacher-account screens; `apps/web-student` remains isolated from teacher diagnostics.
- Backend APIs: catalog point content schema, validation/parsing endpoints, catalog tree import/seed services, ES index state endpoints, RAG evidence job endpoints, question-bank generation gates.
- Database: catalog point content fields, normalized reaction storage, optional job/outbox tables, catalog-node evidence bindings, seed cleanup validation, question-bank reset markers.
- Workers/services: existing ES sync path, optional BGE service, future catalog/RAG worker; first implementation should prefer Postgres-backed jobs before introducing Redis/Rabbit/Celery.
- Data and seeds: authoritative docs catalog seed, 30 sample point seed for ES tests, protected canonical `source_chunks` and embeddings, retired legacy evidence/question-bank seed data.
- OpenSpec dependencies: this roadmap builds on the completed catalog tree, teacher/student/admin split, hybrid BGE RAG, point-context assistant, and search-refactor changes.
