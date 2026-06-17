## 1. Entry Flow And Current Context

- [x] 1.1 Trace the current student H5 learning entry from login/pretest fallback into `LearningSurface` and document how a selected `profile_id` or default profile is resolved.
- [x] 1.2 Decide the concrete route/state contract for periodic-table entry to chapter page handoff, using `profile_id`, `chapter_id`, or family number consistently.
- [x] 1.3 Replace page-level sibling-family primary tabs with current-family identity plus a secondary return/switch-chapter affordance.
- [x] 1.4 Ensure default or recommended profiles render as one current chapter page rather than a browse-all-families surface.

## 2. Seed And API Contract

- [x] 2.1 Extend `data/seed/student_learning/element_profiles.json` so each element can provide selected-element facts: atomic number, electron configuration, group/family, common valence, elemental state, oxidizing/reducing tendency, and optional note.
- [x] 2.2 Separate family-wide common properties or trend summaries from selected-element facts in the seed shape while preserving existing fields during migration.
- [x] 2.3 Add optional reference media metadata to the seed or a manifest with source URL, license, attribution, usage scope, alt text, and optional local path.
- [x] 2.4 Update student learning schema types in backend and frontend to expose current family context, selectable elements, selected-element facts, family common properties, property sections, and optional reference media.
- [x] 2.5 Update production resource validation so required student learning profile fields and new element fact fields are checked without requiring optional media.

## 3. Chapter Page Composition

- [x] 3.1 Recompose the H5 current chapter page into: current family header, element chips, selected-element facts, family common properties, property selector, related experiment-point groups, and completion action.
- [x] 3.2 Make element chips touch-friendly and update selected-element facts without changing the active family/chapter.
- [x] 3.3 Render family common properties as compact chapter-level context and connect each relevant property to experiment-point groups.
- [x] 3.4 Keep the experiment-point area discoverable on 360px, 390px, and 430px phone widths using compact summaries or progressive disclosure for long facts.
- [x] 3.5 Preserve AI chat and feedback floating entries under existing admin feature switches without overlapping primary learning actions.

## 4. Experiment Points, Detail, And Assessment

- [x] 4.1 Ensure experiment-point cards include point title, parent experiment context, concise reaction or summary when available, media availability, and question count.
- [x] 4.2 Ensure selecting a point opens the existing point detail route with profile, property, experiment, and point context preserved.
- [x] 4.3 Keep point detail video-first but video-optional, with graceful empty media state and compact explanation context.
- [x] 4.4 Preserve existing learning event recording, AI point context, feedback context, and completion-to-posttest behavior.
- [x] 4.5 Confirm completing learning from the chapter page or point detail starts the existing post-learning assessment flow.

## 5. Reference Media Governance

- [x] 5.1 Identify candidate public reference media sources only when they have clear source URLs and licensing suitable for the intended use.
- [x] 5.2 Render reference media as optional contextual illustration, never as protected experiment video or manually reviewed point evidence.
- [x] 5.3 Provide empty or fallback visual states when optional reference media is absent, unavailable, or intentionally disabled.

## 6. Verification

- [x] 6.1 Run backend tests or targeted validation covering the updated student learning payload and profile validation.
- [x] 6.2 Run `npm run typecheck` for `apps/student-web`.
- [x] 6.3 Run `npm run build` for `apps/student-web`.
- [x] 6.4 Run mobile viewport QA for 360x780, 390x844, and 430x932 CSS pixels covering the chapter page, element switching, point list, point detail, AI entry, feedback entry, and assessment handoff.
- [x] 6.5 Run `openspec validate student-element-chapter-learning-composition --strict`.
- [x] 6.6 Record final verification notes, including any remaining manual phone/WebView risks.
