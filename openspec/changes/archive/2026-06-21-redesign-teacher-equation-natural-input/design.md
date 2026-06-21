## Context

The existing multi-equation implementation preserved the important backend boundary: raw teacher input is stored and backend normalization is authoritative for AI/ES/RAG. The product problem is that the visible editing model is still unnatural. Teachers do not want to build equations by clicking `+`, `=`, arrows, and state buttons; they type, paste, or describe reactions.

The screenshots that triggered this change show a more serious backend issue as well: an input like `CL2+2h2 = 2hcl` should be interpreted as an imperfect human attempt at `Cl2 + 2H2 -> 2HCl`, but the current parser treats the casing too literally and produces misleading preview output. Better UX therefore requires both a simpler input surface and a more forgiving normalization pipeline.

Research references remain:

- Moodle/mhchem: natural text input into an editor, with chemistry notation rendering and optional toolbar assistance.
- CKEditor/ChemType: a dedicated equation editor area with preview, where toolbar controls support the editing area rather than becoming the primary workflow.
- ChemType: chemistry-specific notation tools help with subscripts, superscripts, arrows, ions, and state notation, but the goal is faster notation, not forcing users into fragmented form controls.
- MarvinJS/Ketcher/ChemDoodle/PubChem Sketcher: useful for advanced structure drawing, not the default high-school inorganic reaction entry path.

## Goals / Non-Goals

**Goals:**

- Make the default teacher workflow: type or paste natural reaction text, one reaction per line.
- Provide near-real-time backend preview through debounce so teachers see recognition feedback while typing.
- Normalize forgiving inputs such as missing spaces, `=`, `->`, Unicode arrows, inconsistent casing, and common Chinese substance names.
- Distinguish between "system understood this" and "system suggests this correction/balancing."
- Let teachers explicitly accept a normalized/corrected suggestion.
- Add optional AI assistance for generating or fixing reaction candidates from point context.
- Preserve raw teacher input and backend-derived canonical records for AI/ES/RAG.

**Non-Goals:**

- Do not make a symbol popover the main path.
- Do not silently rewrite teacher input while they type.
- Do not use AI as the real-time parser for every keystroke.
- Do not add a full structure drawing dependency as the default editor.
- Do not publish AI-generated equations without teacher acceptance and backend normalization.

## Decisions

### Decision 1: Use a single multiline reaction input as the default

The default equation principle UI should show one large text area labeled for natural reaction entry. Each non-empty line becomes one reaction candidate. This matches how teachers naturally paste from notes, textbooks, or their own memory.

Alternative considered: keep per-equation cards as input containers. Rejected because it makes system structure visible too early. Cards are better as parsed output, not as the primary typing surface.

### Decision 2: Use debounced backend preview, not manual-first checking

The frontend should call the existing/new preview endpoint after input pauses for about 400-600 ms. A manual "重新检查" action can remain for recovery, but the default feedback loop should feel live.

Alternative considered: call the backend on every keypress. Rejected because it adds unnecessary load and flicker. Debounce gives teachers the same perceived immediacy without treating every keystroke as a final equation.

### Decision 3: Expand backend normalization before adding AI

The backend parser should first handle deterministic human-input cleanup:

- Normalize arrows: `=`, `->`, `=>`, `→`, `<=>`, `⇌`.
- Insert logical spacing around separators.
- Canonicalize likely element symbols and common compounds while preserving raw input.
- Recognize common Chinese aliases such as 氯气, 氢气, 氯化氢, 盐酸, 溴水, 碘, 淀粉, 氢氧化钠, 硫酸铜 where applicable.
- Return warnings when a casing or alias correction was applied.
- Suggest balanced forms when a simple stoichiometric balance can be inferred confidently.

Alternative considered: rely on an LLM for all correction. Rejected because deterministic chemistry cleanup is faster, cheaper, more testable, and safer for core persistence.

### Decision 4: AI assistance is explicit and teacher-accepted

AI should be available through explicit actions such as:

- "AI 修正当前反应式"
- "AI 根据现象生成反应式"
- "AI 补全并配平"

AI returns one or more draft candidates with rationale. The teacher must choose "采用" before the candidate replaces or appends to the multiline input. After acceptance, the backend preview/normalization still runs and remains authoritative.

Alternative considered: automatic AI suggestions while typing. Rejected because it would be slow, costly, and can feel intrusive. The teacher should stay in control.

### Decision 5: Parsed output should be compact and confidence-oriented

Preview output should show a compact list below the text area:

```text
系统理解为
1. Cl2 + H2 -> 2HCl        [建议采用配平]
   已将 CL2/HCL 识别为 Cl2/HCl；当前系数疑似未配平
```

The input remains the editing surface. Parsed output is feedback plus accepted suggestions.

Alternative considered: render full card chrome for every equation. Rejected because it visually overpowers the task when most points only need one to three reactions.

### Decision 6: Store normalized rows from accepted/current text, not preview UI state

Saving point content should split the current multiline input into rows and submit those raw rows. The backend normalizes on save and stores canonical records. Preview state is not persisted directly.

Alternative considered: persist accepted preview objects from the frontend. Rejected because it risks saving stale or frontend-mutated records.

## Risks / Trade-offs

- [Risk] Debounced preview can race with older responses. -> Mitigation: track request sequence or input snapshot and ignore stale responses.
- [Risk] Casing correction can misinterpret uncommon symbols. -> Mitigation: only auto-correct against a known periodic-table symbol set and common-alias dictionary, and return correction warnings.
- [Risk] AI suggestions can be chemically wrong. -> Mitigation: show them as drafts only, require teacher acceptance, and run backend normalization/validation after acceptance.
- [Risk] Balancing is non-trivial for complex reactions. -> Mitigation: start with simple inorganic reactions; return "无法可靠配平" instead of fabricating certainty.
- [Risk] The new multiline model must preserve multi-row storage. -> Mitigation: split non-empty lines into `reaction_equations` input rows at preview/save boundaries.

## Migration Plan

1. Keep existing stored `reaction_equations` rows.
2. Hydrate the new multiline editor by joining existing raw rows with newline separators.
3. On save, split the current multiline value into row inputs and submit them through the existing point content payload.
4. Keep backend normalized row shape unchanged unless adding optional suggestion metadata fields.
5. Rollback can restore row-based input because raw rows remain preserved.

## Open Questions

- Should AI assistance use the current configured teacher AI provider immediately, or start with deterministic correction only and hide AI until provider health is available?
- Should accepted balanced suggestions replace the raw line or append as a new candidate line?
- Which Chinese alias dictionary should be seeded first: only existing 30 point samples, or a broader high-school inorganic list?
