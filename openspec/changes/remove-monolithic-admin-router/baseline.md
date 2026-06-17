## Current Backend Structure Baseline

Date: 2026-06-17

Branch: `codex/productionize-admin-platform`

## Current State

`server/app/admin.py` is the remaining backend admin monolith:

- Size: 1843 lines.
- FastAPI owner: imported by `server/app/admin_main.py` as `admin_router`.
- Registration: `app.include_router(admin_router)` still wires the mixed router into the production app.
- Scope: unrelated endpoint groups live in one module alongside Pydantic request models, helper functions, SQLAlchemy queries, file-serving helpers, and learning-assistant streaming glue.

Existing domain routers already use the desired ownership model:

| File | Current role |
| --- | --- |
| `server/app/routers/admin_analytics.py` | analytics summary routes |
| `server/app/routers/admin_experiments.py` | experiment catalog/admin routes |
| `server/app/routers/admin_learning_resources.py` | learning resource routes |
| `server/app/routers/admin_question_banks.py` | question bank import/export/list routes |
| `server/app/routers/admin_question_drafts.py` | draft question routes |
| `server/app/routers/admin_question_generation.py` | generation routes |
| `server/app/routers/admin_question_workbench.py` | AI question workbench routes |
| `server/app/routers/admin_point_aware_questions.py` | point-aware question routes |
| `server/app/routers/student_experiment_questions.py` | student experiment question routes |

## Current `admin.py` Endpoint Groups

### Platform And AI Configuration

| Method | Path |
| --- | --- |
| GET | `/api/admin/platform-settings` |
| PUT | `/api/admin/platform-settings` |
| GET | `/api/admin/ai-configuration` |
| PUT | `/api/admin/ai-configuration` |

### Learning Assistant Admin / RAG Assets

| Method | Path |
| --- | --- |
| GET | `/api/admin/learning-assistant/runtime` |
| GET | `/api/admin/rag-assets` |
| POST | `/api/admin/learning-assistant/ask` |
| POST | `/api/admin/learning-assistant/ask/stream` |

### Feedback

| Method | Path |
| --- | --- |
| GET | `/api/admin/feedback/summary` |
| GET | `/api/admin/feedback` |
| GET | `/api/admin/feedback/{feedback_id}` |
| PATCH | `/api/admin/feedback/{feedback_id}` |

### Classes, Registration, Roster

| Method | Path |
| --- | --- |
| GET | `/api/admin/classes` |
| POST | `/api/admin/classes` |
| GET | `/api/admin/classes/{class_id}` |
| PATCH | `/api/admin/classes/{class_id}` |
| POST | `/api/admin/classes/{class_id}/teachers` |
| GET | `/api/admin/registration-settings` |
| PUT | `/api/admin/registration-settings` |
| GET | `/api/admin/classes/{class_id}/registration-settings` |
| PUT | `/api/admin/classes/{class_id}/registration-settings` |
| POST | `/api/admin/classes/{class_id}/roster/preview` |
| POST | `/api/admin/classes/{class_id}/roster/import` |
| GET | `/api/admin/classes/{class_id}/students` |
| POST | `/api/admin/classes/{class_id}/students` |
| PATCH | `/api/admin/classes/{class_id}/students/{student_id}` |
| DELETE | `/api/admin/classes/{class_id}/students/{student_id}` |
| POST | `/api/admin/classes/{class_id}/students/{student_id}/reset-password` |

### Curriculum Versions And Review Items

| Method | Path |
| --- | --- |
| GET | `/api/admin/curriculum/versions` |
| POST | `/api/admin/curriculum/versions` |
| GET | `/api/admin/curriculum/versions/{version_id}` |
| POST | `/api/admin/curriculum/versions/{version_id}/publish` |
| POST | `/api/admin/curriculum/versions/{version_id}/archive` |
| GET | `/api/admin/review/items` |
| GET | `/api/admin/review/items/{item_id}` |
| POST | `/api/admin/review/items/{item_id}/actions` |

### Media

| Method | Path |
| --- | --- |
| GET | `/api/admin/media/assets` |
| POST | `/api/admin/media/assets/precheck` |
| GET | `/api/admin/media/assets/processing` |
| POST | `/api/admin/media/assets/complete-upload` |
| GET | `/api/admin/media/assets/{asset_id}/file` |
| GET | `/api/admin/media/assets/{asset_id}/stream` |
| GET | `/api/admin/media/assets/{asset_id}/thumbnail` |
| POST | `/api/admin/media/assets/{asset_id}/retry-processing` |
| PATCH | `/api/admin/media/duplicate-candidates/{candidate_id}` |
| POST | `/api/admin/media/assets` |
| POST | `/api/admin/media/assets/{asset_id}/replace` |
| POST | `/api/admin/media/bindings` |
| POST | `/api/admin/media/bindings/{binding_id}/publish` |
| POST | `/api/admin/media/bindings/{binding_id}/unpublish` |
| DELETE | `/api/admin/media/bindings/{binding_id}` |
| POST | `/api/admin/media/bindings/{binding_id}/delete` |
| POST | `/api/admin/media/bindings/{binding_id}/archive` |

## Existing Service Surface To Reuse

| Module | Reuse expectation |
| --- | --- |
| `server/app/services/platform_settings.py` | keep as platform and AI config backing service |
| `server/app/services/media.py` | keep media lifecycle operations; move only HTTP/file glue as needed |
| `server/app/services/curriculum.py` | keep curriculum version operations |
| `server/app/services/review.py` | keep review item operations |
| `server/app/services/roster.py` | keep roster parsing/preview helpers |
| `server/app/agent.py` | keep assistant runtime behavior; move admin endpoint orchestration only |

## Test Gap

Existing router tests cover many already-split routers but do not assert registration or compatibility for the remaining `admin.py` endpoint groups. This change must add route registration coverage for each moved group and ensure each path/method appears exactly once in `server.app.admin_main.app`.

## Constraints

- Do not modify protected seed/resource data.
- Do not modify database schema or migrations.
- Do not modify frontend route behavior.
- Do not modify GitHub Actions production readiness triggers; it remains manual-only.
- Do not remove compatibility endpoints, especially media binding `delete` and `archive` aliases, unless the owner explicitly requests an API break.
