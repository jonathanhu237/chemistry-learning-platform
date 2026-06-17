## Context

This change targets the student H5 element experiment learning page. The corrected product model is:

```text
periodic-table learning entry
  -> student selects a family/chapter, e.g. 17族（卤素）
    -> current family/chapter learning page
      -> student selects an element inside the current family, e.g. F / Cl / Br / I / At
      -> page shows selected-element facts and family-wide common properties
      -> page drives student into related experiment points
      -> point detail learning leads to post-learning assessment
```

The page is therefore not a sibling-family chooser. The current family is the current chapter. A top row of sibling family tabs such as `17 / 16 / 15 / 14 / 13` is misleading when it appears as page-level primary navigation. Family/chapter switching belongs to the periodic-table entry or a secondary "switch chapter" affordance.

Current implementation signals:

- `apps/student-web/src/App.tsx` already has `LearningSurface`, `LearningHomePanel`, `LearningProfileTabs`, `LearningProfileHero`, `LearningPropertyCards`, `PropertySectionButton`, point cards, point detail, AI chat, feedback, and assessment handoff.
- `data/seed/student_learning/element_profiles.json` already provides explicit display seed data for 9 enabled profiles, with family elements, property cards, and property sections.
- `student-h5-learning-experience` already requires explicit student learning profile seed, real learning payloads, point detail, mobile-first H5 behavior, AI/feedback settings, and global feedback.
- `student-h5-mobile-design-system` already requires phone-first H5/WebView behavior, touch targets, safe-area handling, and floating overlay governance.

Research context to preserve:

- Chemistry periodic-table products generally use the periodic table as the selection surface and the detail page as the selected object surface. Examples:
  - Royal Society of Chemistry periodic table: table entry plus element detail, trends, history, podcasts, and videos. https://periodic-table.rsc.org/
  - PubChem periodic table and element pages: periodic table/list/game entry, element property pages, downloadable element data, and widgets. https://pubchem.ncbi.nlm.nih.gov/docs/periodic-table-element-pages
  - Ptable: interactive periodic table with property, electron, isotope, compound, and trend views. https://ptable.com/
  - NIST periodic table: authoritative atomic-property reference data. https://www.nist.gov/pml/periodic-table-elements
  - ACS educational explanation: the periodic table is used to reference element information and discern property trends. https://www.acs.org/education/whatischemistry/periodictable.html
- For this product, the mature pattern should be adapted into an experiment-learning path:
  - selected family/chapter identity,
  - within-family element selection,
  - per-element facts,
  - family-wide common properties and trends,
  - property-driven experiment-point learning,
  - point detail,
  - completion-to-assessment.
- Public images/videos may be used as optional reference media only when licensing, attribution, and source URLs are tracked. They must not replace current protected experiment-point resources, current question bank, canonical chunks, embeddings, or manually reviewed point evidence.

## Goals / Non-Goals

**Goals:**

- Make the student H5 learning page a current family/chapter page reached from the periodic-table entry.
- Remove sibling-family tabs from the page's primary navigation and replace them with current-family context plus a secondary return/switch-chapter affordance.
- Add within-family element chips that switch selected-element facts.
- Separate selected-element facts from family-wide common properties:
  - selected-element facts: atomic number, electron configuration, family/group, common valence, elemental state, oxidizing/reducing tendency where applicable;
  - family-wide common properties: shared trend summaries, formulas, reaction tendency, and property sections such as oxidizing property, reducing property, precipitation, coordination, disproportionation, or other seed-defined topics.
- Keep experiment-point groups as the primary learning task below the contextual chemistry summary.
- Keep point detail video-first, with compact explanation context and AI/feedback awareness.
- Preserve phone-first H5/WebView behavior at 360, 390, and 430 CSS-pixel widths.
- Preserve current AI assistant, feedback switch, posttest, authentication, and protected media behavior.

**Non-Goals:**

- Do not introduce a native WeChat mini-program, Taro, uni-app, React Native, or a separate mobile build chain.
- Do not redesign the teacher/admin console.
- Do not change CI/release workflow.
- Do not replace protected production seed resources or derive display facts from RAG chunks at request time.
- Do not make public reference media required for the learning page to work.
- Do not make the page a general encyclopedia page; chemistry facts support the experiment-point learning path.

## Decisions

### Decision 1: Periodic table owns family/chapter selection

The periodic-table learning entry is the place where students choose the family/chapter. The chapter page receives or resolves one active profile and treats it as the current learning context.

Alternatives considered:

- Keep sibling-family tabs at the top of the chapter page. This preserves current implementation but duplicates the periodic-table entry and makes the current page feel like a cross-family index.
- Hide all switching. This is simpler but makes it hard to recover if the student opened the wrong chapter.

Chosen behavior:

- The chapter page shows current family identity and a clear return/switch-chapter control.
- Sibling families are not shown as page-level primary tabs.
- If a default/recommended profile is used because no explicit profile is supplied, the page still presents it as the current family/chapter rather than as a browse-all-families surface.

### Decision 2: Element chips switch per-element facts inside the current family

