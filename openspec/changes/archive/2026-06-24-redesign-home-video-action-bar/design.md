## Context

The student home root now behaves as an experiment-video discovery feed. Each video card already has a 16:9 preview/poster, catalog path, title, summary, badges, and actions. The current action area is a three-column toolbar containing `查看实验`, `搜索相关`, and `问问Atom`.

That structure was useful while the page was still finding its shape, but it now fights the video-feed mental model. `搜索相关` belongs to the home header / video-library search route, not to every individual video card footer. The footer should instead feel like a compact video action row: one clear learning CTA plus familiar lightweight actions.

## Goals / Non-Goals

**Goals:**

- Make the home video card footer read as a classic video-stream action row.
- Preserve `查看实验` as the primary left-side learning action.
- Preserve Atom as a learning-assistant action and make it visually branded with the Atom icon and green treatment.
- Remove the per-card `搜索相关` footer action.
- Keep the layout compact, aligned, and touch-safe on common phone widths.
- Avoid backend/API changes for lightweight icon affordances.

**Non-Goals:**

- Do not add persistent like/favorite/share data models.
- Do not implement comments, creator/channel concepts, follower counts, or entertainment-social ranking.
- Do not change home feed ranking, preview activation, media playback, or video-library search behavior.
- Do not change the point detail route, Atom chat route, or bottom navigation identity.

## Decisions

1. Use a left-primary / right-icons layout.

   The action row should be a flex row with `查看实验` anchored on the left and a compact icon group on the right. This keeps the learning destination obvious while letting the secondary actions feel like video-feed chrome.

   Alternative considered: keep three equal columns and replace `搜索相关` with another label. That still reads as a utility toolbar and keeps too much visual weight under every video card.

2. Remove card-level search from the footer.

   Search should stay in the home header entry and the second-level video-library page. A card-level `搜索相关` action makes the footer feel like a query panel and duplicates a higher-level discovery affordance.

   Alternative considered: keep search under the `更多` menu. That can be reconsidered later if students need per-card related discovery, but it should not remain a primary visible card action.

3. Treat Atom as the one branded high-priority icon action.

   Atom should use the existing Atom icon and green primary color treatment. It may include a short `Atom` label if space allows, because it is a product-specific action rather than a universal video icon. When the assistant is disabled, the Atom action should keep the row geometry stable while communicating disabled state.

   Alternative considered: make Atom visually equal to like/favorite/share. That undersells the learning assistant and makes a core learning action look like generic social chrome.

4. Keep like, favorite, share, and more lightweight until behavior is specified.

   These actions can render as recognizable icon buttons with accessible labels. They do not need backend persistence in this change. If they are inert, local-only, or future-enabled, they must not block the primary learning flow or imply that social engagement is required.

   Alternative considered: defer all non-learning icons. That would leave the row too sparse and miss the user's requested video-stream feel.

5. Prefer simple CSS layout over new component infrastructure.

   The change is local to the home feed card markup and card styles. A new shared action-bar component is not needed unless later pages reuse the pattern.

## Risks / Trade-offs

- Icon-only controls may be ambiguous → Provide accessible labels and use familiar lucide icons for like, favorite/bookmark, share, and more.
- Rendering non-persistent social-style actions may imply unavailable behavior → Keep them visually lightweight and avoid counters, active engagement claims, or ranking copy.
- Atom label plus multiple icons may overflow narrow phones → Use a non-wrapping icon group, allow Atom to fall back to icon-only or compact label styling, and verify 360px, 390px, and 430px widths.
- Removing `搜索相关` may reduce one shortcut path → The home header and video-library entry remain the search/discovery route, preserving a cleaner information architecture.

## Migration Plan

1. Replace the `HomeVideoFeedCard` footer markup with the left-primary / right-icons action row.
2. Remove the `onSearch` card-footer prop path from the feed card if it is no longer used by the footer.
3. Keep the home header search/video-library entry unchanged.
4. Update CSS for the compact action row and remove the three-column divider treatment.
5. Update tests that assert the old `搜索相关` footer action and add coverage for the new action row.
6. Build and hot-update the student container for phone-frame review.
