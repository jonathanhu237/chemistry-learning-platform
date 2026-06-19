## Context

The student H5 chapter page already has within-family element selection, an element tile visual language, family-level common properties, and experiment-point video groups. The current selected-element card combines a generated heading with `element.note`, but the note can contain family-level trend text. The result looks grammatical yet feels wrong: a compact current-element card appears to explain the whole family.

External element references suggest a useful split:

- periodic-table tiles identify the element quickly with atomic number, symbol, and name
- fact boxes expose stable facts such as group, period, state, mass, and electron configuration
- prose sections explain longer chemical meaning, trends, uses, and history
- interactive tables often foreground one selected property rather than all properties at once

The student H5 page needs an even narrower card because experiment videos are the primary learning task. The card should introduce the current observation target, not become an encyclopedia section.

## Goals / Non-Goals

**Goals:**

- Redesign the selected-element card as a compact experiment-learning card.
- Preserve the existing periodic-table element square as the visual anchor.
- Surface one curated focus property for the selected element.
- Explain why the selected element matters to the current chapter's experiments.
- Separate compact card copy from detailed facts, family trends, and element-detail text.
- Keep the experiment-point task area discoverable on 360px to 430px phone viewports.

**Non-Goals:**

- Do not redesign the full element detail page.
- Do not add a global element encyclopedia or whole-app search behavior.
- Do not change route-stack or tab-page architecture.
- Do not replace the experiment video view or point detail flow.
- Do not infer card copy from RAG chunks or generated front-end sentence templates.

## Decisions

### Decision 1: Use a three-layer card model

The selected-element card should render three semantic layers:

```text
+------------------------------------------------+
| [periodic tile]  Current observation element    |
|                  Chlorine                       |
|                  Focus: Strong oxidizing agent  |
|                  Relevance: links directly to   |
|                  halogen displacement videos    |
|                  [Group 17] [Gas] [-1 valence]  |
|                                      Details -> |
+------------------------------------------------+
```

- Identity layer: the existing periodic-table tile with atomic number, symbol, and English label.
- Focus-property layer: a short, curated property line such as `Strong oxidizing agent` or `Most electronegative element`.
- Experiment-relevance layer: one sentence explaining why the element matters to this chapter's experiment tasks.

Rationale: this borrows the strong recognition pattern from periodic-table tiles, the focused-property pattern from interactive periodic tables, and the student-facing explanation style from teaching references.

Alternative considered: keep the current title plus note structure and only rewrite the seed text. That would reduce the immediate awkwardness but still leave the component semantics too loose; future seed edits could reintroduce family-level text into the compact card.

### Decision 2: Add card-specific seed fields

Each enabled element in a student learning profile should support card-specific fields separate from existing detailed fields:

```json
{
  "card_focus": "Strong oxidizing agent",
  "card_relevance": "Connects directly to chloride, bromide, and iodide displacement observations.",
  "card_tags": ["Group 17", "Gas", "-1 valence"]
}
```

Chinese display copy can be authored in the seed, for example:

```json
{
  "card_focus": "氧化性强，常用于卤素置换对比",
  "card_relevance": "氯水能把 Br-、I- 氧化成对应单质，现象直接对应本章实验视频。",
  "card_tags": ["17族卤素", "气体", "常见-1价"]
}
```

Rationale: the card should be curated content, not composed from `element.name`, `profile.family_name`, or family trend notes at render time.

Alternative considered: reuse `note` as the card body. This is rejected because `note` already carries broader explanation and has proven too ambiguous.

### Decision 3: Keep detailed chemistry outside the compact card

The compact card should not show full electron configuration, density, melting point, long redox trends, or family-wide trend paragraphs. Those belong in the facts/common-property area or element detail view.

Rationale: the chapter page must keep experiment videos discoverable and avoid becoming a dense reference page before students reach the primary tasks.

Alternative considered: mimic a full RSC-style fact box in the top card. This is useful for a detail page but too heavy for the chapter page.

### Decision 4: Define explicit fallback behavior

If new card fields are missing during migration, the UI may fall back to concise existing facts in this order:

1. `redox_tendency` if it is already element-specific and short
2. `common_valence` plus `state_at_20c`
3. group/period/block tags only with an unavailable focus state

The fallback must not generate prose in the form `<element>在<family>中的位置` or prefix family-level trends with the selected element name.

Rationale: this keeps partial migration safe while preventing the exact awkward pattern that triggered the redesign.

## Risks / Trade-offs

- Curated copy increases seed-maintenance work -> mitigate with validation that requires card copy for enabled elements and with short authoring guidelines.
- Some elements have weak direct experiment relevance -> mitigate by allowing relevance to describe chapter role, comparison role, or "extension only" role.
- Existing `note` may still appear elsewhere -> mitigate by explicitly reserving `note` or renamed detail fields for details/facts sections, not the compact card.
- Long Chinese labels can overflow on phone cards -> mitigate with maximum line counts, responsive wrapping, and viewport QA at 360px, 390px, and 430px widths.

## Migration Plan

1. Extend the student learning element seed schema with `card_focus`, `card_relevance`, and `card_tags`.
2. Author card copy for all enabled profile elements, starting from halogens and then covering existing active profiles.
3. Expose card fields through the student learning payload while keeping existing detailed fields.
4. Update the H5 selected-element card to render the new three-layer model.
5. Keep existing element detail/fact sections intact, then verify that family trends remain visually separate.
6. Remove or stop using the old generated heading/body pattern for the compact card.

Rollback is straightforward: retain old fields in the payload during migration and gate the new card rendering behind the presence of card fields until validation is complete.

## Open Questions

- Should `card_focus` always be a property phrase, or can it be an experiment-action phrase such as `用于观察置换反应`?
- Should `card_tags` be fully curated per element, or can some tags such as group/period/state be derived from stable factual fields?
- Should the compact card link to the element detail route, expand inline details, or keep the existing detail action only?
