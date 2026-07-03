## 1. Frontend Runtime Reshape

- [x] 1.1 Remove the newer frontend packages from the legacy branch runtime surface.
- [x] 1.2 Promote the old student frontend to `apps/web-student`.
- [x] 1.3 Promote the old teacher frontend to `apps/web-backoffice`.
- [x] 1.4 Update frontend package names, document titles, app metadata, and local product references for the renamed apps.

## 2. Backoffice Product Naming

- [x] 2.1 Replace shell-level teacher-console wording in the promoted backoffice app with backoffice/backend wording.
- [x] 2.2 Remove `platform_admin` as a canonical old backoffice frontend admission role while keeping `admin` and `teacher`.
- [x] 2.3 Update backoffice tests that assert shell labels, product names, and role boundaries.

## 3. Compose And Documentation

- [x] 3.1 Replace the default Compose topology with the old runtime using `web-student`, `web-backoffice`, and `backend`.
- [x] 3.2 Remove the separate old Compose entrypoint after promotion.
- [x] 3.3 Update README and environment documentation to describe the legacy branch two-entrypoint runtime and remove standalone web-admin token-console instructions.

## 4. Validation

- [x] 4.1 Run package install/typecheck/test/build for `apps/web-student`.
- [x] 4.2 Run package install/typecheck/test/build for `apps/web-backoffice`.
- [x] 4.3 Run focused backend import/route tests for auth, old admin/student APIs, and retained backend compatibility.
- [x] 4.4 Run `openspec validate trim-legacy-to-old-runtime --strict`.
