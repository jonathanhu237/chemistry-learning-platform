## Context

The student H5 app now treats AI as a primary root destination and contextual learning assistant. In `apps/web-student`, AI entry points currently use a mixture of chat bubbles, bot icons, and sparkle icons, while the Atom icon also appears in non-AI chemistry contexts such as element search and experiment principle sections.

The change is intentionally visual and student-web scoped. Teacher and admin consoles have their own AI affordances and should keep their existing icon vocabulary.

## Goals / Non-Goals

**Goals:**
- Make Atom the consistent student H5 AI identity across AI root, contextual AI actions, assistant states, and AI-related empty states.
- Make `Atom 学习助手` the student-web-only product name for the assistant, while teacher/admin surfaces keep their existing AI naming.
- Replace student-web `问 AI` / `问AI` ask-entry copy with `问问Atom`.
- Move non-AI student-web uses of the Atom pictogram to clearer alternatives so Atom does not mean both "element" and "AI" in visible affordances.
- Keep search controls recognizable with Search and experiment/chemistry content recognizable with `FlaskConical` or existing non-AI content icons.
- Preserve behavior, routes, API payloads, permissions, and layout structure.

**Non-Goals:**
- Do not change teacher or admin AI iconography.
- Do not introduce a custom SVG/icon asset or a new icon dependency.
- Do not rename AI routes, assistant contexts, or backend feature flags.
- Do not redesign the AI root beyond icon substitution and any spacing needed to keep existing layout stable.

## Decisions

1. Use Lucide `Atom` as the student AI identity icon.
   - Rationale: it already belongs to the installed icon set, visually fits chemistry, and can become a compact program identity mark without new assets.
   - Alternative considered: keep `MessageCircle` for AI because it reads as chat. This keeps generic chat semantics but does not create a distinctive chemistry-course AI mark.

2. Replace element-search Atom with Search.
   - Rationale: the control is an input/search affordance first. Once Atom represents AI, Search avoids implying the element box is AI-powered.
   - Alternative considered: use `FlaskConical`. This reads as experiment content rather than element lookup.

3. Replace non-AI Atom section/empty-state icons in student-web with chemistry or search alternatives.
   - Rationale: after the identity shift, visible Atom pictograms outside AI would dilute the rule.
   - Alternative considered: allow Atom to keep a dual meaning for atoms and AI. This is lower-effort but creates avoidable ambiguity in a phone UI.

4. Keep teacher/admin unchanged.
   - Rationale: their AI surfaces are operational tools with different visual conventions; this change is about student-facing product identity only.

5. Use Atom naming only in `apps/web-student`.
   - Rationale: the student app needs a friendly branded assistant, but teacher/admin settings and analytics still describe the general AI capability.
   - Alternative considered: rename every app-wide AI label to Atom. This would overreach the student-facing scope and change operational console copy.

## Risks / Trade-offs

- [Risk] Atom no longer visually signals literal atom/element in some student-web empty states. → Mitigation: keep full atom model content and labels unchanged; only replace small pictogram affordances where an alternate icon is sufficient.
- [Risk] Existing tests assert generic AI icon absence/presence indirectly. → Mitigation: update focused student-web tests for the icon identity without changing route or behavior assertions.
- [Risk] Internal route, context, or feature-flag names still contain "AI". → Mitigation: treat this change as student-facing copy only; keep technical identifiers stable.
- [Risk] Existing uncommitted AI root visual work is in progress. → Mitigation: limit edits to imports and JSX icon replacements; avoid restructuring AI root layout or CSS.
