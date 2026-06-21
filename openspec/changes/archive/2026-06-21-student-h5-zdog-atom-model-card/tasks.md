## 1. Data Contract And RSC Fact Seed

- [x] 1.1 Confirm final optional field names for RSC-style physical facts on student learning elements: relative atomic mass, group, period, block, 20°C state, density, source URL, and source attribution.
- [x] 1.2 Update backend Pydantic schemas and student learning service mapping so optional physical fact fields can flow from the profile seed to the student learning page payload.
- [x] 1.3 Update frontend `StudentLearningElementBadge` types to include the optional physical fact fields without breaking existing learning payload consumers.
- [x] 1.4 Expand `data/seed/student_learning/element_profiles.json` for the 47 active profile symbols (`Ag, Al, Ar, As, At, B, Ba, Bi, Br, C, Ca, Cd, Cl, Co, Cr, Cu, F, Fe, Ga, H, He, Hg, I, In, K, Kr, Li, Mg, Mn, N, Na, Ne, Ni, O, P, Pb, S, Sb, Se, Si, Sn, Te, Ti, Tl, V, Xe, Zn`) using curated RSC Periodic Table fact-box data.
- [x] 1.5 Keep teaching fields such as common valence, redox tendency, and notes separate from RSC physical fact fields in the seed and API types.
- [x] 1.6 Add or update resource validation tests so active profile elements report missing first-scope physical fact fields and source URLs.

## 2. Atom Viewer Feature Module

- [x] 2.1 Add `zdog` and TypeScript support dependencies to `apps/student-web` as needed.
- [x] 2.2 Create `apps/student-web/src/features/atom-viewer/` and import/adapt the Zdog prototype viewer code from `C:\Users\38122\Documents\zdog` commit `e665060`.
- [x] 2.3 Remove prototype-only app shell, English demo header, test element picker, and demo fact strip from the imported student feature code.
- [x] 2.4 Localize viewer controls and labels into Chinese, including electron-layer/orbital mode, reset, play, pause, drag hint, and orbital/spin headings.
- [x] 2.5 Implement the student `learningAtomAdapter` that maps `StudentLearningElementBadge`, periodic metadata, English element name mapping, area colors, and RSC facts into the viewer element model.
- [x] 2.6 Implement robust shell derivation from electron configuration, including noble-gas core expansion and explicit subshell parsing for common p/d/f profile elements.
- [x] 2.7 Preserve animation lifecycle controls: requestAnimationFrame loop, pause/play, visibility handling, ResizeObserver sizing, pointer drag, and cleanup on unmount.
- [x] 2.8 Add graceful unavailable states for missing or unparsable model data.

## 3. Learning Facts UI Integration

- [x] 3.1 Create `LearningAtomModelCard` or equivalent selected-element card component that combines the existing element tile identity, Zdog canvas, localized controls, compact facts, and teaching cues.
- [x] 3.2 Replace `LearningSelectedElementFacts` in `LearningFactsView` with the new atom model card while preserving `LearningElementChips` and selected element state.
- [x] 3.3 Ensure selecting another element chip updates the atom model card without changing current profile, selected property section, facts/experiments switcher state, or experiment groups.
- [x] 3.4 Restyle the selected-element area to match the student H5 green paper/card system rather than the standalone dark Zdog demo.
- [x] 3.5 Replace the old 2x3 fact grid with compact physical fact strips/chips plus a compact teaching cue area for common valence and redox tendency.
- [x] 3.6 Add a compact RSC source note or link where appropriate without making the primary card read like a citation block.
- [x] 3.7 Verify the atom model card remains compact enough that family common properties and experiment learning content remain discoverable on phone viewports.

## 4. Tests And Mobile QA

- [x] 4.1 Add unit or focused frontend tests for the atom adapter, including noble-gas shorthand, explicit p/d configurations, and fallback behavior.
- [x] 4.2 Update `apps/student-web/src/App.e2e.test.tsx` to expect the atom model card instead of the old selected-element fact grid.
- [x] 4.3 Update `apps/student-web/scripts/mobile-viewport-qa.mjs` to check atom model card visibility, element chip switching, mode control reachability, nonzero canvas dimensions, and no horizontal overflow.
- [x] 4.4 Verify the facts/experiments switcher, bottom navigation, assistant tab handoff, profile feedback flow, experiment point detail, and assessment handoff still pass after the atom card integration.
- [x] 4.5 Run `npm run typecheck --prefix apps/student-web`.
- [x] 4.6 Run `npm run test:e2e --prefix apps/student-web`.
- [x] 4.7 Run `npm run build --prefix apps/student-web`.
- [x] 4.8 Run mobile viewport QA for 360x780, 390x844, and 430x932 CSS-pixel viewports.
- [x] 4.9 Run `openspec validate student-h5-zdog-atom-model-card --strict`.
- [x] 4.10 Run `git diff --check`.

## 5. Review And Rollback Readiness

- [x] 5.1 Record final verification evidence, including any manual phone/WebView check needed for canvas rendering.
- [x] 5.2 Confirm the implementation does not iframe or depend on the standalone Zdog prototype dev server.
- [x] 5.3 Confirm optional new seed/API fields are backward compatible and the old selected-element panel can be restored by reverting frontend integration if needed.
