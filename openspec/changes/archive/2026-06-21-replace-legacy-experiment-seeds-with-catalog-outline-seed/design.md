## Context

The admin console now uses a chapter-scoped catalog tree. The canonical experiment outline has moved to `docs/实验目录_整理版.md`, while the database and several seed/import scripts still reflect the old formal-experiment and video-point inventory.

Verified source facts:
- `docs/实验目录_整理版.md` is the new canonical source for the experiment catalog tree.
- The catalog seed MUST preserve the full structure, not just leaves: `##` section headings are directory nodes, non-leaf bullet items are directory nodes, and leaf bullet items are experiment point nodes.
- The current outline contains 569 catalog nodes under existing chapter contexts: 176 directories and 393 point nodes.
- Chapter 21 contains the cleanup placeholder `暂无对应实验内容`; it MUST be treated as empty and MUST NOT seed a directory or point.
- There is no active `(点位)` marker contract. All leaf nodes are points by structure.
- The corrected chapter 13 entries are two distinct points: `NaClO + MnSO₄` and `NaClO + 品红溶液`.
- `docs/30点位例子.txt` contains 30 point-content examples used for ES/search smoke testing. They are randomly selected and MUST be semantically mapped to concrete catalog point nodes.

Current legacy state to retire:
- `server/migrations/020_experiment_catalog_tree.sql` seeds catalog data from `formal_experiments` and `experiment_video_points`.
- `server/migrations/021_separate_catalog_directory_point_nodes.sql` normalized old `hybrid`/`shortcut` style nodes but did not rebuild from the new outline.
- Active legacy counts observed during exploration included 379 catalog nodes, 300 point nodes, 77 formal experiments, 300 old video point evidence bindings, 77 question banks, and 2,310 old questions.
- `scripts/generate_video_point_default_evidence.py` implements a useful GPU/BGE rerank flow, but its IO model is legacy `experiment_id + point_key`; it cannot be reused unchanged for the new catalog tree.
- `scripts/import_manual_reviewed_point_evidence.py`, `scripts/point_aware_question_bank.py`, and production resource validation docs/scripts still protect or consume invalid old point/question/evidence resources.

The user's product decision is explicit: old question banks, old points, old video references, and old point-to-AI-chunk evidence bindings are invalid and may be deleted from the seed layer without audit. Canonical RAG chunks and embeddings remain valid candidate corpus data and MUST be preserved.

## Goals / Non-Goals

**Goals:**
- Replace old seed inputs with a structured catalog seed derived from `docs/实验目录_整理版.md`.
- Preserve the full experiment directory tree under the existing chapter model.
- Seed exactly 30 mapped point-content examples from `docs/30点位例子.txt` for ES/search smoke tests.
- Reset legacy question-bank and point-evidence seed baselines to empty/retired states.
- Keep canonical RAG chunks and embeddings available for future catalog-node evidence generation.
- Update validation and operations docs so protected resources match the new reality.

**Non-Goals:**
- Do not regenerate the full question bank in this change.
- Do not bind all new points to RAG chunks in this change.
- Do not build a runtime Markdown parser as the production seed source.
- Do not preserve old experiment/question/evidence identity mappings for audit.
- Do not migrate old video bindings or old AI evidence to new point nodes.

## Decisions

### Decision 1: Use a structured static catalog seed, not runtime Markdown parsing

The production seed should be a structured file committed under `data/seed/**`, for example `data/seed/experiment_catalog/catalog_tree.json`, generated from the curated outline and then validated. This follows the user's direction to directly replace the old seed rather than introduce a parser as production behavior.

Recommended seed fields:
- `chapter_number`
- `seed_key`
- `parent_seed_key`
- `node_kind`: `directory` or `point`
- `title`
- `path_titles`
- `display_order`
- `source_doc`
- `source_line`

Stable identity should be deterministic from chapter number plus full path and sibling order, because titles may repeat across chapters and branches. The importer can then create stable `experiment_catalog_nodes` rows and point content rows from seed keys.

Alternative considered: parse `docs/实验目录_整理版.md` directly on every seed/import run. Rejected because it makes whitespace and editing style part of production behavior and obscures review of the exact seed payload.

### Decision 2: Preserve the whole tree and classify leaves as points

The new outline is a complex directory tree. It is not correct to seed only leaf nodes, because the product needs the chapter directory tree for navigation, grouping, authoring, moving nodes, publishing state, and teacher workbench context.

Classification rules:
- Existing chapters remain chapter contexts/selectors.
- Every `##` heading under a chapter becomes a directory node.
- Every bullet with children becomes a directory node.
- Every bullet without children becomes a point node.
- Chapter 21 placeholder text is ignored and seeds no node.
- The structured seed must validate to 569 catalog nodes: 176 directories and 393 points.
- No seeded point node may have children.