The current family page needs an element-level selection row, e.g. `F / Cl / Br / I / At` for halogens. Selecting an element changes the element facts area, not the overall chapter.

Data implication:

- The existing `elements` seed entries should be expanded or normalized so each element can expose display facts needed by the UI:
  - atomic number,
  - electron configuration,
  - family/group label,
  - common valence,
  - elemental state,
  - oxidizing/reducing tendency or a safe "not applicable" value,
  - optional concise note.

The current family-wide `property_cards` can remain for common facts, but the API should distinguish element-specific facts from family/common facts to avoid mixing scopes.

### Decision 3: Family-wide common properties follow the selected-element facts

After the selected element facts, the page should show the common properties and trends of the family/chapter. This is where the "chapter general knowledge" lives.

For 17族（卤素）, examples include:

- `X₂` oxidizing ability trend: `F₂ > Cl₂ > Br₂ > I₂`;
- `X⁻` reducing ability trend: `F⁻ < Cl⁻ < Br⁻ < I⁻`;
- typical salt formation;
- silver halide precipitation and photosensitivity;
- displacement reactions used as experimental evidence.

This section should be compact and should lead into property-driven experiment groups. It should not bury the experiment-point list beneath an encyclopedia-length article.

### Decision 4: Experiment-point groups remain the page spine

The page's main learning work is not memorizing facts; it is opening and learning related experiment points. Property sections are the bridge from chemistry trends to experiments.

Recommended page order:

```text
current family/chapter header
within-family element chips
selected-element fact panel
family-wide common properties and trend summary
property selector, e.g. 氧化性 / 还原性 / 与金属离子反应
related experiment-point groups
finish learning / go to assessment
```

The experiment point card should surface:

- point title,
- parent experiment title,
- reaction/formula or concise point summary when available,
- media availability,
- question count,
- learning status when available.

### Decision 5: Point detail remains video-first but not video-dependent

The point detail page keeps available video as the primary learning media. If there is no video, the page must still work and show a graceful empty media state, point title, parent experiment context, observed phenomenon or summary, reaction/principle, and safety/caution notes when available.

The point detail should provide AI context with chapter, property, experiment, point key/title, and concise summary. It should preserve the existing admin-controlled student AI and feedback switches.

### Decision 6: Optional reference media must be manifest-backed

Public images/videos can improve the top chapter page, especially for element appearance or family trend illustration, but they should be optional and explicitly licensed.

Recommended seed shape:

```json
{
  "id": "halogens-chlorine-reference-001",
  "usage": "element_reference",
  "profile_ids": ["halogens-17"],
  "element_symbols": ["Cl"],
  "property_keys": ["oxidizing"],
  "asset_type": "image",
  "source_url": "https://...",
  "license": "CC BY 4.0",
  "attribution": "...",
  "local_path": null,
  "alt_text": "..."
}
```

The UI must function without reference media. Reference media must not be confused with protected experiment media, canonical RAG evidence, or manually reviewed point evidence.

## Risks / Trade-offs

- [Risk] Removing sibling-family tabs may reduce fast switching during development previews. → Mitigation: provide a secondary return/switch-chapter action to the periodic-table entry.
- [Risk] Expanding seed facts can create maintenance overhead. → Mitigation: validate required fields and allow optional fields to degrade gracefully.
- [Risk] Public media licensing may become ambiguous. → Mitigation: require source URL, license, attribution, usage, and alt text in a manifest; treat media as optional.
- [Risk] The top facts area can again become too tall and push experiment points below the fold. → Mitigation: cap the visible fact summary, use expandable detail for secondary facts, and keep point groups visible early on common phone widths.
- [Risk] Existing payload consumers may expect `property_cards` to be family-level. → Mitigation: add new fields for element facts rather than repurposing existing fields silently; preserve old fields until the UI migrates.
- [Risk] Text length in Chinese chemistry formulas/titles can break mobile layout. → Mitigation: verify at 360, 390, and 430 CSS-pixel widths and keep cards responsive with no horizontal scrolling.

## Migration Plan

1. Extend seed validation and profile schema to support selected-element facts and optional reference media metadata.
2. Update the student learning API so one active profile is the current chapter context and sibling profile summaries are available only for secondary navigation if needed.
3. Recompose the student H5 page:
   - current family header,
   - element chips,
   - selected-element facts,
   - family common properties,
   - property selector,
   - experiment-point groups,
   - finish/assessment action.
4. Preserve route behavior for point detail, AI chat, feedback, and posttest.
5. Run backend validation/tests, student-web typecheck/build, and mobile viewport QA.

Rollback strategy:

- Keep existing profile seed fields during migration.
- If the new composition has an issue, restore the previous H5 rendering while leaving additive seed fields harmless.
- Do not delete protected learning, question, chunk, evidence, or media resources as part of this change.

## Open Questions

- Should the periodic-table entry route encode `profile_id`, `chapter_id`, or family number in the URL/state?
- Should selected element default to the first element, the most experiment-relevant element, or a seed-defined default such as chlorine for halogens?
- Should point learning status be introduced in this change or deferred to a learning-progress change?
- Should optional public reference media be linked externally first, with local caching considered later?
