# Legacy Competition Profile

The legacy branch treats the old competition profile as the canonical product line:

- `apps/web-student`: student experiment-video learning frontend.
- `apps/web-teacher`: teacher teaching-management frontend.

The two frontends share the same backend, database, catalog, video resources, question bank, assessment sessions, mastery records, and analytics records. They are not a seed fork and must not introduce old-only runtime ids.

The product narrative centers:

- experiment knowledge navigation;
- AI-assisted objective question creation;
- teacher review before publication;
- BKT mastery tracking;
- personalized experiment-video recommendation;
- smart assessment composition;
- teacher learning-score review.

The visible UI uses SYSU red branding and official SYSU logo assets copied into each frontend's `public/assets` directory. The source material is the local official asset package at `E:\迅雷下载\sysu-logo-main`, but builds must use repository-managed copies only.

Default Compose services:

- `web-student`, default endpoint `127.0.0.1:15176`;
- `web-teacher`, default endpoint `127.0.0.1:15177`;
- `backend`, default endpoint `127.0.0.1:18000`.

Use `python scripts/deploy_compose_stack.py` or `python scripts/validate_compose_stack.py --build` for the legacy runtime. The standalone token-based operations frontend is not part of this branch.
