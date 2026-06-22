## Why

The backend architecture gate is currently red after the catalog preview work: a domain module imports a web/runtime auth type, and several newly registered preview/media diagnostics routes are missing from the canonical route inventory. This change restores the intended backend architecture contract before more teacher-console work builds on top of it.

## What Changes

- Remove the catalog preview domain's dependency on `server.app.auth.AuthUser` by passing a small runtime-neutral teacher identity shape into token creation.
- Add the preview, media thumbnail-stream, and video-library search diagnostics routes to the canonical backend route inventory.
- Keep the existing runtime behavior and API paths unchanged.
- Verify the backend architecture and route inventory tests return to green.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `backend-slim-domain-architecture`: Clarify that catalog preview token/domain helpers must remain runtime-neutral and that preview/media diagnostic routes must be represented in the canonical route inventory.

## Impact

- Affected backend domain/API files:
  - `server/app/domains/catalog_tree/preview.py`
  - `server/app/api/admin/admin_catalog_tree.py`
  - `server/tests/contracts/backend_route_inventory.json`
- Affected validation:
  - `server/tests/test_backend_architecture.py`
  - `server/tests/test_admin_router_contract.py`
