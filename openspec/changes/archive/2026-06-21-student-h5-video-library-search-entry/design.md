## Context

The student H5 app now has a route-stack architecture with five first-level roots and hidden-nav detail pages. The home root is meant to be a lightweight recommendation and entry surface, not a dense tool console. The product direction from this exploration is that the app does not need a large global search bar today; it needs a focused experiment-video discovery path.

The older idea of an experiment/video tab should not return as a sixth root tab. Instead, it should become a second-level experiment video library page opened from the home entry. Learning-page tags and cards remain direct navigation into the matching chapter, experiment, or point detail routes; they must not detour through the video library. The video library can own search, browse organization, and ES-backed result grouping without making the home page feel dry.

Search intent is mostly phenomenon-driven rather than file-name-driven. Students may search for a reagent, color change, gas, precipitate, extraction layer, chapter concept, or partial experiment name. Results should take them somewhere useful in the learning route stack.

External app/platform pattern check: modern mobile navigation guidance treats tab/bottom navigation as access to a small set of top-level sections, while nested task/search/detail surfaces are opened inside the current navigation stack. X search is reached from Explore on mobile and then shows typed result filters such as posts, people, photos, and videos. This supports the product split here: keep the student app's five roots stable, place experiment-video search inside a focused collection page, and let result taps push actionable detail pages without promoting those result pages into new root categories.

## Goals / Non-Goals

**Goals:**

- Keep the home page free of a large global search bar.
- Add a home entry into a second-level experiment video library page.
- Put the search box, browse chips, filters, and results inside the video library page.
- Use Elasticsearch or an Elasticsearch-compatible backend for search.
- Index experiment-video learning documents around experiment titles, video points, observations, reagents, apparatus, phenomena tags, chapters, element families, equations, and knowledge points.
- Make every result actionable and route to a second-level learning page.
- Preserve route-stack semantics: hidden bottom navigation on the video library page and source-aware return from result pages.
- Define route/page levels by navigation role: root tabs are first-level pages; all non-tab task, collection, and detail routes are semantic second-level/detail pages even if opened from another detail page.
- Provide useful default content before any query is entered.
- Keep learning-page tag/card navigation direct to the matching learning route rather than using the video library as an intermediate page.
- Support graceful fallback when the search service is unavailable or the index is empty.

**Non-Goals:**

- Do not add a sixth bottom-nav tab.
- Do not add a large home-page all-site search box.
- Do not search unrelated admin content, teacher drafts, private media, or backend management data.
- Do not require a complete video transcript/ASR pipeline in the first version.
- Do not make learning-root tags, chapter cards, or point cards open the video library instead of their direct target route.
- Do not redesign the whole point detail page.
- Do not replace contextual AI; AI remains an explanation destination that can be opened from results.

## Decisions

### Decision 1: Home Shows An Entry, Not A Search Bar

The home root should show an experiment video library entry card, possibly with small teaser chips or examples, but it should not expose the main search input. The search input belongs inside `/video-library`.

Rationale: the home page should keep its role as a recommendation and next-action surface. A large all-site search box makes the page feel like a generic tool and blurs the app's learning path.

Alternative considered: put the search input directly at the top of home. Rejected because the app currently does not need broad global search, and search results would crowd the root page.

### Decision 2: Video Library Is A Detail Route

Add a route such as `/video-library` under the authenticated route tree. It is a second-level page with a page back control and hidden bottom navigation. In P0 it should be reachable from the home video-library entry, not from learning-page tags/cards that already have precise destinations.

Rationale: this matches the app's route-stack model. The library is a focused collection/search surface, similar to AI chat or feedback in route depth, not a first-level destination and not an intermediate router for normal learning-page selections.

Alternative considered: restore a video tab or route learning-page tags through the video library. Rejected because the current first-level model is intentionally limited to home, learn, AI, assessment, and profile, and learning selections should keep direct task navigation.

### Decision 3: Page Level Is Semantic, Not Stack Depth

Use a route-role taxonomy rather than a numeric history-depth taxonomy:

- First-level/root pages are only the bottom-nav roots: home, learn, AI, assessment, and profile.
- Second-level/detail pages are all non-root authenticated pages opened by push/navigation: video library, chapter learning detail, experiment point/video detail, AI chat detail, assessment session, assessment report, feedback, and future result-detail pages.
- A detail page may open another detail page. For example, `home -> video-library -> point-detail` is a deeper history stack, but `point-detail` is still a semantic second-level/detail page because it is not a bottom-nav root and can be opened from multiple sources.
- Specs, tasks, tests, and frontend route organization should prefer names like `root`, `tab root`, `detail`, `collection detail`, and `task/detail route` when ambiguity matters.

Rationale: this matches common app architecture and prevents a false "third-level page" category from leaking into product wording, route visibility, tests, or directory ownership. The important distinction is whether a page belongs in persistent root navigation, not how many pushes happened before it.

