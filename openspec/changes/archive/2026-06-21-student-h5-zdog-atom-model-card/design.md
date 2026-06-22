## Context

The current student H5 learning facts view is implemented under `apps/student-web/src/features/learning/LearningFactsView.tsx`. It renders:

```text
LearningFactsView
├─ LearningElementChips
├─ LearningSelectedElementFacts
│  ├─ selected element tile: atomic number / symbol / English name
│  └─ 2x3 static fact cards
├─ LearningReferenceMedia
├─ LearningFamilyCommonProperties
└─ LearningPropertySectionSummaries
```

The element tile itself works well visually. The weak part is the rest of `LearningSelectedElementFacts`: it repeats database-like fields and makes the phone learning page feel like a compact admin record rather than an interactive chemistry lesson.

There is a separate Zdog prototype at `C:\Users\38122\Documents\zdog`, final commit `e665060 Finalize Zdog atom viewer prototype`. It is a React + Vite + `zdog` prototype with:

- `src/components/AtomViewerZdog.tsx`: canvas-based Bohr/orbital model renderer.
- `src/data/orbitalOptions.ts`: electron-configuration parsing, valence subshell selection, orbital option resolution, and spin-slot distribution.
- `src/components/ModeSegment.tsx`: Bohr/Orbital mode switch.
- `src/components/OrbitalSpinDisplay.tsx`: orbital spin-box display.
- `src/data/testElements.ts`: small prototype fact data for 8 elements only.

The prototype has been built successfully and is reported smooth on phone hardware. Its production bundle is acceptable for an educational visualization feature. However, the standalone demo is English, dark-themed, and backed by limited demo fact data, so it should not be embedded directly into the student H5.

The student learning seed currently covers 47 profile element symbols:

```text
Ag, Al, Ar, As, At, B, Ba, Bi, Br, C, Ca, Cd, Cl, Co, Cr, Cu, F, Fe, Ga,
H, He, Hg, I, In, K, Kr, Li, Mg, Mn, N, Na, Ne, Ni, O, P, Pb, S, Sb, Se,
Si, Sn, Te, Ti, Tl, V, Xe, Zn
```

The seed already includes teaching facts such as `atomic_number`, `state`, `group_label`, `electron_configuration`, `common_valence`, `redox_tendency`, and `note`. The new physical fact fields should mainly follow the Royal Society of Chemistry Periodic Table fact boxes:

- RSC Periodic Table: `https://periodic-table.rsc.org/`
- Example element pages: `https://periodic-table.rsc.org/element/17/chlorine`, `https://periodic-table.rsc.org/element/26/iron`, etc.
- Fact-box fields of interest: atomic number, relative atomic mass, group, period, block, state at 20°C, density, and electron configuration.

## Goals / Non-Goals

**Goals:**

- Replace the static selected-element fact grid with a model-led, Chinese, mobile-first atom model card.
- Preserve the current element tile visual identity (`atomic number / symbol / English name`) as the card's selected-element lockup.
- Import the Zdog atom viewer as an internal student-web feature module.
- Support both `电子层模型` and `轨道模型` where electron-configuration data permits.
- Extend maintained profile element data with RSC-style fact-box fields and source metadata.
- Keep teaching-specific facts such as common valence and redox tendency as local instructional fields, not as RSC physical-fact fields.
- Verify phone viewport behavior, canvas rendering, element switching, mode switching, and no horizontal overflow.

**Non-Goals:**

- No iframe or micro-frontend embedding of the standalone `zdog` dev server.
- No runtime scraping of RSC pages.
- No full periodic-table database product or encyclopedia page in this change.
- No Three.js rewrite.
- No native mini-program, Taro, uni-app, or React Native package.
- No removal of family common properties, property summaries, experiment video view, or bottom-tab shell behavior.
- No requirement to make RSC the source for teaching simplifications such as common valence choices.

## Decisions

### 1. Integrate Zdog As An Internal Feature Module

Create a new student-web feature module:

```text
apps/student-web/src/features/atom-viewer/
├─ AtomViewerZdog.tsx
├─ AtomModeSegment.tsx
├─ OrbitalSpinDisplay.tsx
├─ orbitalOptions.ts
├─ learningAtomAdapter.ts
└─ LearningAtomModelCard.tsx
```

The implementation may adapt code from `C:\Users\38122\Documents\zdog`, but it must be owned by the student web frontend after import. This means:

- CSS class names must be namespaced for student H5 usage.
- Labels must be localized into Chinese.
- The visual style must match the existing student H5 green paper/card system.
- The component must receive current student learning data, not `testElements`.