### Decision 3: Destructively reset invalid legacy seed data

The catalog seed/import flow should clear or replace old seed-derived rows rather than attempting a legacy migration. This includes old catalog nodes, old point content, old point media/video bindings, old point evidence bindings, old question banks, old questions, old search documents derived from retired points, and seed artifacts that exist only to support them.

The reset must preserve:
- Canonical text/chunk corpus tables.
- Chunk embeddings.
- Analyzer dictionaries and ES infrastructure assets.
- User/auth/course data not generated from the retired experiment seed.

Alternative considered: migrate old formal experiments and points into new nodes using best-effort matching. Rejected because the user determined the old topic/question/evidence relationships are invalid and do not deserve audit preservation.

### Decision 4: Seed the 30 examples by explicit point mapping

`docs/30点位例子.txt` has internal numbered phenomenon/safety lists, so it should not be treated as a naive numbered-list import. For this change, create an explicit seed mapping from each example to a catalog point node. Each mapped example should create or update `experiment_catalog_point_content` for the target point:
- `principle_mode = text`
- `principle_text = 实验原理`
- `phenomenon_explanation = 现象解释`
- `safety_note = 安全提示`
- teacher-only notes remain empty unless a seed explicitly supplies them
- content may be published for ES/search smoke tests, while unmapped points remain empty/draft unless product code already has a separate status model

Required mapping:

| # | Example title | Target catalog path |
|---|---|---|
| 1 | 第18章 五 焰色反应 | 第18章 碱金属和碱土金属 / 五、焰色反应 / 锂、钠、钾、钙、锶、钡盐的焰色反应 |
| 2 | 第18章 一 1.钠加热燃烧实验 | 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 钠加热燃烧实验 |
| 3 | 第18章 一 2.镁条燃烧实验 | 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 镁条燃烧实验 |
| 4 | 第18章 一 3.钠与水反应 | 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 钠与水反应 |
| 5 | 第18章 一 5.镁与冷／热水反应 | 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 镁与冷／热水反应 |
| 6 | 第18章 一 6.钙与水反应 | 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 钙与水反应 |
| 7 | 第15章 二 （1）亚硝酸的生成与分解 | 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸的生成与分解 |
| 8 | 第15章 二 （2）亚硝酸的氧化性 | 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸的氧化性 |
| 9 | 第15章 二 （3）亚硝酸的还原性 | 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸的还原性 |
| 10 | NaNO₂ + 对氨基苯磺酸 + 萘胺 | HAc酸性体系 | 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸根的检验方法 / NaNO₂ + 对氨基苯磺酸 + 萘胺 | HAc酸性体系 |
| 11 | NaNO₂ + KI + CCl₄ | H₂SO₄酸性体系 | 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸根的检验方法 / NaNO₂ + KI + CCl₄ | H₂SO₄酸性体系 |
| 12 | 浓硝酸 + 硫粉 | 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸的氧化性 / 浓硝酸 + 硫粉 |
| 13 | 浓硝酸 + Na₂S | 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸的氧化性 / 浓硝酸 + Na₂S |
| 14 | 浓硝酸/稀硝酸 + 铜 | 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸的氧化性 / 浓硝酸/稀硝酸 + 铜 |
| 15 | FeSO₄·7H₂O + NaNO₃ + 浓硫酸 | 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸根的检验 / FeSO₄·7H₂O + NaNO₃ + 浓硫酸 |
| 16 | 难溶性硅酸盐的生成——“水中花园” | 第17章 硼族元素 / 一、硼、硅的相似相异性 / 难溶性硅酸盐的生成——“水中花园” |
| 17 | KI + 浓硫酸 | 湿的醋酸铅试纸 | 第13章 卤族元素 / 三、卤素离子的还原性（通风橱内进行） / 利用浓硫酸比较卤素离子的还原性 / KI + 浓硫酸 | 湿的醋酸铅试纸 |
| 18 | KBr + 浓硫酸 | 湿的KI-淀粉试纸 | 第13章 卤族元素 / 三、卤素离子的还原性（通风橱内进行） / 利用浓硫酸比较卤素离子的还原性 / KBr + 浓硫酸 | 湿的KI-淀粉试纸 |
| 19 | KCl + 浓硫酸 | 湿的pH试纸 | 第13章 卤族元素 / 三、卤素离子的还原性（通风橱内进行） / 利用浓硫酸比较卤素离子的还原性 / KCl + 浓硫酸 | 湿的pH试纸 |
| 20 | NaClO + MnSO₄ | 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 次氯酸盐的氧化性 / NaClO + MnSO₄ |
| 21 | NaClO + 品红溶液 | 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 次氯酸盐的氧化性 / NaClO + 品红溶液 |
| 22 | NaClO + KI-淀粉 | 酸性体系 | 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 次氯酸盐的氧化性 / NaClO + KI-淀粉 | 酸性体系 |
| 23 | KClO₃ + 浓盐酸 | 湿 KI-淀粉试纸 | 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 氯酸盐的氧化性 / KClO₃ + 浓盐酸 | 湿 KI-淀粉试纸 |
| 24 | KClO₃ + Na₂SO₃ + AgNO₃ | 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 氯酸盐的氧化性 / KClO₃ + Na₂SO₃ + AgNO₃ |
| 25 | KClO₃ + KI + CCl₄ | 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 氯酸盐的氧化性 / KClO₃ + KI + CCl₄ |
| 26 | KClO₃ + KI-淀粉 | 酸性体系 | 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 氯酸盐的氧化性 / KClO₃ + KI-淀粉 | 酸性体系 |
| 27 | 高氯酸盐的氧化性 | 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 高氯酸盐的氧化性 |
| 28 | 卤化银的感光性 | 第13章 卤族元素 / 七、金属卤化物的性质 / 卤化银的感光性 |
| 29 | 过氧化氢的酸性 | 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的酸性 |
| 30 | H₂O₂ + KI | 酸性体系 | 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的氧化性 / H₂O₂ + KI | 酸性体系 |

