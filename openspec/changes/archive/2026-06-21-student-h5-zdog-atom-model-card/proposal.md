## Why

The current student H5 facts view treats the selected element as a set of static database-like fact cards; the only satisfying part is the compact periodic-table element tile such as `17 / Cl / Chlorine`. This misses the opportunity to make the phone learning page feel visual, tactile, and chemistry-specific after the student selects an element.

We already have a working React + Zdog atom viewer prototype in `C:\Users\38122\Documents\zdog` at commit `e665060 Finalize Zdog atom viewer prototype`, and the prototype has been verified on phone hardware as smooth enough for this use case. This change absorbs that prototype into the student H5 as a Chinese, mobile-first atom model card backed by maintained element fact data rather than embedding the standalone English demo.

## What Changes

- Replace the selected-element fact-card block in the learning facts view with a Chinese atom model card.
- Preserve the existing element tile visual identity (`atomic number / symbol / English name`) as the lockup for the selected element.
- Import the Zdog-based Bohr and orbital visualization engine into the student web frontend as an internal feature module instead of iframe/micro-frontend embedding the standalone prototype server.
- Add a student-web adapter that converts `StudentLearningElementBadge` plus periodic-table metadata into the atom viewer's element model.
- Extend maintained student learning profile element facts with RSC-style fact-box fields: relative atomic mass, group, period, block, 20°C state, density, electron configuration, and source URL/attribution metadata.
- Keep teaching-specific simplified fields such as common valence and redox tendency in the profile seed, separate from RSC physical facts.
- Localize controls and labels into Chinese while keeping compact scientific notation such as `3p5`, `d`, `g/cm3`, and element symbols.
- Add mobile QA coverage for the atom canvas, mode switching, element switching, and no-overflow behavior at common phone widths.
- Do not add a native mini-program rewrite, a Three.js replacement, or automatic data scraping at runtime.
- **BREAKING (UI):** the previous 2x3 selected-element fact grid is removed from the primary facts view and replaced by the atom model card with compact facts.

## Capabilities

### New Capabilities
- `student-h5-atom-model-card`: Defines the selected-element atom model card, Zdog integration, profile-to-viewer data adaptation, RSC-backed fact fields, localized controls, and mobile interaction contract.

### Modified Capabilities
- `student-h5-learning-experience`: Updates selected-element facts behavior from static fact cards to a model-led element facts area while preserving within-family element selection semantics.
- `student-h5-mobile-design-system`: Adds mobile interaction, safe layout, canvas, touch, and animation constraints for an embedded atom model card inside the phone-first H5 shell.

## Impact

- `apps/student-web/package.json`: add `zdog` and its type dependency if needed by TypeScript.
- `apps/student-web/src/features/atom-viewer/`: new internal feature module adapted from `C:\Users\38122\Documents\zdog`.
- `apps/student-web/src/features/learning/LearningFactsView.tsx`: replace `LearningSelectedElementFacts` with a model-led selected element panel.
- `apps/student-web/src/features/periodic-table/periodicHelpers.ts` and `apps/student-web/src/periodic.ts`: reuse or extend periodic metadata for group, period, block, area color, English names, and atom viewer adapter inputs.
- `apps/student-web/src/styles/learning.css` or a dedicated atom-viewer stylesheet: replace large fact-card grid styling with responsive atom model card styling aligned to the student H5 green paper visual system.
- `apps/student-web/src/api.ts`, `server/app/student_learning_schemas.py`, and `server/app/services/student_learning_service.py`: expose optional new RSC-style element fact fields from the maintained profile seed.
- `data/seed/student_learning/element_profiles.json`: expand element facts for the 47 currently covered learning symbols (`Ag, Al, Ar, As, At, B, Ba, Bi, Br, C, Ca, Cd, Cl, Co, Cr, Cu, F, Fe, Ga, H, He, Hg, I, In, K, Kr, Li, Mg, Mn, N, Na, Ne, Ni, O, P, Pb, S, Sb, Se, Si, Sn, Te, Ti, Tl, V, Xe, Zn`) using RSC Periodic Table fact boxes as the primary reference for physical facts.
- `apps/student-web/src/App.e2e.test.tsx` and `apps/student-web/scripts/mobile-viewport-qa.mjs`: update expectations from `.element-fact-grid` style facts to atom model card, canvas, and compact fact checks.
- OpenSpec specs: add a new atom model card capability and update existing student H5 learning/mobile contracts.
