## Context

The student H5 app already uses Lucide `Atom` as the student-facing AI identity mark across the root AI tab, assistant headers, empty states, and AI actions. The root assistant running turn currently uses a flat thinking line with a decorative three-dot cluster and a phase label such as `正在判断问题范围`, `正在检索课程资料`, or `正在生成回答`.

The user provided a downloaded `Atom.json` Lottie asset intended to replace the three-dot cluster. Local inspection shows the asset is small and technically clean:

- Lottie version `5.12.2`
- `100x100` viewport
- `25fps`, `31` frames, about `1.24s`
- `3330` bytes
- `3` vector shape layers
- no image assets, no fonts, no embedded external resources
- pure black stroke values in the shape layers

The change should keep the recently completed root flat thinking model while replacing the generic dot motif with an Atom-branded animated mark.

## Goals / Non-Goals

**Goals:**

- Replace the root assistant running-state three-dot cluster with the provided Atom Lottie animation.
- Preserve the existing phase-label state machine, fade-through text transitions, minimum visible timing, and completion cleanup.
- Keep the running turn flat and inline on the root canvas, with no card, pill, badge, or bordered loading surface.
- Recolor the animation to the student service's main green visual system so it belongs to the product rather than appearing as an imported black asset.
- Add the smallest reasonable React Lottie runtime dependency for local JSON rendering.
- Preserve accessibility by keeping the animation decorative and using the current phase label for status announcements.
- Preserve reduced-motion semantics by disabling or freezing repeated animation while keeping the current label visible.
- Keep contextual/detail-route loading behavior distinct unless it already uses the shared root thinking line.

**Non-Goals:**

- Do not redesign the root assistant layout, composer, message model, or header.
- Do not change assistant stream events, backend APIs, request payloads, local history, or permissions.
- Do not introduce a general animation system for the whole student app.
- Do not replace the static Atom icons in navigation, welcome, metadata, or action surfaces with animated Lottie.
- Do not copy or recreate a paid reference animation from screenshots; use only a licensed user-provided asset or an approved internal replacement.

## Decisions

1. **Use `lottie-react` for local JSON playback.**

   `apps/web-student` uses React and Vite with `resolveJsonModule` already enabled. `lottie-react` can render imported local animation data directly with a small component API:

   ```tsx
   import Lottie from "lottie-react";
   import atomThinkingAnimation from "../../assets/lottie/atom-thinking.json";
   ```

   This is simpler than using `lottie-web` directly, which would require manual container refs, mount/destroy lifecycle management, and renderer cleanup. It is also a better fit than dotLottie-specific players because the asset is ordinary `.json`, not a `.lottie` bundle.

   Alternative considered: `lottie-web` directly. Rejected because it adds implementation code without meaningful benefit for one local decorative animation.

   Alternative considered: `@lottiefiles/dotlottie-react`. Rejected for this change because the provided asset is Lottie JSON, and the dotLottie runtime is unnecessary unless we later standardize on `.lottie` packages.

2. **Replace only the visual mark inside `AssistantThinkingLine`.**

   The current `AssistantThinkingLine` already owns the root running status, phase label, fade-through text stack, queued phase timing, and cleanup. The implementation should replace:

   ```tsx
   <span className="ai-thinking-dots" aria-hidden="true">...</span>
   ```

   with a decorative Atom animation container, for example:

   ```tsx
   <span className="ai-thinking-atom-mark" aria-hidden="true">
     <Lottie ... />
   </span>
   ```

   This keeps the behavioral surface small and avoids destabilizing the assistant stream logic.

   Alternative considered: create a new root loading component that replaces `AssistantThinkingLine`. Rejected because the text transition and accessibility behavior already exist and should be preserved.

3. **Store the Lottie JSON as a local source asset.**

   The animation should live under a student-web source asset path such as:

   ```text
   apps/web-student/src/assets/lottie/atom-thinking.json
   ```

   Vite can bundle JSON imported from source. Keeping it in source also makes tests and code review straightforward.

   Alternative considered: load the downloaded JSON from a public URL or external asset host. Rejected because the assistant loading indicator must be available offline with the app bundle and must not depend on a third-party animation CDN.

4. **Recolor the asset to product green before committing it.**

   The provided JSON currently uses black stroke values (`[0,0,0,1]`). CSS `color` is not a reliable way to recolor Lottie paths because the renderer emits path-level fill/stroke values. The implementation should create the committed asset with the Lottie shape stroke colors changed to the student service main green:

   ```text
   #005826
   ```

   Equivalent Lottie normalized RGBA:

   ```text
   [0, 0.345, 0.149, 1]
   ```

   This matches `--mobile-color-green` / `--green` from the student mobile tokens and aligns with current assistant thinking colors.

   Alternative considered: keep the asset black. Rejected because black reads like an imported generic icon and is visually harsher than the current Atom product language.

   Alternative considered: mutate the imported animation data at runtime based on CSS variables. Rejected for the first implementation because static recoloring is simpler, testable, and sufficient for one brand color.

