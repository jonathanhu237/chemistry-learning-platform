## Context

Teachers currently author experiment principles with a natural equation editor where each non-empty line is one reaction equation. That line contract is correct and must remain stable because teachers, AI importers, preview, save, and indexing all depend on it.

The missing piece is row-level explanatory text. Teachers often need to attach notes such as alkaline medium, excess reagent, reagent source, or observation constraints to the same equation. A separate note line is wrong because it becomes another reaction candidate. Bracket inference is also unsafe because real chemistry uses parentheses for formula groups, state markers, and prose conditions.

This change treats reaction equation text as a tiny explicit language:

```text
REACTION_LINE := EQUATION_CORE [ " // " ANNOTATION ]
```

The ASCII `//` delimiter is reserved for inline annotations. The backend parses only `EQUATION_CORE` as chemistry and keeps `ANNOTATION` attached to the same row for display, search, AI context, and derived annotation metadata.

## Goals / Non-Goals

### Goals

- Keep one non-empty input line as exactly one reaction equation row.
- Use `//` as an explicit delimiter that AI and teachers can understand.
- Parse only the equation core for canonical display, mhchem, reactants, products, balancing diagnostics, and core formula terms.
- Preserve annotation text on the same row for teacher preview, student display, search text, and AI/RAG context.
- Derive annotation-side fields such as `annotation_formulae` and `condition_tags` without merging them into reactants or products.
- Normalize Unicode ion charge notation before formula extraction so charged species do not become misleading elements or counts.

### Non-Goals

- Do not add a structure drawing editor.
- Do not make teachers put annotations on a separate line.
- Do not treat parentheses alone as annotation syntax.
- Do not merge annotation formulae into core participant lists.
- Do not require a database schema migration if the existing reaction-row metadata JSON can carry the additional fields.

## Decisions

### Decision 1: Reserve `//` as the annotation delimiter

Each saved or previewed reaction row may contain one annotation delimiter. Text before the first delimiter is the equation core. Text after it is the annotation. AI-generated text SHOULD emit spaces around the delimiter (` // `) for readability, but the backend MAY tolerate missing spaces.

Example:

```text
Mn^2+ + ClO- + 2OH- -> MnO2↓ + Cl- + H2O // NaClO溶液本身呈碱性，提供OH-
```

This remains one reaction row. The note is not a second equation candidate.

### Decision 2: Keep raw input non-destructive and store annotation metadata beside the row

The raw teacher line remains the source text, including the `//` suffix. The normalized row SHOULD expose:

- `raw_text`: full teacher line.
- `equation_core`: raw text before `//`.
- `annotation_text`: raw text after `//`, trimmed.
- `canonical_display`: normalized display for the equation core only.
- `canonical_mhchem`: mhchem output for the equation core only.
- `reactants` and `products`: derived from the equation core only.
- `formulae`: core formula terms only.
- `annotation_formulae`: formula-like terms found in the annotation only.
- `condition_tags`: normalized condition qualifiers derived from the annotation, such as acidic, alkaline, excess, dilute, concentrated, heat, or light.
- `plain_search_text`: display/search text combining the equation core and annotation.

The implementation SHOULD store new fields in existing reaction metadata where possible, so the change remains compatible with current point content persistence.

### Decision 3: Annotation fields may enrich search and AI, but not core chemistry participants

`annotation_text`, `annotation_formulae`, and `condition_tags` SHOULD be included in ES/search documents and AI/RAG context blocks because they help users find the experiment and help AI understand conditions.

They MUST NOT be merged into `reactants`, `products`, core `formulae`, balancing diagnostics, or evidence-query participant hints. This keeps tokenizer/search benefits without corrupting reaction semantics.

### Decision 4: AI assistance must preserve or emit annotation syntax

When AI imports or repairs experiment principle text, it SHOULD place explanatory prose on the same reaction line after `//`. If the teacher already has an annotation suffix and accepts an AI correction for only the equation core, the suffix MUST be preserved unless the teacher explicitly accepts annotation edits.

AI SHOULD convert ambiguous bracket or prose notes into the explicit delimiter. The annotation suffix is a human-facing Chinese supplemental explanation, not a machine-label field, so AI MUST NOT emit labels such as `note:`, `condition:`, `amount:`, or `medium:`:

```text
Mn^2+ + ClO- + 2OH- -> MnO2↓ + Cl- + H2O // NaClO溶液本身呈碱性，提供OH-
```

### Decision 5: Unicode ion normalization is part of the parsing contract

The backend must normalize common Unicode charge forms before formula extraction. Inputs equivalent to `Mn^2+`, `Cl-`, and `OH-` must be recognized as charged species and must not produce misleading tokens such as `MN2`.

This applies to both equation core parsing and annotation formula extraction.

## Risks / Trade-Offs

- `//` is a reserved delimiter. A teacher who truly needs a literal `//` inside a note would need a later escape convention; this is acceptable for v1 because chemistry equation text does not normally use `//`.
- Annotation formula extraction can be imperfect. That field is useful for search and AI context only, so it is deliberately separate from core participant fields.
- Some existing consumers may read only `canonical_display`. They need targeted updates to include `annotation_text` where user-facing or context-facing display matters.

## Migration Plan

- Existing rows without `//` remain unchanged.
- Existing raw lines with explanatory second lines are not automatically migrated in this change; AI assistance/import may rewrite future content into the delimiter syntax.
- Saved rows should hydrate the editor from `raw_text` so teacher-authored annotations round-trip exactly.

## Open Questions

- Annotation text is displayed as a smaller "补充说明" line under the equation so teachers and students see Chinese prose instead of internal labels.
- Whether `condition_tags` should use English enum keys, Chinese display labels, or both should follow the existing search/AI metadata conventions in the codebase.