Alternative considered: embed `http://127.0.0.1:5199/` or `http://222.200.189.249:5199/` in an iframe. Rejected because it would depend on a separate dev server, preserve the English/dark demo shell, complicate mobile sizing, and split state from the selected element chips.

### 2. Replace Only The Selected-Element Fact Area

The element-selection flow stays:

```text
Chapter context
→ facts / experiments switcher
→ within-family element chips
→ selected element model card
→ reference media
→ family common properties
→ property summaries
```

`LearningElementChips` remains the way students choose `Cl`, `Br`, `I`, etc. Selecting a chip updates the atom model card. The selected family/chapter and facts/experiments switcher do not change.

The old 2x3 fact grid is removed from the primary view. Its content is redistributed into:

- model card header: selected element tile and short selected-element identity.
- compact fact strip: RSC-style physical facts.
- teaching cue area: common valence and redox tendency.
- optional orbital panel when `轨道模型` is selected.

Alternative considered: append the atom viewer above or below the old fact grid. Rejected because it would make the facts view too long on phone and keep the weak static-card design.

### 3. Extend Profile Element Facts With Curated RSC Fields

Extend each relevant profile element record with optional fields such as:

```json
{
  "relative_atomic_mass": "35.45",
  "period": 3,
  "group": "17",
  "block": "p",
  "state_at_20c": "Gas",
  "density": "0.002898 g/cm3",
  "rsc_url": "https://periodic-table.rsc.org/element/17/chlorine",
  "fact_source": "RSC Periodic Table"
}
```

Naming can be finalized during implementation, but the contract should preserve these concepts:

- `atomic_number` and `electron_configuration` may continue using existing top-level fields.
- `group_label` remains the teaching/family label, such as `17 / 卤素`.
- `group`, `period`, and `block` are physical periodic-table facts.
- `state` may remain teaching-facing Chinese text; `state_at_20c` stores the RSC-style physical fact value.
- `density` and `relative_atomic_mass` should be strings to preserve units, uncertainty annotations, and ranges without numeric precision issues.
- `rsc_url` or equivalent source URL should be stored per element for auditability.

The first implementation should cover the 47 currently active learning symbols. If an element lacks a RSC field during migration, the UI must degrade gracefully, but validation should make missing required first-scope fields visible to maintainers.

Alternative considered: derive all facts from `periodic.ts` plus electron configuration. Rejected because `periodic.ts` does not include mass, density, RSC state-at-20°C, or source URLs.

### 4. Keep RSC Physical Facts Separate From Teaching Simplifications

RSC fact boxes are used for stable physical facts. Teaching simplifications remain in the existing profile seed:

- common valence,
- redox tendency,
- note,
- family common-property summaries,
- property sections,
- experiment focus.

This separation matters because common valence values are curriculum- and context-sensitive. The UI can show both, but it should not imply RSC authored the simplified teaching valence sequence.

### 5. Use A Student-Specific Adapter Instead Of Demo `testElements`

Add an adapter that maps:

```text
StudentLearningElementBadge
+ periodic metadata
+ RSC fact fields
→ AtomViewerElement
```

The viewer element should include:

- `symbol`,
- Chinese name,
- English name,
- atomic number,
- electron configuration,
- shells for Bohr rendering,
- block/group/period,
- accent color from existing periodic-table area colors,
- optional compact fact strings.

The adapter should derive Bohr `shells` from electron configuration rather than relying on prototype test data. A practical derivation strategy:

- Expand noble-gas cores with a small map such as `[He] -> [2]`, `[Ne] -> [2, 8]`, `[Ar] -> [2, 8, 8]`, `[Kr] -> [2, 8, 18, 8]`, `[Xe] -> [2, 8, 18, 18, 8]`.
- Parse explicit subshell tokens with `/(\d+)([spdf])(\d+)/g`.
- Sum electrons by principal quantum number.
- If parsing fails, fall back to a simple shell distribution from atomic number or render a clear unavailable state.

The orbital mode can continue using the prototype's valence-subshell parsing, adapted to the student element model.

### 6. Localize The Viewer Into The Student H5 Visual System

The card should not use the standalone prototype's dark app shell. The target visual language:

- cream/white card surface matching current learning panels,
- green element tile lockup retained,
- atom canvas on a contained visual stage with subtle green/blue/gold accents,
- 8px card radius unless an existing token requires otherwise,
- Chinese labels such as `电子层`, `轨道`, `重置视角`, `暂停`, `播放`,
- compact scientific notation preserved where useful,
- no decorative marketing hero or unrelated explanatory text.

