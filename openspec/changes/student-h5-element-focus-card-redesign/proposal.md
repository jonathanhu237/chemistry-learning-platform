## Why

The current selected-element card on the student H5 chapter page reads like a generated sentence that mixes an individual element heading with family-level trend text. This makes the top chemistry context feel dry and semantically awkward, especially when the card should help students quickly understand the current observation target before they enter detailed element facts or experiment videos.

This change redesigns the element card as a compact, experiment-learning card: keep the recognizable periodic-table element tile, foreground one curated focus property, and explain why that element matters to the current chapter's experiments.

## What Changes

- Replace dynamic selected-element card copy such as `<element> in <family>` plus family trend text with curated card-level fields.
- Keep the small periodic-table element tile as the card's visual anchor, including atomic number, symbol, and English label.
- Add a prominent focus-property area that states the selected element's most important chapter-relevant property in one short line.
- Add an experiment relevance line explaining why the element matters for the current chapter's experiment videos or observation tasks.
- Keep detailed facts, full trend explanations, and longer chemical descriptions in the element detail or facts sections rather than the compact card.
- Preserve within-family element selection behavior and the existing route/page structure.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-experience`: Define the selected-element card as a compact experiment-learning summary with curated focus property and experiment relevance copy.
- `student-h5-mobile-design-system`: Define the phone layout rules for the redesigned element card so it remains compact, readable, and does not push experiment tasks too far down the page.

## Impact

- Student learning profile seed data will need new card-level copy fields for each enabled element, separate from detailed notes and family trend summaries.
- Student learning payload schemas and backend mapping may need to expose the new card-level fields while keeping backward compatibility for existing detail fields.
- Student H5 learning page components and styles will need to render the redesigned card and remove brittle title/body sentence composition.
- Tests and validation should cover seed completeness, graceful fallback, element switching, mobile viewport fit, and that detailed facts remain available outside the compact card.
