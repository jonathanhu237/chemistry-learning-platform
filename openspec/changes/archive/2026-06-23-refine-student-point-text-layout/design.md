## Context

The student H5 point detail page now follows a watch-page direction: a 16:10 point video player is fixed at the top of the phone viewport, while the point learning body scrolls below it. The current body already contains the required student-facing material:

- catalog path
- full experiment point title
- experiment principle, including equation-mode rows and annotations
- phenomenon explanation
- safety note
- related experiment links
- non-content actions such as AI, practice, and completion

The remaining issue is information design. In screenshots from the current page, dense text, repeated bold "补充说明" prefixes, and large colored principle areas make the body feel like a pasted document rather than a mobile video learning page. The user explicitly wants the mental model to be "YouTube": stable player above, flat scrollable content below, and related experiments as video-like recommendation blocks.

Market research used for this design:

- YouTube watch pages and chapters: player-first, title/description/chapters, related videos below; chapters add context and let learners revisit sections.
- Coursera mobile lecture transcripts and notes: mobile learners need readable text under/around video, with notes and transcript snippets that support review without hiding the video.
- Coursera unified notes: captured screenshots, highlighted transcript text, and notes become organized review material rather than undifferentiated body copy.
- Udemy new course experience: course overview, notes, Q&A, transcripts, and resources live around or under the player, but the player remains the learning anchor.
- Open edX transcripts/handouts: transcript and handout content are auxiliary learning material below the video, with accessibility and readability priorities.
- TED-Ed lessons: video is followed by structured learning tasks such as Watch, Think, Dig Deeper, and Discuss; the insight is to divide post-video material by learning purpose.

Existing constraints:

- No backend API change should be required for this refinement.
- The point detail API already returns the required fields.
- Teacher preview must render the same student-facing body while keeping preview actions disabled.
- Related point payloads currently expose titles and relation labels, but not guaranteed thumbnails.
- The page must remain phone-first and avoid card-heavy or desktop-style density.
- Completion and practice controls must not cover required learning content.

## Goals / Non-Goals

**Goals:**

- Make the text below the fixed player scannable and calm on a phone viewport.
- Preserve all required student content: full title, path, principle, phenomenon, safety note, and related links.
- Use a YouTube-like flat watch-page flow rather than a lesson-card dashboard.
- Use a Coursera-like learning-note hierarchy for actual explanatory text.
- Present the phenomenon before principle so the post-video reading flow starts from observation and then explains cause.
- Treat equation rows as structured learning notes with annotations, not as one large paragraph.
- Make related links look and behave like a vertical list of related experiment videos.
- Keep action controls visually separate from required content.

**Non-Goals:**

- Redesign the ArtPlayer chrome or the SYSU logo progress indicator.
- Add comments, social actions, likes, subscriptions, channel controls, or entertainment-platform behavior.
- Introduce transcripts, timestamps, or chapter markers before the backend has those data.
- Add a new related-point thumbnail API.
- Change teacher authoring fields or the point detail response schema.
- Change assessment, AI chat, or learning-completion business logic.

## Decisions

### Decision: Use a YouTube-like watch-page skeleton

The body should remain a single flat scroll beneath the fixed video:

```text
Fixed 16:10 video player

Path
Full title

Phenomenon explanation
Experiment principle
Safety note
Related experiment links

Actions: AI, practice, completion
```

Rationale: the user chose YouTube as the target mental model. A watch page lets the video stay primary while supporting quick scanning below. This is more appropriate than Udemy full-screen course chrome for non-fullscreen mode.

Alternative considered: a tabbed or accordion lesson page. This was rejected because it hides required information and makes the user perform extra taps for a short chemistry point detail.

### Decision: Show phenomenon before principle

After the title area, the first learning text section should answer "what did I just see?" before "why did it happen?"

Rationale: students arrive from the video. Observation is the immediate context, and principle is the explanation. This mirrors the learning sequence of watch -> notice -> explain -> caution -> continue.

Alternative considered: keep the current authored order of principle before phenomenon. This preserves data field order but is less aligned with the video-first mental model.