5. **Size the Atom mark as an inline status affordance, not a hero logo.**

   The current dot cluster occupies `34x24px`. The Lottie animation has a square `100x100` viewport and heavier stroke geometry, so it should render around `28px` to `34px` square in the thinking line. The exact CSS can tune optical balance, but the animation must stay secondary to the status text.

   The thinking line should remain inline-flex with stable line height. The animation container should use fixed dimensions and `flex: 0 0 auto` so playback cannot shift text layout.

   Alternative considered: render the Atom animation larger as a standalone loading panel. Rejected because it would reintroduce a separate loading surface and break the flat root chat model.

6. **Keep accessibility anchored on text, not animation.**

   The animation is decorative and should remain `aria-hidden="true"`. The outer thinking line should keep `role="status"`, `aria-live="polite"`, `aria-atomic="true"`, and the current phase label as its accessible name. Outgoing fade-through labels should remain visually hidden from assistive announcements by staying inside an `aria-hidden` visual text stack.

   Alternative considered: announce the animation or use the animation title as status. Rejected because screen reader users need the phase label, not the fact that an Atom mark is moving.

7. **Handle reduced motion explicitly.**

   CSS alone can stop the previous three-dot animation, but Lottie playback is JavaScript-driven. The implementation should either:

   - render a static Atom mark when `prefers-reduced-motion: reduce` matches, or
   - render Lottie with `autoplay={false}` and `loop={false}` for reduced-motion users.

   The current phase label must remain visible and update normally. The static/reduced mark should not be required to communicate progress.

   Alternative considered: let Lottie loop for all users and rely on CSS only. Rejected because CSS cannot reliably stop JavaScript-driven Lottie playback.

8. **Treat asset licensing as an implementation gate.**

   The user supplied a downloaded `Atom.json`, but the earlier reference page indicated a premium animation source. Before committing the exact asset into the repository, the implementation should confirm the product has appropriate rights for source control, bundled web delivery, and student-facing production use. If licensing is not confirmed, the same component and integration can use an internally authored replacement JSON with the same product requirements.

## Risks / Trade-offs

- [Risk] The Lottie asset's reveal loop may feel like an appearing/disappearing logo rather than continuous thinking. -> Mitigation: keep the animation small and secondary to the phase label; verify the loop in the actual root chat context before shipping.
- [Risk] Adding `lottie-react` increases bundle size for one animation. -> Mitigation: keep the asset tiny, limit usage to the root thinking mark, and confirm the dependency impact during build review.
- [Risk] Tests currently assert `.ai-thinking-dots` and dot-specific CSS. -> Mitigation: update tests to assert `.ai-thinking-atom-mark`, decorative `aria-hidden`, phase text transitions, and reduced-motion CSS/behavior.
- [Risk] Reduced-motion users could still see JavaScript animation if playback is not controlled. -> Mitigation: add a small media-query hook or equivalent runtime check and disable Lottie autoplay/loop when reduced motion is requested.
- [Risk] Asset licensing may not permit bundling. -> Mitigation: require licensing confirmation before committing the downloaded JSON, or substitute an approved internally authored Lottie asset.
- [Risk] The black source asset could be committed unchanged. -> Mitigation: make product-green recoloring an explicit task and test/review point.

## Migration Plan

1. Add the Lottie runtime dependency to `apps/web-student`.
2. Add the local Atom thinking Lottie JSON asset after confirming it can be used, recolored to `#005826`.
3. Add a small `AtomThinkingMark` or equivalent component colocated with assistant UI code.
4. Replace the three-dot markup inside `AssistantThinkingLine` with the Atom mark.
5. Update assistant CSS to size and align `.ai-thinking-atom-mark`; remove or deprecate dot-only styling for the root thinking line.
6. Update tests that currently assert `.ai-thinking-dots` and dot CSS.
7. Run focused student-web tests, typecheck, and OpenSpec validation.

Rollback is straightforward: revert the component usage to `.ai-thinking-dots`, remove the Lottie dependency and asset, and restore dot-specific tests/CSS.

## Open Questions

- Has the exact downloaded `Atom.json` been licensed for bundled production use in the student app?
- Should the animation be frozen on the first frame or replaced by a static Lucide Atom icon when reduced motion is enabled?
- Is `28px`, `30px`, or `34px` the best optical size for the inline root thinking line after testing on 360px, 390px, and 430px phone widths?
