## Why

Teachers need to keep the current "one line = one reaction equation" authoring model while still attaching explanatory notes such as alkaline medium, excess reagent, or reagent-source explanations to that same reaction. Today any extra explanatory line is treated as another reaction candidate, and bracket-based inference would be ambiguous with real chemical notation such as `Al(OH)3`, `Ca3(PO4)2`, or state markers.

This change introduces an explicit, AI-friendly inline annotation DSL using `//`, so generated or teacher-authored reaction lines can preserve notes for display, search, and AI context without polluting reactant/product parsing.

## What Changes

- Define a reaction-line DSL: `EQUATION_CORE [ // ANNOTATION ]`.
- Preserve the existing multiline model: each non-empty line remains exactly one reaction equation row.
- Parse only the `EQUATION_CORE` portion into canonical equation display, mhchem, reactants, products, formulae, and balancing diagnostics.
- Preserve `ANNOTATION` as part of the same reaction row for teacher/student display, AI context, and search text.
- Extract annotation-side formulae and condition tags into separate derived fields such as `annotation_formulae` and `condition_tags`; these MUST NOT be merged into `reactants` or `products`.
- Update AI equation assistance/import expectations so AI converts bracketed or prose notes into `//` annotations instead of new lines.
- Fix Unicode ion charge handling so inputs equivalent to `Mn^2+`, `Cl-`, and `OH-` do not become misleading formula tokens such as `MN2`.
- Keep raw teacher input non-destructive; suggestions may rewrite the equation core but must preserve inline annotations unless the teacher explicitly accepts annotation edits.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `catalog-point-natural-equation-authoring`: Defines `//` inline annotation semantics while preserving one-line-per-equation input and preview behavior.
- `catalog-point-chemical-equation-authoring`: Extends backend-normalized reaction records with equation core, annotations, annotation formulae, and condition tags while keeping reactants/products sourced only from the equation core.
- `teacher-experiment-catalog-editor`: Updates teacher preview and AI assistance behavior to show and preserve inline annotations attached to a reaction row.
- `student-h5-learning-experience`: Updates student-facing experiment principle rendering so inline annotations are visible with their reaction equation.

## Impact

- Backend reaction parser and preview/assist endpoints under `server/app/domains/catalog_tree/equations.py` and `server/app/api/admin/admin_catalog_tree.py`.
- Catalog point content save/hydration paths that persist normalized reaction equation rows.
- Search, ES, AI, and RAG context builders that consume normalized reaction fields.
- Teacher catalog content editor preview and AI suggestion application.
- Student point detail rendering for equation-mode principles.
- Tests for reaction parsing, content payload mapping, teacher preview contracts, search/AI context, and student display.
