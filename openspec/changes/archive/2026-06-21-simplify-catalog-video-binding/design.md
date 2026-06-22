## Context

Catalog point video binding currently has three mismatched models layered together:

- The product model says one catalog point has at most one experiment video.
- The teacher UI still exposes a multi-select asset dropdown, allowing batch binding without thumbnails or enough media context.
- The backend stores each binding with its own `draft` / `published` / `archived` state, and student visibility requires both `media_assets.upload_status = ready` and `experiment_catalog_point_media_bindings.binding_status = published`.

This makes routine authoring confusing. Teachers must first upload/process a video in the video resource library, then return to the point, choose from a text-only dropdown, bind as draft, and publish the binding. Because node publication already controls student visibility, the additional binding publication state has no useful product meaning for this workflow.

The implementation should follow the mature CMS/media-library pattern used by systems such as Strapi, WordPress, Cloudinary integrations, and Contentful extensions: a content field shows either an empty media slot or a selected asset preview; choosing/replacing opens a media library picker with thumbnails, metadata, search/filtering, preview, and a single insert/select action.

## Goals / Non-Goals

**Goals:**

- Make the video tab represent exactly one selected video for the current catalog point.
- Replace the inline text-only Select with a modal media picker that shows visual and operational context.
- Make selecting a ready video immediately bind it as the point's active video.
- Keep replacement and removal simple: choose another video to replace, or remove the current binding.
- Remove teacher-facing publish/unpublish controls for catalog point video bindings.
- Update student and teacher preview visibility so a bound ready video appears when the point itself is visible/published.
- Normalize existing data so every canonical point keeps at most one active non-archived video binding.
- Preserve the separate video resource upload/library page as the place where raw video files are uploaded and processed.

**Non-Goals:**

- This change does not redesign the video resource library upload workflow.
- This change does not add multi-video playlists, chapters, alternate camera angles, or per-point video ordering.
- This change does not remove upload/processing status from media assets.
- This change does not make unready videos student-visible.
- This change does not change node/point publication semantics beyond no longer requiring binding-level publication.

## Decisions

### Decision 1: Treat point video binding as a single active reference

For catalog point authoring, the binding table should behave as if each canonical point has at most one active, non-archived binding. The existing `experiment_catalog_point_media_bindings` table can remain in place, but write behavior should archive any previous active bindings for the same canonical point before inserting or updating the selected asset.

Fresh and upgraded schema should add a partial uniqueness rule where practical:

```text
unique active video per canonical point:
  canonical_point_id
  where binding_status <> 'archived'
```

For placements that do not yet have a canonical point id, the write path should use the node id as fallback identity and still avoid multiple active bindings for that point.

Alternative considered: keep multiple active rows and hide all but the first in the UI. Rejected because it preserves inconsistent backend state and leaves student/read-model behavior ambiguous.

### Decision 2: Keep archived as deletion state, remove draft/published as authoring states

The table's `binding_status` column can temporarily remain for migration safety and older data, but teacher authoring should no longer create draft bindings or expose publish/unpublish actions. New binds should write the active visible state directly, or the read model should treat any non-archived binding as active.

Student visibility should depend on:

```text
point/node is visible to students
AND media asset upload_status = ready
AND binding_status <> archived
```

`published_by` and `published_at` are no longer meaningful for catalog point video binding and should not appear as teacher-facing concepts. They may remain nullable legacy columns until a future destructive cleanup if that is safer than rewriting every historical migration immediately.

Alternative considered: rename `published` to `active`. Rejected for now because it creates a schema churn step without much product value; the behavior can be simplified while preserving migration compatibility.

### Decision 3: Use a media picker modal, not a richer dropdown

Ant Design `Select` supports custom option rendering, but a dropdown is still a poor fit for videos: thumbnails, processing state, preview actions, file names, search, and empty states need more room. The video tab should instead show:

```text
Video tab
  Header / shortcut to video resources
  Current video slot
    empty: dashed choose-video slot
    selected: thumbnail + title + filename + readiness + preview / replace / remove

Picker modal
  search/filter bar
  list or grid of ready/processing video assets
  rows/cards with thumbnail, title, filename, status, updated time
  preview affordance
  disabled state for unready assets
  Select video action
```

