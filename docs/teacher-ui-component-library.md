# Teacher UI Component Library

`apps/web-teacher` uses Ant Design through the product-local adapter module at `apps/web-teacher/src/ui/TeacherUI.tsx`.

The adapter is the boundary for component-library primitives. Teacher pages should import layout, buttons, cards, forms, alerts, empty/loading states, switches, tooltips, and modals from `TeacherUI` instead of importing Ant Design directly in page files. This keeps the SYSU red and warm-paper identity in one provider and prevents broad page CSS from drifting back into hand-written primitive styles.

## Styling Rules

- Keep brand assets, sidebar width, desktop minimum width, and canonical routes in page code.
- Put Ant Design theme tokens in `TeacherUiProvider`.
- Keep legacy page-specific layout classes for dense workbench surfaces such as the catalog tree, question review list, learning matrix, and report detail.
- Do not reimplement primitive button, card, form, alert, empty, loading, switch, tooltip, or modal shells in page CSS.
- If an Ant Design component needs a stable selector for tests or E2E, expose it through the adapter and pass through `className`, `data-testid`, and ARIA props.

## Validation

Run these commands after changing the teacher UI adapter or migrated teacher pages:

```powershell
Set-Location apps/web-teacher
npm run typecheck
npm test
npm run build
```

Then run the legacy E2E smoke against Compose when user flows or deployment wiring changed:

```powershell
python scripts/validate_legacy_e2e.py --build
```

## Bundle Size

The first Ant Design-backed production build for `apps/web-teacher` produced:

- CSS: `32.91 kB`, gzip `6.37 kB`
- JS: `702.21 kB`, gzip `226.05 kB`

The JS chunk exceeds Vite's default `500 kB` warning threshold. This increase is accepted for this legacy teacher-only workbench because it replaces broad hand-written primitives with a maintained component library and does not affect `apps/web-student`. Revisit code splitting only if teacher load time becomes a measured issue.
