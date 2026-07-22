# Unify legacy and main product applications

## Goal

End the long-running `main` / `legacy` split and deliver one canonical five-tab student H5 plus one canonical teacher console on `main`. The result is a deliberate product and code reconciliation: retain useful fixes and proven flows from `legacy`, retain valuable platform and AI/RAG work from `main`, and remove features that no longer serve the product instead of preserving duplicate applications or accumulating every historical feature.

## Background

- The student application is a mobile H5 application, not a native WeChat Mini Program.
- The canonical navigation remains five tabs: Home, Learn, Atom, Assessment, and Profile.
- `main` and `legacy` diverged at `3096f82`; at planning time `main` has 11 unique commits and `legacy` has 117 unique commits.
- `main/apps/web-student` is a separate modern rewrite. The latest `legacy/apps/web-student` is the old competition application plus later fixes and product refinements. `main/apps/web-student-old` is only a pre-refinement snapshot and is not the latest legacy baseline.
- Existing documentation describes a video-discovery-centered product. The user has confirmed that the Home video feed remains part of the product, while some surrounding collaborator-built video-library capabilities remain candidates for deletion or simplification.
- The accepted visual direction is the current collaborator-built modern green student H5. Legacy is a source of behavior and fixes, not a request to restore the red competition visual style.
- The current teacher console is a modular twelve-route product that already includes resources, online textbooks, classes, catalog editing, video processing, an evidence-aware question workbench, analytics, feedback, a learning assistant, student preview, settings, and monitoring. Latest `legacy` is a narrower seven-route monolith. Teacher reconciliation therefore starts from the current console and ports only approved legacy behavior; it does not replace the current console with the old red application.
- The user has decided that the standalone platform-administrator operations frontend may be removed. Its account-management and operational responsibilities must be explicitly migrated or deleted before removing the runtime; they must not disappear accidentally as a side effect of deleting `apps/web-admin`.
- `main` contains the current online textbook ingestion, configurable OCR/embedding/rerank, publication, and textbook RAG work. That work must survive the reconciliation.
- The worktree already contains an unrelated user-owned modification at `artifacts/catalog_outline_seed_validation_report.json`; this task must not overwrite or stage it accidentally.

## Requirements

