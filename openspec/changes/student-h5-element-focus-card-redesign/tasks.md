## 1. Seed Data and Content Model

- [x] 1.1 Add card-level element fields to the student learning element model: `card_focus`, `card_relevance`, and `card_tags`.
- [x] 1.2 Update student learning profile validation so enabled redesigned-card profiles report missing card-level focus copy, experiment relevance copy, or compact tags.
- [x] 1.3 Author curated card copy for all enabled profile elements, starting with the halogen profile and then covering the remaining active profiles.
- [x] 1.4 Keep family trend text, detailed element notes, and reference facts separate from compact card copy.
- [x] 1.5 Add content-review guidance or inline seed comments that define the intended length and role of `card_focus`, `card_relevance`, and `card_tags`.

## 2. Backend Payload

- [x] 2.1 Extend student learning response schemas/types to expose the new card-level element fields.
- [x] 2.2 Map `card_focus`, `card_relevance`, and `card_tags` from `element_profiles.json` into each element badge payload.
- [x] 2.3 Preserve existing detailed fields such as electron configuration, common valence, redox tendency, physical facts, `note`, and reference URL for facts/detail surfaces.
- [x] 2.4 Add or update backend tests for profile validation, payload mapping, and graceful handling of temporarily missing card fields during migration.

## 3. Student H5 Frontend

- [x] 3.1 Update student-web API types to include the new selected-element card fields.
- [x] 3.2 Redesign the selected-element summary component to render the existing periodic-table tile, focus-property line, experiment-relevance line, compact tags, and detail action.
- [x] 3.3 Remove the old compact-card heading/body composition that generated prose from selected element name, family name, or family trend notes.
- [x] 3.4 Implement fallback rendering that uses stable factual tags without recreating the old generated prose pattern.
- [x] 3.5 Ensure element chip selection updates the redesigned card without changing the current family/chapter context or facts/experiments switcher state.
- [x] 3.6 Ensure full element facts and family trend explanations remain available in the facts/detail area rather than expanding the compact card by default.

## 4. Mobile Layout and Visual QA

- [x] 4.1 Update mobile styles so the element tile remains visible and unclipped beside the focus/relevance content at 360px to 430px widths.
- [x] 4.2 Constrain long focus, relevance, tag, and detail-action labels so they wrap or clamp without overlapping nearby content.
- [x] 4.3 Keep the redesigned card compact enough that the first experiment-point task area remains discoverable on phone viewports.
- [x] 4.4 Verify touch reachability for element chips, the detail action, facts/experiments switcher, point cards, AI entry, feedback entry, and completion action.
- [x] 4.5 Run mobile viewport QA at 360x780, 390x844, and 430x932 CSS pixels covering element switching, long Chinese copy, tag wrapping, and experiment-point visibility.

## 5. Verification

- [x] 5.1 Run targeted backend validation/tests for student learning seed data and payload mapping.
- [x] 5.2 Run targeted student-web typecheck/build/tests for the learning page card redesign.
- [x] 5.3 Run `openspec validate student-h5-element-focus-card-redesign --strict`.
- [x] 5.4 Record final verification notes, including commands run, viewport sizes checked, and any remaining mobile/WebView risks.
