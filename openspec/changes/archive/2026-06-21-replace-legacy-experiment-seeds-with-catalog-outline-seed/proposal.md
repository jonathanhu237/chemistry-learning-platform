## Why

The experiment catalog seed currently reflects the old formal-experiment/video-point inventory, while the product has moved to a chapter-scoped experiment catalog tree whose canonical source is `docs/实验目录_整理版.md`. Keeping the old question bank, point inventory, video references, and AI chunk bindings would preserve invalid data, block correct ES testing, and make later RAG/question-bank regeneration depend on the wrong point identities.

## What Changes

- **BREAKING** Replace the legacy seed model based on formal experiments and old video points with a static, structured seed generated from the new curated catalog outline.
- **BREAKING** Treat legacy question-bank rows, old experiment points, old video-reference bindings, and old AI evidence/chunk bindings as invalid seed data that may be deleted or reset without audit.
- Preserve the full chapter directory tree from `docs/实验目录_整理版.md`, not only leaf nodes; non-leaf headings become directory nodes and every leaf becomes an experiment point node.
- Treat chapter 21's `暂无对应实验内容` placeholder as empty and do not seed a node for it.
- Seed the 30 manually supplied point-content examples from `docs/30点位例子.txt` by explicit semantic mapping to catalog point nodes for ES/search smoke testing.
- Keep canonical RAG chunks and embeddings as the valid candidate corpus, but clear point-to-chunk evidence bindings so every new point can later rerun the GPU/BGE rerank workflow.
- Update production validation and operations docs so retired seed resources are no longer protected baseline data.
- Leave full question-bank regeneration out of scope for this change because it depends on fresh point-level RAG evidence bindings.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `experiment-catalog-tree`: Replace legacy catalog migration assumptions with a canonical outline-backed seed that preserves the full directory tree, classifies leaves as point nodes, and seeds 30 mapped point-content examples.
- `experiment-question-bank-management`: Redefine the current default experiment question bank as empty after the catalog reset until a future evidence-backed regeneration creates a new bank.
- `hybrid-bge-rag-retrieval`: Retire old point evidence bindings and require future point evidence generation to target catalog node identities instead of legacy experiment/point keys.
- `production-readiness-governance`: Update protected resource and validation requirements so new catalog seeds, sample point content, canonical chunks, and embeddings are protected, while old question-bank and point-evidence seed files are not.

## Impact

- Affected seed data and scripts: `data/seed/**`, catalog seed/import scripts, old question-bank seed/import scripts, point evidence generation/import scripts, and ES indexing smoke data.
- Affected database tables: experiment catalog nodes, point content, point media/video bindings, point evidence bindings, experiment question banks/questions, and any search-index queue/documents derived from retired points.
- Affected docs and validation: `docs/production-operations.md`, `docs/productionization-final-notes.md`, `data/seed/README.md`, `scripts/validate_production_resources.py`, and any resource manifest or protected-count checks.
- Existing canonical chunks and chunk embeddings remain valid and must not be removed by this change.