Alternative considered: classify pages by exact stack depth. Rejected because the same point detail can be opened from learn, home, recent learning, or video-library search, and its product role should not change based on the opening path.

### Decision 4: Search Is Experiment-Phenomenon Search

The search product should be framed as experiment-video and phenomenon discovery. Search fields should cover:

- experiment title, code, aliases, module title
- video point title and point key
- observation text and candidate point text
- reagents, apparatus, and materials
- phenomenon tags such as color change, precipitate, gas, layering, fading, heat, flame, smell, and light
- chapter IDs, element symbols, element family names, property titles, knowledge point IDs/titles
- equations and formula text where available
- optional transcript segments when a transcript source exists later

Rationale: students usually search by what they saw or what reagent was used, not by internal media IDs.

Alternative considered: search only published video metadata. Rejected because that misses the real student query shape.

### Decision 5: Result Types Are Explicit And Actionable

The search API should return typed result items grouped by action:

- `video_point`: opens point detail with experiment ID and point context.
- `experiment`: opens point detail or a future experiment-point list for the experiment.
- `chapter_experiment`: opens chapter detail with experiment content visible where supported.
- `knowledge_point`: opens chapter detail or AI chat with context.
- `ai_prompt`: opens AI chat seeded with a phenomenon/reagent/context question.

Every result must include a stable route target or enough typed data for the frontend to build one.

Rationale: passive results create a dead end. This product should behave like a learning launcher.

Alternative considered: return a flat ES hit list and render snippets. Rejected because students need jumps into learning pages, not search-engine UI.

### Decision 6: Index Adapter With Local Fallback

Introduce a backend adapter boundary for video-library search. In production-like deployments it uses Elasticsearch or an Elasticsearch-compatible service. In local/dev or disabled mode, it can fall back to a deterministic in-memory search over available experiment/video metadata.

Rationale: the feature should be testable and usable in local development without requiring an ES cluster for every frontend iteration.

Alternative considered: require ES for all environments. Rejected because it would slow local development and make route/UI tests brittle.

### Decision 7: Index Only Student-Visible Material

The indexing pipeline must only expose student-visible, active, published, or otherwise allowed experiment/video resources. Drafts, archived resources, teacher-only metadata, and unready media must not appear in search responses.

Rationale: search is another content exposure path and must honor the same privacy/publishing rules as the learning APIs.

Alternative considered: index all experiment management data and filter later in the frontend. Rejected because hidden content should not leave the backend boundary.

### Decision 8: Default Library State Is Browseable

Before a query, the video library should show useful browse modules:

- continue/recent learning if data exists
- recommended or high-value experiment videos
- phenomenon chips
- reagent chips
- chapter/element family chips
- empty-state guidance if no searchable content exists

Rationale: a blank search page feels dry, and the user explicitly wants the home to stay warm and useful.

Alternative considered: blank input-only search page. Rejected because it recreates the dry global search problem inside a second-level page.

## Risks / Trade-offs

- [Risk] Search results could expose unpublished media or teacher-only data. -> Mitigation: build the index from student-visible repository queries and test draft/unpublished exclusion.
- [Risk] ES adds deployment complexity. -> Mitigation: isolate configuration and provide a local fallback/search-disabled state.
- [Risk] Result routing can become inconsistent if each result builds URLs ad hoc. -> Mitigation: centralize result target types and frontend navigation mapping.
- [Risk] The video library can become too broad and turn into global search. -> Mitigation: keep scope limited to experiment-video learning content and reject unrelated result domains in specs/tests.
- [Risk] Chinese chemistry terms, formulas, and reagent synonyms may not tokenize well by default. -> Mitigation: normalize aliases, symbols, formula variants, and manually curated tags; choose analyzer settings deliberately.
- [Risk] No transcript data in P0 limits video-internal search. -> Mitigation: index video point metadata and candidate observations first; treat transcript search as a future enhancement.

## Migration Plan

1. Add the video-library route and home entry card.
2. Define backend search response schemas and frontend result target types.
3. Add the ES adapter/configuration with disabled/local fallback behavior.
4. Build the initial index source from student-visible experiment detail, video resource, candidate point, chapter, element, and knowledge point data.
5. Implement default browse modules and query-result grouping in the video library page.
6. Wire result clicks to existing route helpers for point detail, chapter detail, and AI chat.
7. Add direct SPA fallback tests for `/video-library`.
8. Add search API tests, result routing tests, and mobile QA coverage.

Rollback: hide/remove the home entry and video-library route while leaving the backend adapter disabled. No data migration should be required for P0.

## Open Questions

- Should P0 include a dedicated result route for a video-point list, or should experiment results open the existing point detail route directly?
- Which ES analyzer/tokenizer should be used for Chinese chemistry terms in deployment?
- Where should recent/continue-watching state come from if learning history is not yet durable enough?
- Should AI prompt results be shown as a grouped result type in P0, or only as a secondary action on video/phenomenon results?