- **R1 — Join branch history:** integrate `legacy` into `main` with ancestry preserved, rather than leaving two permanently divergent product branches or representing the work only as unrelated cherry-picks.
- **R2 — One student H5:** finish with one canonical student runtime at `apps/web-student`; do not leave current and legacy student applications as competing implementations.
- **R2a — One teacher console:** finish with the current modular teacher console as the canonical teacher runtime. Do not retain the legacy monolith or an optional old teacher service after approved behavior has been ported and verified.
- **R3 — Product triage before conflict resolution:** classify overlapping capabilities as Keep, Rework, or Delete before resolving the student H5 merge. Git conflict choices must follow that product matrix.
- **R4 — Five-tab information architecture:** preserve Home, Learn, Atom, Assessment, and Profile as the root structure even when responsibilities and content within a tab change.
- **R4a — Retain Home video feed:** Home continues to provide an experiment-video discovery feed. Reconciliation may change its interaction model and remove nonessential surrounding features, but must not delete the feed itself.
- **R4b — Simplify video discovery:** retain the modern Home feed, main-viewport muted preview, paginated loading, focused search, recommendation marking, and navigation into the owning learning point. Remove the separate video-library surface, excessive phenomenon topic rail, watch-later system, and social-style or fake Home actions such as like/not-interested/share/feedback controls.
- **R4c — One Home feed/search owner:** serve default Home discovery and focused video search from the same canonical published catalog/video read model and API, with deterministic recommendation-first ordering and a cursor bound to the normalized query. Explicit teacher recommendations are authored from the current teacher catalog workflow and shown as recommendations; ordinary catalog items must not be mislabeled as recommended. Retire the student video-library Elasticsearch projection, index state, route, configuration, scripts, and operational contract. This does not remove Elasticsearch from textbook RAG or the separate teacher catalog-authoring search.
- **R5 — Selective legacy inheritance:** port useful legacy bug fixes, edge-case handling, and validated learning/assessment behavior where the corresponding product capability remains in scope. Legacy behavior is evidence, not an obligation to retain every legacy feature.
- **R5a — Assessment baseline:** use the latest legacy smart-baseline and assessment behavior as the functional baseline, rendered in the current modern visual system. Remove the separate current two-stage pretest gate so first-time students do not complete two overlapping baseline mechanisms.
- **R5b — Hierarchical custom assessment:** use latest legacy's final assessment setup: smart assessment plus an optional searchable chapter → directory → point scope tree. A custom assessment expands selected published scope nodes to usable leaf points and supports the configured 1/2/3 questions per point. Do not restore the removed random-practice or all-range entry modes.
- **R6 — Main platform preservation:** retain the current online textbook ingestion/RAG pipeline, administrator-configurable AI integrations, current platform architecture boundaries, and data contracts unless an explicitly approved design replaces them.
- **R7 — Complete deletion:** when a capability is classified Delete, remove or retire its UI, routes, API clients, backend endpoints/domain code, projections, configuration, operational documentation, tests, and optional services when they no longer have another consumer. Do not leave fake controls or dead compatibility wrappers.
- **R8 — Real user actions:** retained buttons and navigation entries must perform durable or clearly defined actions. Controls that only toggle ephemeral UI while claiming persistence must be implemented or removed.
- **R9 — Safe reconciliation:** preserve user-owned unrelated work, identify data/operational compatibility risks, and provide a rollback point before the merge commit is finalized.
- **R10 — Documentation alignment:** update the student product model, engineering structure, deployment guidance, and branch/runtime descriptions to match the accepted product after reconciliation.
- **R11 — Reconcile teacher behavior, then remove old runtime:** audit the latest legacy teacher frontend and port approved workflows, fixes, and data-integrity behavior into the current teacher product architecture. Prefer the current owner when it is already a functional superset: global and class-level assessment settings stay in the current settings/class surfaces. Do not merge the old red competition UI wholesale. Remove the optional legacy teacher frontend/runtime only after approved behavior is present and verified in the current teacher product.
- **R11a — One smart-paper configuration owner:** retain `main`'s existing global smart-assessment settings and per-class override/preview surfaces. Do not restore legacy's separate `/paper` route, which edits the same strategy rather than providing a distinct manual paper-library workflow. Port only validated formula, parameter, and edge-case semantics into the current owners.
- **R11b — Element-family analytics with current evidence UX:** use latest legacy's chapter-to-element-family taxonomy as the primary teacher analytics matrix (for example halogens, chalcogens, and pnictogens), while retaining the current analytics UI, report center, export, and drill-down drawers for experiments, points, attempts, and assessment evidence.
- **R11c — Reversible published-question review:** port latest legacy's published-question withdrawal lifecycle into the current evidence-aware question workbench. A published question may be withdrawn to a traceable draft, edited, revalidated, and republished without losing its lineage; this is distinct from disabling or deleting a question.
- **R11d — Teacher self-service password change:** expose the existing authenticated password-change contract in the current teacher account menu. Require the current password, update password version, and revoke other active sessions; do not mix this personal security action into global platform settings.
- **R12 — Preserve visual direction:** student and teacher pages retained or ported from legacy must be expressed through the accepted current visual systems, shells, tokens, navigation, and responsive interaction style.
- **R13 — Retain current-only student capabilities:** keep the current 3D atom/orbital learning experience and persisted Profile favorites; latest legacy contains no implementation to substitute for either capability.
- **R14 — Remove the standalone platform-operations frontend:** retire `apps/web-admin` and its runtime/deployment surface after its feature inventory is resolved. Migrate only approved remaining owners into the current teacher console and remove operations-only UI/API/configuration that no longer serves an approved workflow.
- **R14a — Supervisor-teacher account ownership:** keep one teacher product and treat the existing privileged account capability as “主管教师” rather than a separate platform-operations product. Every teacher can change their own password; only a supervisor teacher can list, create, reset, enable, or disable peer teacher accounts. Do not expose account deletion or role editing in the teacher product. Enforce first-login password change and revoke affected sessions on password reset or disable.
- **R15 — Protect canonical runtimes during the Git merge:** treat the current `main` student and teacher implementations as protected baselines during semantic merge review. Auto-merged deletions, entrypoint changes, dependency downgrades, or route rewrites from `legacy` are not accepted merely because Git reports no conflict. Restore the current runtime boundary first and then apply each approved legacy behavior deliberately.

## Acceptance Criteria