Suggested card layout:

```text
┌──────────────────────────────┐
│ [17 Cl Chlorine]  当前元素模型 │
│ 氯 · 第3周期 · p区 · 17族       │
├──────────────────────────────┤
│        Zdog atom canvas       │
│        drag to rotate         │
├───────────┬──────────────────┤
│ 电子层    │ 轨道              │
├──────────────────────────────┤
│ 质量 / 密度 / 状态 / 电子排布   │
│ 常见化合价 / 氧化还原提示       │
└──────────────────────────────┘
```

On narrow phone widths, the fact strip should be compact and wrap safely. It must not recreate six large cards.

### 7. Animation And Touch Performance Rules

The imported viewer must preserve the prototype's practical performance controls:

- use `requestAnimationFrame`,
- stop animation when paused or when `document.hidden`,
- use `ResizeObserver` to size the canvas,
- support pointer drag with `touch-action: none` only on the canvas,
- clean up animation frames and observers on unmount,
- rerender when selected element, mode, reset signal, or orbital choice changes.

Additional student H5 constraints:

- default to auto-play if performance is acceptable, but provide an obvious pause control.
- avoid blocking page vertical scroll outside the canvas.
- respect bottom navigation spacing and facts/experiments switcher behavior.
- ensure the canvas is nonblank after route changes, tab switches, and element switches.

### 8. Verification Scope

Implementation should verify:

- TypeScript typecheck.
- Student web build.
- Student e2e tests updated for the new atom model card.
- Mobile viewport QA at 360x780, 390x844, and 430x932.
- Canvas exists, has a nonzero rendered size, and is not fully blank where automation can reasonably test it.
- Selecting another element updates the tile and viewer.
- Switching `电子层` / `轨道` keeps the card within phone width.
- Missing optional RSC facts do not crash the page.
- OpenSpec validation passes for this change.

## Risks / Trade-offs

- RSC data collection is manual and can be inconsistent across 47 elements -> store per-element source URLs, validate required fields, and keep physical facts separate from teaching fields.
- Electron-configuration parsing can fail for edge cases such as irregular d/f configurations -> parse explicit configuration first, keep core expansion maps, and provide fallback/unavailable states.
- Canvas rendering can become blank after resize or tab switches -> add QA checks for nonzero canvas dimensions and run manual browser verification if automation cannot inspect pixels reliably.
- Zdog dependency increases bundle size -> acceptable for a learning visualization; monitor build output and avoid importing the standalone demo shell.
- Orbital mode can be visually dense on mobile -> default to `电子层`, keep orbital controls compact, and allow progressive disclosure.
- The atom model may push experiment tasks lower -> remove the old 2x3 fact grid and keep compact facts to preserve discoverability.
- RSC fact wording is English while student UI is Chinese -> translate labels and selected display values where appropriate, but retain source URL and scientific notation.

## Migration Plan

1. Add `zdog` dependency and student atom-viewer feature module.
2. Extend frontend and backend element fact types with optional RSC-style fields.
3. Expand `data/seed/student_learning/element_profiles.json` for the 47 active profile symbols using curated RSC fact-box data.
4. Add validation for the new first-scope physical fact fields and source URLs.
5. Replace `LearningSelectedElementFacts` with `LearningAtomModelCard`.
6. Restyle the selected-element area as a Chinese student H5 card.
7. Update e2e and mobile QA expectations.
8. Run typecheck, build, e2e, mobile QA, and OpenSpec validation.

Rollback is frontend-safe: the feature can be reverted to the old selected-element fact panel while leaving optional new seed fields harmless. Backend schema additions should be backward compatible because the new fields are optional.

## Open Questions

- Should the first implementation require all 47 active profile symbols to have complete RSC fact-box data before merge, or allow a smaller first batch with validation warnings? Default recommendation: cover all 47 because the current profile scope is finite and known.
- Should `state_at_20c` values be stored in English as RSC display values, translated Chinese, or both? Default recommendation: store the RSC value plus show Chinese labels/translation in UI where straightforward.
- Should the orbital mode be visible for all elements with parseable electron configuration, or hidden behind a compact disclosure for heavier d/f elements? Default recommendation: visible as a mode tab, with compact orbital controls.
- Should source attribution be visible in the UI or only stored in data? Default recommendation: show a small `数据参考 RSC` link inside the card detail/footer, not in the primary header.
