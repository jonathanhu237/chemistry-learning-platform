## Context

The roadmap change already established the data contract for multi-equation point authoring: teachers enter raw reaction strings, while the backend owns parsing, normalization, validation, and derived AI/ES/RAG fields. The first UI implementation kept that boundary, but the visible interaction is too technical: helper buttons sit directly on the main page, the primary action says “后端预览”, and preview/status output reads like implementation diagnostics.

The preferred reference model is lightweight chemistry notation authoring, not a full chemical structure drawing tool:

- Moodle/mhchem-style entry: teachers type natural formula/equation text and receive rendered chemistry notation.
- CKEditor MathType/ChemType-style workflow: the main surface stays text-first, with chemistry controls available through a toolbar/dialog.
- Ketcher, MarvinJS, ChemDoodle, and PubChem Sketcher are better fits for advanced molecular/reaction drawing; they are too heavy for the default high-school inorganic experiment point editor.

## Goals / Non-Goals

**Goals:**

- Make equation authoring feel like a focused chemistry content editor rather than a backend debug form.
- Keep the UI fully Chinese.
- Show each reaction as a card containing raw teacher input, backend-normalized display preview, and status/warnings.
- Move symbol helpers into grouped controls so the primary form is not dominated by snippets.
- Preserve row add, edit, delete, and reorder behavior for multiple equations.
- Keep backend preview/save responses authoritative for normalized chemistry meaning.

**Non-Goals:**

- Do not add Ketcher, MarvinJS, ChemDoodle, PubChem Sketcher, or any other structure editor as the default authoring surface.
- Do not move parsing, balancing, or AI/ES/RAG normalization into the frontend.
- Do not change backend schemas, migrations, or normalization APIs in this UI-only refinement.
- Do not redesign unrelated point content fields such as phenomenon explanation, safety note, video binding, or AI context.

## Decisions

### Decision 1: Use per-equation cards as the primary surface

Each equation row will be presented as a compact card with an index/title, raw input, inline preview, status message, and row actions. This better matches the mental model of “several reaction equations for this point” than a global toolbar followed by blank rows.

Alternative considered: keep the current `Form.List` row layout and only restyle buttons. Rejected because the current layout still makes the helper toolbar the most visible element and hides the equation row as an implementation detail.

### Decision 2: Replace permanent helper buttons with grouped symbol insertion

Common snippets remain useful, but they should be available through a grouped popover/dropdown such as “常用符号”. Groups should include reaction symbols, states, ions, and common reagents. Insertion still only changes raw text in the focused row.

Alternative considered: remove helper snippets entirely. Rejected because simple chemistry keyboard assistance is useful for teachers and aligns with ChemType-style controls.

### Decision 3: Rename preview actions to product language

The main action will use teacher-facing wording such as “检查” instead of “后端预览”. The UI may still call the existing backend preview API internally, but no main visible label should ask teachers to think in backend terms.

Alternative considered: auto-preview after every keystroke. Deferred because it may create noisy network calls; manual “检查” plus inline preview is safer for the current implementation. A future debounced preview can be added without changing the contract.

### Decision 4: Render backend-normalized results inline

When preview/save returns normalized records, each card should show the canonical display/mhchem result and warnings close to the input that produced them. Advanced diagnostic fields may remain hidden or compact, but the main preview must not appear as a generic alert block.

Alternative considered: a single global preview panel below the form. Rejected because teachers need to connect feedback to the specific equation row.

### Decision 5: Keep advanced structure drawing out of scope

The default teacher workflow remains text-plus-preview. Full drawing tools can be evaluated later as an optional advanced modal for molecular structures or complex organic reactions, but this change must not introduce their package size, licensing, or interaction complexity.

## Risks / Trade-offs

- [Risk] Manual “检查” can leave previews stale while typing. -> Mitigation: show clear row status and keep save behavior authoritative.
- [Risk] Card UI adds vertical height for many equations. -> Mitigation: keep cards compact and row actions icon-sized.
- [Risk] Teachers may expect equation balancing guarantees from the preview. -> Mitigation: label parser warnings plainly and rely on backend validation messages.
- [Risk] Existing tests may assert old strings such as “后端预览”. -> Mitigation: update contract tests to assert product-facing Chinese labels and backend-authority behavior.

## Migration Plan

1. Ship the UI refinement behind the existing point content editor; no data migration is required.
2. Existing equation rows continue to load as raw text and receive previews through the existing backend preview response.
3. Rollback can restore the previous component layout without changing saved point content.

## Open Questions

- Should a future version add debounced preview after the teacher stops typing?
- Should an optional advanced structure drawer be exposed only for selected chemistry topics, or remain out of the catalog editor entirely?