### Decision: Keep sections flat with dividers, not cards

Sections should use white or paper background, compact headers, measured spacing, and simple dividers. They should not become nested cards or large decorative panels.

Rationale: YouTube-style body content is a continuous scroll. Too many cards make the page feel like a dashboard and compete with the fixed player.

Alternative considered: card per content type. This is visually heavier and increases vertical waste inside a phone viewport.

### Decision: Treat equation-mode principles as rows

Equation principles should render as a list of reaction rows. Each row should contain:

- optional small row number or equivalent sequence cue
- rendered chemical equation
- annotation text directly attached to the equation

The annotation should read as explanatory body copy. Repeating a bold "补充说明：" label for every row should not be the dominant visual pattern.

Rationale: Coursera-like notes work when each fact has a clear local context. A reaction row plus its explanation is easier to scan than a large tinted paragraph.

Alternative considered: render the backend-composed principle text as one pre-wrapped paragraph. This loses row semantics and makes long equation sections hard to navigate.

### Decision: Safety is a compact caution block

Safety should remain short and visible, with a shield/caution icon and a restrained treatment such as a small accent line or light alert background. It should not dominate the page unless content length requires wrapping.

Rationale: safety must be noticed, but it is usually a concise note. A compact treatment keeps it visible without visually overpowering principle and phenomenon.

Alternative considered: make safety a large warning card. This may be useful for hazardous workflows later, but is too heavy for the current point-detail text density.

### Decision: Related links become related experiment video rows

Related experiments should render as a vertical list of video-style blocks:

- left side: 16:10 thumbnail/poster placeholder or future thumbnail
- right side: related experiment title
- secondary line: relation label or generic "相关实验"

Rationale: this matches YouTube recommendations and supports the user's decision that related links should feel like lower video recommendations.

Alternative considered: text-only buttons. This is functional but does not match the chosen watch-page model and makes the related section feel like form navigation.

### Decision: Actions are outside the content hierarchy

AI, practice, and completion actions should be visually and semantically separate from the required learning text. Fixed completion controls must not obscure related links or safety text.

Rationale: the user explicitly stated that AI and practice buttons are not content. Content should remain readable even when action controls are fixed or floating.

Alternative considered: place actions between learning sections. This interrupts reading and makes the page feel task-first rather than video-learning-first.

## Risks / Trade-offs

- Long equation lists could push phenomenon, safety, and related links far down the page -> Keep equations compact, row-based, and avoid large background blocks.
- Moving phenomenon before principle may surprise users accustomed to the current order -> Preserve clear section headings and keep all fields present.
- Related links without real thumbnails can look artificial -> Use a stable 16:10 placeholder now; later plug in thumbnail data when the API supports it.
- Fixed completion controls can overlap content near the bottom -> Ensure the scroll body has enough bottom padding and content sections remain reachable above fixed actions.
- Teacher preview may expose layout differences if preview shell sizing differs from normal H5 -> Reuse the same component styles and verify preview route.
- Overusing accent colors can recreate the current heavy-text problem -> Restrict accent backgrounds to equation rows or safety emphasis, not whole long sections.

## Migration Plan

1. Update the point detail body layout in the student H5 frontend only.
2. Keep existing API fields and route behavior unchanged.
3. Update tests to assert required section order, flat-section structure, related video-row presentation, and fixed-player/body separation.
4. Run typecheck and focused student H5 tests.
5. Build `apps/web-student` and copy the production bundle to the `chemistry-admin-web-student-1` Nginx container when implementation is requested.

Rollback is straightforward: revert the frontend layout and style changes. No database or API migration is involved.

## Open Questions

- Should the title area show a short collapsed/expanded description behavior like YouTube if titles or paths become very long?
- Should equation rows use visible numbering, subtle bullets, or no explicit sequence marker?
- Should safety use a green chemistry-note treatment or a warmer caution treatment for hazardous materials?
- Should related experiment placeholders eventually use real thumbnails from target point videos when the backend can provide them?
