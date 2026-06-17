## Context

The productionization work has already reduced the largest frontend shell risks and moved several backend admin areas into focused routers. The remaining structural risk is `server/app/admin.py`, which still mixes platform settings, AI configuration, learning assistant admin actions, RAG asset discovery, feedback management, class roster/registration, curriculum review, and media operations in one module.

This module is not just long; it also owns different engineering concerns at once: Pydantic contracts, route definitions, SQLAlchemy queries, file serving, service orchestration, streaming responses, and compatibility aliases. That makes future changes harder to review because a small change in one admin domain can touch a file that appears to own unrelated domains.

## Goals / Non-Goals

**Goals:**

- Remove `server.app.admin` from production app routing.
- Preserve all existing admin API paths, methods, auth dependencies, response fields, and compatibility aliases.
- Move endpoint groups into domain-owned routers under `server/app/routers/`.
- Move SQL-heavy and stateful business logic into focused service modules.
- Add route registration tests that assert moved endpoints exist exactly once.
- Record the owner map and validation in OpenSpec files so future work can continue after context compaction.

**Non-Goals:**

- Do not redesign APIs or frontend workflows.
- Do not rename paths or introduce versioned API paths.
- Do not change database schema, migrations, seed files, protected resources, RAG evidence semantics, or canonical chunk data.
- Do not change GitHub Actions triggers or release flow.
- Do not refactor unrelated existing routers that are already feature-owned.
- Do not rewrite `server/app/agent.py` or the learning assistant internals beyond moving admin HTTP orchestration.

## Decisions

1. Replace the monolith with domain routers instead of one renamed router.

   Target routers:

   | New router | Endpoint ownership |
   | --- | --- |
   | `admin_platform.py` | platform settings and AI configuration |
   | `admin_learning_assistant.py` | learning assistant runtime, RAG asset listing, ask, and ask stream |
   | `admin_feedback.py` | feedback summary/list/detail/update |
   | `admin_classes.py` | classes, teacher assignment, registration settings, roster import, students, password reset |
   | `admin_curriculum_review.py` | curriculum version and review item operations |
   | `admin_media.py` | media assets, uploads, duplicate decisions, file/stream/thumbnail serving, media bindings |

   Rationale: these groups match frontend feature ownership and existing service boundaries. A single renamed `admin.py` would keep the same review risk.

2. Keep the `/api/admin` prefix on every new router.

   Rationale: preserving the external API contract is more important than exposing internal module names. Every new router should define `APIRouter(prefix="/api/admin", ...)` or an equivalent prefix composition that preserves all current paths.

3. Move DB-heavy feedback and class/roster logic into services.

   Rationale: feedback filtering/update and class/roster registration operations contain the highest amount of SQL and state manipulation inside the current router. Extracting them prevents the new routers from becoming smaller monoliths.

4. Keep existing service modules as sources of truth where they already exist.

   Rationale: platform settings, media lifecycle, curriculum, review, and roster parsing already have service modules. The refactor should reuse them and avoid duplicating business logic.

5. Preserve compatibility aliases explicitly.

   Rationale: media binding deletion currently has multiple routes, including compatibility-style `delete` and `archive` operations. Even if the frontend primarily uses one path, the refactor must keep all current paths unless a later spec intentionally removes them.

6. Prove ownership with route-registration tests.

   Rationale: path-preserving refactors can silently double-register routes or drop one route. Tests should inspect `server.app.admin_main.app.routes`, assert required path/method pairs are present exactly once, and confirm `server.app.admin` is no longer imported by the application wiring.

## Target Owner Map

| Domain | Router | Service/schema candidates |
| --- | --- | --- |
| Platform and AI config | `server/app/routers/admin_platform.py` | existing `services/platform_settings.py`; optional `schemas/admin_platform.py` |
| Learning assistant admin | `server/app/routers/admin_learning_assistant.py` | optional `services/admin_learning_assistant_service.py`; existing `agent.py` |
| Feedback | `server/app/routers/admin_feedback.py` | new `services/feedback_service.py`; existing feedback schemas/helpers |
| Classes and roster | `server/app/routers/admin_classes.py` | new `services/class_roster_service.py`; existing `services/roster.py` |
| Curriculum and review | `server/app/routers/admin_curriculum_review.py` | existing `services/curriculum.py`, `services/review.py` |
| Media | `server/app/routers/admin_media.py` | existing `services/media.py`; optional helper for file responses |

## Migration Plan

1. Add OpenSpec artifacts and commit them before implementation.
2. Add baseline route-registration tests for every path currently owned by `admin.py`.
3. Extract low-risk routers first: platform/AI config and curriculum/review.
4. Extract learning assistant admin/RAG routes while preserving streaming response behavior.
5. Extract media routes while preserving file response and compatibility aliases.
6. Extract feedback routes and move query/update logic into a service.
7. Extract classes/registration/roster routes and move database-heavy logic into a service.
8. Update `server/app/admin_main.py` to include the new routers and stop importing `server.app.admin`.
9. Delete `server/app/admin.py` once no imports remain.
10. Run focused tests after each major domain move and full production-readiness validation at the end.

Rollback is straightforward while this is branch-local: revert the relevant commit(s). No database or resource migration is part of this change.

## Risks / Trade-offs

- [Risk] A route can be dropped or double-registered during extraction. Mitigation: route-registration tests assert each moved path/method appears exactly once.
- [Risk] Streaming assistant behavior can regress despite type checks passing. Mitigation: preserve the existing streaming helper behavior mechanically and run assistant/runtime tests plus optional e2e smoke if runtime pages are touched.
- [Risk] Media file paths and compatibility aliases are easy to break. Mitigation: keep existing service calls, add route registration coverage for all media paths, and run media lifecycle tests.
- [Risk] Feedback/class extraction can accidentally change SQL filters or role checks. Mitigation: move logic mechanically first, then only introduce thin service wrappers; run backend tests after each group.
- [Risk] Moving Pydantic classes into schema modules can create import cycles. Mitigation: keep schema modules domain-local and import services from routers, not routers from services.

## Open Questions

None for this pass. The owner has confirmed that `admin.py` is not needed as a long-term compatibility layer.
