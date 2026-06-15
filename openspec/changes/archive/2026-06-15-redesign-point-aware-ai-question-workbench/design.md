## Context

The current question-bank page has the right data foundation but the wrong repair shape. A teacher can inspect a point-aware question in a detail modal, then open a separate AI suggestion drawer that no longer keeps the original item, point evidence, option diagnostics, or repair history in focus. The result is a one-shot generation form instead of a question-authoring workflow.

Research notes from modern assessment tools point to a different pattern:

- Canvas New Quizzes item banks emphasize searchable/filterable banks, item details, metadata/tags, item-type filtering, and controlled edits to bank items.
- Moodle question banks provide a dedicated create/preview/edit space, category organization, ready/draft status, question versions/history, comments, usage, and filters.
- TAO authoring keeps an item library, item authoring actions, preview, and review submission in the same authoring flow.
- Kahoot AI generation and Mentimeter AI quiz creation generate from source material, then require review/customization before saving; Mentimeter explicitly supports editing through chat or the standard editor.
- Professional item review workflows treat item authoring as only the first step and require documented review states before release.

For this product, those patterns translate into one integrated workbench: original question context on one side, multi-turn AI repair conversation on the other, and generated candidate versions with validation and publish controls in the same surface.

## Goals / Non-Goals

**Goals:**

- Make the original question and its point-aware evidence visible throughout repair.
- Support multi-turn teacher prompts for a single repair session instead of one detached generation attempt.
- Persist repair/create sessions so teachers can close and reopen work without losing chat history or generated candidates.
- Compare generated candidates against the original question before adoption.
- Reuse the existing draft/publish validation policy so AI never mutates the live bank without teacher confirmation.
- Keep AI-created and AI-repaired questions objective, deterministic, metadata-preserving, and auditable.

**Non-Goals:**

- Do not introduce AI semantic grading for student answers.
- Do not automatically replace published default-bank questions when an AI candidate is generated.
- Do not implement full collaborative reviewer assignment in this change.
- Do not redesign unrelated admin navigation, class analytics, or experiment management pages.
- Do not remove the point-aware question-bank data model already imported into the default bank.

## Decisions

### Decision: Replace the detached drawer with a focused workbench surface

The UI will open an "AI question workbench" from question detail or selected experiment/point context. For repair, the workbench will keep an original-question panel visible with stem, options, answer, explanation, point keys, source audit, source references, option diagnostics, status, and lineage. The adjacent AI panel will contain chat history, prompt composer, context chips, generated candidate cards, validation results, and publish/reject actions.

Alternative considered: keep the current side drawer and add a small original-question summary at the top. That would reduce code churn but still forces teachers to repair from an overloaded drawer nested over the detail modal, and it does not solve comparison or multi-turn continuity.

### Decision: Model AI assistance as sessions, turns, and candidates

The backend will persist AI assistance as a session with a mode (`repair` or `create`), experiment id, optional point key, optional original question id, immutable original-question snapshot for repair, chat turns, and generated candidates. Each candidate links to the turn that produced it and carries validation status, draft id when stored, rejection/publish state, and generation lineage.

Alternative considered: reuse the existing generation endpoint as a stateless "generate suggestions" call. That works for a single draft list but cannot support reopening, multi-turn context, or precise audit from teacher prompt to accepted candidate.

### Decision: Build server-side context from canonical question-bank data

For repair sessions, the server will assemble context from the current question record, metadata, source audit, option diagnostic links, and selected experiment point. The frontend may display this context, but it will not be trusted as the only source for AI grounding. For create sessions, the same context builder will use selected experiment/point coverage and source evidence instead of an original question.

Alternative considered: send the full visible detail payload from the browser to the LLM. That is easier, but it risks stale context, missing metadata, or client-side tampering.

### Decision: Keep candidates as drafts until explicitly published

Generated candidates will remain reviewable drafts or draft-like candidate records. A teacher can ask follow-up prompts, regenerate, reject a candidate, accept a candidate for later review, or publish it only after validation passes. Repair publication records the relationship to the original question but does not silently mutate the original without an explicit replace/disable policy.

Alternative considered: let "publish" directly overwrite the original question. That is simpler for teachers in the moment, but it makes rollback, analytics continuity, and source audit harder.

### Decision: Use deterministic validation as the publication gate

Before a candidate can be published, validation will check objective type, answer shape, accepted fill-blank answers, point bindings, source audit, option diagnostic links for single-choice items where applicable, and lineage back to session/turn/original question. Validation failures remain visible in the workbench with actionable messages.

Alternative considered: rely on the model to self-report "can publish". That is not sufficient for a student-facing bank.

## Risks / Trade-offs

- [Risk] Session persistence adds data model and API complexity -> Mitigation: keep the first implementation narrow with repair/create session CRUD, turns, candidates, and existing draft publication; defer reviewer assignment and kanban-style workflows.
- [Risk] The workbench may become visually dense -> Mitigation: use stable split panes, compact metadata chips, collapsible evidence sections, and candidate cards with diff/readiness summaries.
- [Risk] Multi-turn prompts can drift away from source evidence -> Mitigation: every turn includes the server-built context snapshot or a compact session memory, and every candidate must pass the same validation gate.
- [Risk] Teachers may publish an inferior AI candidate because it looks polished -> Mitigation: show original-vs-candidate comparison, source/evidence readiness, and explicit responsibility/confirmation before publication.
- [Risk] Existing one-shot AI endpoint may still be used by older UI paths -> Mitigation: route new UI through session APIs while keeping the old endpoint only as a compatibility wrapper or removing it after migration.

## Migration Plan

1. Add session/candidate persistence and APIs without removing the existing suggestion endpoint.
2. Implement the workbench behind the existing AI repair/create entry points on the question-bank page.
3. Route repair actions from question detail into the workbench and show original context in the workbench, not hidden behind the modal backdrop.
4. Route add-question generation for selected experiment/point through create-mode sessions.
5. Keep old generated drafts readable and publishable, but new generation attempts should create session-linked candidates.
6. After verification, de-emphasize or remove the detached drawer entry point.

## Open Questions

- Should repair publication create a new published question and disable the original, or should it support an explicit "replace original" action with version history?
- How much chat history should be sent to the model for long sessions: full turns, summarized memory, or last N turns plus immutable context?
- Should accepted-but-unpublished candidates appear in the main draft list, a session-only queue, or both?
