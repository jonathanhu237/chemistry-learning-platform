## Why

The OpenSpec inventory has accumulated many small student H5 capability specs across several UI iterations. The current student-side behavior is mostly stable, but the specs now reflect iteration history more than durable ownership boundaries, making future changes harder to reason about.

## What Changes

- Consolidate completed student H5 specs that describe the same product surface into fewer, clearer capability files.
- Remove obsolete or empty student H5 capability remnants, including the retired assistant point-starter spec.
- Replace generated `TBD` purposes on touched specs with explicit ownership statements.
- Move home video feed and video-library search rules into a broader student video-discovery capability.
- Move catalog-shell and catalog-navigation rules into a broader student learning-catalog capability.
- Merge login lifecycle rules into the student authentication capability.
- Merge AI root, starter, and local-history rules into the student AI assistant capability.
- Remove stale point-starter mobile-design requirements that no longer match the current direct chat shell.
- Add governance for future OpenSpec inventory cleanup so completed UI iterations do not continue to create permanent one-off capabilities.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `production-engineering-governance`: Add a requirement that recurring OpenSpec cleanup must consolidate obsolete, empty, or duplicate capability specs instead of preserving iteration artifacts indefinitely.

## Impact

- Affected files are limited to `openspec/changes/consolidate-student-h5-openspec-specs/**` and `openspec/specs/**`.
- No application code, APIs, database schema, tests, Docker configuration, or runtime behavior changes.
- Existing archived changes remain untouched as historical records.
- The active `refine-student-back-arrow-geometry` change remains out of scope and must not be modified.
