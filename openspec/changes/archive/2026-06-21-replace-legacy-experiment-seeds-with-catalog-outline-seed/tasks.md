## 1. Seed Artifacts

- [x] 1.1 Create the structured canonical catalog tree seed under `data/seed/**` from `docs/实验目录_整理版.md`, preserving `##` headings as directories, non-leaf bullets as directories, and leaf bullets as point nodes.
- [x] 1.2 Add catalog seed validation that asserts 569 catalog nodes, 176 directories, 393 points, zero chapter 21 placeholder nodes, no point children, and both corrected `NaClO + MnSO₄` / `NaClO + 品红溶液` sibling points.
- [x] 1.3 Create a separate structured seed for the 30 mapped point-content examples from `docs/30点位例子.txt`, using the explicit target paths listed in `design.md`.
- [x] 1.4 Add validation that all 30 point-content examples resolve to unique catalog point nodes and contain principle, phenomenon explanation, and safety note fields.

## 2. Catalog Import And Reset

- [x] 2.1 Replace the legacy formal-experiment/video-point seed import path with an importer that builds `experiment_catalog_nodes` from the structured catalog seed.
- [x] 2.2 Add an intentional destructive reset for old seed-derived catalog nodes, point content, media/video bindings, point evidence bindings, search documents, question banks, and questions.
- [x] 2.3 Ensure the reset preserves canonical chunks, chunk embeddings, analyzer dictionaries, users, roles, courses, and other non-seed platform data.
- [x] 2.4 Import the 30 mapped point-content examples into the point-content table with text-mode principle, phenomenon explanation, and safety note.
- [x] 2.5 Rebuild or queue ES/search documents for the 30 indexable content-bearing catalog point nodes without requiring legacy point evidence.

## 3. Question Bank And RAG Evidence Guardrails

- [x] 3.1 Remove old point-aware question-bank seed resources from current import paths and make the current experiment question bank empty after catalog reset.
- [x] 3.2 Update question-bank UI/API empty states so teachers do not see old question coverage as valid after reset.
- [x] 3.3 Retire or guard legacy point evidence import/generation scripts that only accept `experiment_id + point_key`, including `scripts/import_manual_reviewed_point_evidence.py` and old default-evidence workflows.
- [x] 3.4 Add catalog-node evidence generation requirements or stubs so any future GPU/BGE rerank job loads leaf catalog nodes and writes catalog node ids or deterministic seed keys.
- [x] 3.5 Ensure AI/question-bank generation fails closed when fresh catalog-node evidence is missing and does not fall back to old evidence bindings.

## 4. Production Validation And Documentation

- [x] 4.1 Update `scripts/validate_production_resources.py` and any manifest logic to protect the new catalog seed, 30-example seed, canonical chunks, embeddings, and analyzer assets.
- [x] 4.2 Remove old protected baseline counts for 300 old point nodes, 77 old banks, 2,310 old questions, and 300 old point evidence bindings.
- [x] 4.3 Update `docs/production-operations.md`, `docs/productionization-final-notes.md`, `data/seed/README.md`, and related seed docs to describe retired legacy resources and the new empty-bank baseline.
- [x] 4.4 Document that canonical chunks and embeddings remain valid corpus data even though old point-to-chunk bindings are retired.

## 5. Verification

- [x] 5.1 Run catalog seed validation and record the count/mapping results in the implementation notes or generated report.
- [x] 5.2 Run backend tests covering catalog import/reset, point-content import, question-bank empty state, and RAG evidence guardrails.
- [x] 5.3 Run frontend checks that cover the affected teacher catalog/question-bank empty states if frontend behavior changes.
- [x] 5.4 Run ES/search smoke verification against the 30 mapped point-content examples.
- [x] 5.5 Run `openspec validate replace-legacy-experiment-seeds-with-catalog-outline-seed --strict`.