### Decision 5: Retire old point evidence and adapt future rerank work to catalog nodes

Old `experiment_video_point_evidence` bindings and old AI-bound chunks are invalid for the new tree. The future evidence generation flow should reuse the existing GPU/BGE rerank strategy but change identity and scope:
- Input points come from leaf catalog nodes.
- Queries include point title plus full catalog path.
- Output evidence binds to `catalog_node_id` or stable catalog seed key, not `experiment_id + point_key`.
- The BGE service URL defaults must align with the actual compose/runtime port configuration before reuse.

This change only resets the invalid evidence state and preserves the canonical chunks/embeddings. Full rerank regeneration is a future task unless implementation finds a small validation stub necessary.

### Decision 6: Validation becomes the source of safety

Because this is a destructive seed replacement, validation must be concrete:
- Structured catalog seed validates to 569 nodes, 176 directories, and 393 points.
- Chapter 21 seeds zero nodes.
- Every leaf is a point and no point has children.
- The two corrected points `NaClO + MnSO₄` and `NaClO + 品红溶液` both exist under the chapter 13 hypochlorite branch.
- The 30 content examples all resolve to unique point nodes.
- Old question-bank and old point-evidence protected counts are removed from production validation.
- Canonical chunks and embeddings continue to pass protected-resource checks.

## Risks / Trade-offs

- Data reset can remove useful historical rows if run against a shared database -> Mitigation: scope reset tooling to seed-derived experiment catalog/question/evidence tables and document that this is an intentional seed replacement.
- Titles repeat across chapters and branches -> Mitigation: use chapter plus full path plus sibling order for deterministic seed identity.
- Future RAG regeneration may be blocked by BGE service URL/port mismatch -> Mitigation: record the mismatch in tasks and require catalog-node rerank tooling to validate service health before generating evidence.
- ES smoke coverage is limited to 30 samples -> Mitigation: treat those samples only as smoke content and do not imply full question-bank readiness.
- `docs/实验目录_整理版.md` may continue to evolve -> Mitigation: require the structured seed and validation report to be updated together when the outline changes.

## Migration Plan

1. Add structured catalog-tree seed and explicit 30-example content seed.
2. Add validation that compares the seed against the expected counts and required mapped paths.
3. Update/import seed logic to reset old catalog/question/evidence-derived rows and import the new tree/content.
4. Update ES/search indexing smoke paths to use the 30 content-bearing catalog point nodes.
5. Update production resource validation and docs to protect the new seed and stop protecting retired old bank/evidence resources.
6. Run OpenSpec validation and repository tests relevant to seed import, catalog APIs, validation scripts, and search indexing.

Rollback for production-like environments is database backup restore plus reverting this change. The implementation should not attempt to keep old/new seeds live side by side.

## Open Questions

- Exact seed file names can follow existing repository conventions, but the implementation should keep catalog tree seed and 30-example content seed separate for easier review.
- Whether the 30 seeded content rows should be published immediately or imported as draft depends on existing point-content status semantics; ES smoke tests require a published/indexable path for those rows.