The first implementation can use a compact list inside a modal rather than a full DAM grid, as long as it includes visual thumbnails and enough metadata to make the choice clear.

Alternative considered: keep `Select` and use `optionRender`. Rejected because it still hides too much information, has limited spatial hierarchy, and keeps the interaction looking like choosing a string rather than selecting a media asset.

### Decision 4: Auto-save selection, replacement, and removal

Video binding should match the simplified related-experiments workflow: direct manipulation persists immediately. Selecting a video from the picker saves the binding and closes the picker. Removing the video archives/deletes the binding and refreshes the point detail. There is no separate save button.

Replacement is not a special second workflow. It is "Select another video", and the backend ensures the old active binding is archived.

Alternative considered: let teachers stage a selected video and click Save. Rejected because a single media reference has low risk and immediate save is easier to reason about.

### Decision 5: Keep upload in the video resource library

The point video tab may retain a clear "视频资源入口" shortcut for uploading/processing new videos, but it should not inline upload. This matches the current system boundary: the media library owns ingestion, duplicate handling, transcoding, and thumbnail generation; the point editor only chooses from existing assets.

The picker should include copy that indicates unready videos cannot be selected yet, but it should not teach upload mechanics in the point editor itself.

Alternative considered: add drag-and-drop upload directly into the point tab. Rejected because it mixes ingestion with authoring and would expand the change into upload pipeline UX.

### Decision 6: Update derived status counts carefully

Existing code and tests use `published_media_count` as the signal for video completeness. With binding publication removed, this count should become "student-visible ready media count" or be replaced by a clearer `ready_media_count` / `active_ready_media_count` in future work.

For minimal compatibility, `published_media_count` can keep its name but count active non-archived bindings whose asset is ready. UI labels should show Chinese readiness text rather than raw backend enum names.

Alternative considered: rename all API fields immediately. Rejected because it would widen the blast radius; behavior can be corrected first while keeping response shape stable.

## Risks / Trade-offs

- [Risk] Existing points may have multiple non-archived video bindings. -> Mitigation: migration archives all but the first deterministic binding per canonical point, preferring currently published and ready assets, then lowest display order / earliest created row.
- [Risk] Old clients may still call publish/unpublish binding endpoints. -> Mitigation: keep the route temporarily but make publish/unpublish no-ops or map them to active/inactive semantics only where safe; teacher frontend stops using it.
- [Risk] Student pages may suddenly show videos that were bound as draft before. -> Mitigation: migration should preserve only the best single active binding, and product decision says bound ready videos should be visible through point publication. Review staging data before production deployment.
- [Risk] Keeping the `binding_status` column while removing its product meaning can confuse future maintainers. -> Mitigation: add explicit spec/tests and comments around active vs archived semantics; schedule a later destructive cleanup if desired.
- [Risk] Picker modal could become a full media manager. -> Mitigation: keep it scoped to choosing one existing video; upload and deep media management remain in the video resource page.

## Migration Plan

1. Add migration to normalize existing catalog point media bindings:
   - identify binding groups by canonical point id or node id fallback;
   - keep one best active row per group;
   - archive other non-archived rows;
   - add a partial unique index for active canonical point bindings where feasible.
2. Update backend binding request schema to remove teacher-controlled status or default new binds to active.
3. Update bind operation to archive previous active bindings for the same canonical point before inserting/reusing the selected media asset.
4. Update student, preview, search, AI context, and status count queries from `binding_status = published` to active non-archived + ready asset where applicable.
5. Update teacher frontend to use a single selected video slot and picker modal.
6. Remove publish/unpublish controls from the teacher video panel.
7. Update tests and OpenSpec validation.
8. Rebuild affected services.

Rollback:

- Code rollback can restore old behavior, but data normalized to one active binding cannot reconstruct the full old multi-binding state without database backup.
- The migration should be one-way for active binding normalization, with rollback documented as database restore if preserving old multi-binding state is required.

## Open Questions

- Should the backend physically drop `published_by` and `published_at` for catalog point bindings now, or leave them as legacy nullable columns for a later destructive cleanup?
- Should the picker initially show all videos with unready rows disabled, or default-filter to ready videos with a toggle to inspect processing items?
- Should stale publish/unpublish API calls return a compatibility success detail, or return `410 Gone` / `400 Unsupported` after the teacher frontend is updated?
