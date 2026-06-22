## 1. Baseline And Acceptance

- [x] 1.1 Review the current student H5 owner map and accept `app/router`, `app/shell`, `routes`, `features`, `shared`, `mobile`, and `styles` as the canonical starting structure.
- [x] 1.2 Review the current admin web owner map and accept the desired `app`, `api`, `features`, `components`, `lib`, and `styles` structure as the next target.
- [x] 1.3 Review the current backend owner map and accept `app_runtime`, `api`, `domains`, `infrastructure`, `workers`, and `scripts_support` as canonical.
- [x] 1.4 Record large-module debt and classify it as follow-up implementation work rather than part of this structure-standard change.
- [x] 1.5 Decide that frontend boundary validation should start as lightweight custom validation scripts, with ESLint import rules or TypeScript project references considered only after the refactor shape stabilizes.

## 2. Student H5 Engineering Structure

- [x] 2.1 Specify root tab pages and reusable second-level detail pages explicitly in the route semantics contract.
- [x] 2.2 Specify that cross-page navigation must use `app/router/navigation.ts` or an equivalent typed navigation owner.
- [x] 2.3 Record `api.ts` domain split as follow-up implementation work while preserving a stable HTTP primitive.
- [x] 2.4 Specify that route-independent display logic belongs in feature owners.
- [x] 2.5 Record large feature components as follow-up implementation work when interaction state, rendering, and adapters are mixed.
- [x] 2.6 Specify style ownership so feature CSS does not leak global shell behavior.
- [x] 2.7 Specify mobile viewport QA as the required regression gate for route-stack and layout changes.

## 3. Admin Web Engineering Structure

- [x] 3.1 Specify `App.tsx` extraction into app providers, auth guard, route registry, nav model, and shell layout as the next recommended implementation change.
- [x] 3.2 Record `api/index.ts` split into HTTP primitives plus domain-specific admin clients and schemas as follow-up implementation work.
- [x] 3.3 Record large page decomposition into page orchestration, hooks, panels, forms, tables, and adapters as follow-up implementation work.
- [x] 3.4 Specify per-feature style ownership and reduction of global `styles.css` to shell/global tokens as follow-up implementation work.
- [x] 3.5 Specify that lazy-loaded page chunks and chunk reporting must be preserved when route ownership changes.
- [x] 3.6 Specify admin e2e smoke as the required regression gate for shell, auth, navigation, and top-level pages.

## 4. Backend Engineering Structure

- [x] 4.1 Specify the existing backend architecture validation as a required gate.
- [x] 4.2 Extend the backend owner map with subdomain patterns for commands, read models, projections, adapters, and workers where needed.
- [x] 4.3 Record large domain file splitting as follow-up implementation work when domains mix commands, read models, external adapters, and projection logic.
- [x] 4.4 Explicitly document root-level modules that remain outside `domains` and `infrastructure` as migration candidates rather than compatibility owners.
- [x] 4.5 Specify that worker entrypoints remain runtime-safe and isolated from API routes.
- [x] 4.6 Specify exact route inventory validation when backend API ownership changes.

## 5. Production Governance

- [x] 5.1 Update production readiness documentation to cite this application structure standard.
- [x] 5.2 Record frontend boundary validation as a required follow-up once the frontend refactor starts.
- [x] 5.3 Specify full production readiness with e2e after structural refactors that affect any two surfaces.
- [x] 5.4 Preserve the policy that destructive refactors are allowed when the OpenSpec change, validation output, and git history make rollback clear.
