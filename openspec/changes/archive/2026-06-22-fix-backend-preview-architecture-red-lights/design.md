## Context

The catalog preview flow added teacher-scoped preview tokens and preview-scoped media routes. The behavior is correct, but two architecture gates now fail:

- `server/app/domains/catalog_tree/preview.py` imports `server.app.auth.AuthUser`, which makes a reusable domain module depend on the web/runtime auth owner.
- The canonical route inventory does not include newly registered preview and diagnostic routes, so route ownership validation no longer matches the FastAPI app.

The fix should restore the backend architecture contract without changing product behavior.

## Goals / Non-Goals

**Goals:**

- Keep catalog preview domain logic free of web/runtime auth imports.
- Keep existing preview token claims, expiration, URLs, and student-preview behavior stable.
- Register all current preview/media diagnostic routes in the canonical inventory.
- Return backend architecture tests to green.

**Non-Goals:**

- No teacher frontend refactor.
- No route path rename or compatibility removal.
- No redesign of preview authentication, media streaming, or student preview UX.
- No broader backend domain splitting beyond the red-light files.

## Decisions

1. Use a runtime-neutral teacher identity payload at the domain boundary.

   `create_catalog_point_preview_token` will accept the identity fields it needs (`id`, `username`, `display_name`, `password_version`) through a small dict-like structure rather than importing `AuthUser`. The API router remains responsible for obtaining the authenticated teacher user from FastAPI dependencies.

   Alternative considered: move token creation entirely into the API router. That would remove the import, but it would also split preview validation and token semantics across layers. Keeping token assembly in the preview domain preserves a single preview owner while keeping the input runtime-neutral.

2. Treat preview and hidden media helper routes as canonical backend routes.

   Even routes marked `include_in_schema=False` are registered FastAPI routes and are part of runtime behavior. The inventory should list them so architecture validation remains exact.

   Alternative considered: exclude hidden routes from inventory validation. That would weaken the route inventory contract and hide exactly the sort of drift this test is meant to catch.

## Risks / Trade-offs

- Runtime-neutral identity shape could drift from `AuthUser` fields -> Keep the conversion in the API router explicit and covered by preview tests.
- Inventory entries may be classified too broadly -> Use existing owner labels (`admin-api` and `student-api`) consistently with the route surface.
- Token behavior regression -> Preserve current tests for token scoping, expiry, preview detail, and preview media scope.