- [ ] `main` contains `legacy` in its Git ancestry through an intentional reviewed merge.
- [ ] Exactly one canonical student H5 implementation and required runtime service remain.
- [ ] Exactly one canonical teacher console remains; the current modular console owns retained teacher workflows.
- [ ] The accepted Keep/Rework/Delete matrix is reflected consistently across frontend, backend, tests, configuration, and documentation.
- [ ] The student H5 exposes exactly five root tabs with the approved responsibilities.
- [ ] Home retains an experiment-video discovery feed with the approved legacy/current behavior and without deleted fake or nonessential controls.
- [ ] Home search uses the same feed/read-model owner as default discovery, returns only published points with playable published media, keeps stable query-bound pagination, orders and labels explicit recommendations correctly, and leaves no student-video-library Elasticsearch runtime or operations contract.
- [ ] Retained legacy behaviors have explicit regression coverage, including authentication/password-change and relevant assessment edge cases.
- [ ] A first-time student enters one smart baseline flow after required password change; the separate two-stage pretest gate and temporary skip copy are absent.
- [ ] Student Assessment offers smart assembly and hierarchical chapter/directory/point custom scope in the current visual system; selected scope validation and per-point question counts match the approved latest-legacy behavior, and random/all-range entry modes are absent.
- [ ] Retained Atom functionality uses the current configurable online textbook RAG path without reintroducing a second vector-management system.
- [ ] No retained visible action falsely reports a durable result when it only changed component-local state.
- [ ] Removed capabilities leave no reachable route, enabled navigation entry, active background projection, or advertised operations setting unless a documented remaining consumer requires it.
- [ ] Approved legacy teacher workflows and fixes are present in the current teacher product with regression coverage, without duplicating current assessment settings, teacher account administration, or other current owners; after verification, the optional old teacher frontend/service and obsolete product documentation are removed.
- [ ] Smart-paper configuration remains fully available through current global and per-class settings, with no duplicate legacy `/paper` route or competing configuration owner.
- [ ] Teacher analytics uses the approved element-family primary matrix and the current experiment/point/evidence/report drill-down experience.
- [ ] A teacher can withdraw a published question to a traceable draft, revise it, pass current evidence/validation gates, and republish it; disable remains a separate action.
- [ ] Every teacher can change their own password from the current teacher account menu, with current-password verification and other-session revocation.
- [ ] The standalone platform-operations frontend and runtime are removed, with every former capability explicitly migrated or deleted and no orphaned navigation, API, deployment, or documentation surface.
- [ ] Teacher account management is embedded in current Teacher Settings and visible only to supervisor teachers; ordinary teachers retain self-service password change, no teacher account can delete historical ownership, and first-login/reset/disable security behavior is enforced.
- [ ] Ported legacy student behavior uses the accepted current modern green visual language rather than legacy red competition styling.
- [ ] The 3D atom/orbital learning experience and persisted Profile favorites remain available in the canonical student H5.
- [ ] A semantic comparison against the pre-merge `main` baseline confirms that Git's automatic merge did not replace either modern frontend entrypoint, delete retained current-only features, downgrade dependencies, or silently restore legacy visual assets.
- [ ] Student H5 typecheck, tests, production build, and mobile viewport QA pass.
- [ ] Backend architecture validation and relevant backend tests pass; production-readiness checks pass to the extent supported by the local environment.
- [ ] The pre-existing `artifacts/catalog_outline_seed_validation_report.json` modification remains preserved and outside task commits unless the user separately requests it.

## Out of Scope

- Native WeChat Mini Program packaging or WeChat-specific APIs.
- Preserving a capability solely because it existed in either branch.
- Maintaining permanent compatibility wrappers for deleted legacy modules.
- A new student media-delivery authentication protocol; the current protected media contract remains for this reconciliation and can be hardened in a dedicated follow-up.
- Cross-device persistence for student AI chat history; retained browser-local history must be labeled as local-device history rather than implying server persistence.

## Resolved Technical Decisions

- Focused Home video search uses the canonical Home catalog/video read model rather than a dedicated student Elasticsearch projection. Elasticsearch remains in use for the single textbook RAG vector projection and for teacher catalog-authoring search, which have separate consumers and contracts.
- The internal `admin` identity may remain the privileged implementation of a supervisor teacher, but it is not exposed as a separate product. The legacy migration that collapses every privileged role to ordinary `teacher` is not accepted because it would erase the approved supervisor boundary.
- Migration filenames from `legacy` must be rebased above `main`'s current migration head rather than introducing duplicate `041`/`042` identifiers.

## Notes

- This is a complex cross-surface task and requires `design.md` and `implement.md` before activation.
- Initial student evidence and recommendations are maintained in `research/feature-cut-matrix.md`; teacher evidence is maintained in `research/teacher-feature-cut-matrix.md`.
