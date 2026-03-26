---
name: Board Hygiene blog post
overview: "Add the Board Hygiene Runbook as a new MDX blog post under the content collection, with the two Trello screenshots copied into `public/images/` and placed at the top of the article body. The post will use `draft: true` so it appears in local/dev builds but not on production until you publish."
todos:
  - id: copy-images
    content: Copy two Trello PNGs from Cursor assets into public/images/2026-03-24/ (trello-board-context-1.png, trello-board-context-2.png)
    status: pending
  - id: add-mdx
    content: Create src/content/posts/2026-03-24-board-hygiene-runbook.mdx — frontmatter, subtitle, horizontal rule, both images, full article body; no duplicate H1; MDX-safe angle brackets
    status: pending
  - id: optional-test-hooks
    content: "Optional: add data-post or data-section attributes for future tests (only if you want automated regression on this page)"
    status: pending
  - id: commit
    content: Commit (pre-commit runs scripts/ensure_server.py then python -m unittest discover tests/ — blocks commit if tests fail)
    status: pending
isProject: false
---

# Add Board Hygiene Runbook draft post

## Todos (checklist)

- [ ] Copy `image-483d640d-62e1-4e21-b621-b7b6f194bdf5.png` and `image-f0ac5504-6016-4493-8aa0-2ff2d8732a23.png` into `public/images/2026-03-24/` with stable names (`trello-board-context-1.png`, `trello-board-context-2.png`).
- [ ] Add `src/content/posts/2026-03-24-board-hygiene-runbook.mdx` with required frontmatter (`title`, `description`, `date`, `image`, `draft: true`).
- [ ] Body: italic tagline, `---`, both screenshots with alt text, then full runbook markdown; omit duplicate `#` title (layout supplies H1).
- [ ] Escape or rephrase `<` in sizing lines (e.g. `S (<1hr)`) so MDX compiles.
- [ ] (Optional) Add `data-*` hooks if you plan to assert this page in `tests/test_site.py` later.
- [ ] Commit — pre-commit starts the server if needed and runs the full test suite; fix failures before pushing.

## Conventions in this repo

- **Posts** live in [`src/content/posts/*.mdx`](src/content/posts) with frontmatter validated by [`src/content.config.ts`](src/content.config.ts): `title`, `description`, `date` (string), `image` (must start with `/`), optional `draft` (default false).
- **Listing and routes**: [`src/pages/blog/index.astro`](src/pages/blog/index.astro) filters out drafts unless `import.meta.env.DEV`. [`src/pages/blog/[...slug].astro`](src/pages/blog/[...slug].astro) only generates routes for non-draft posts in production, so the new URL will work in dev and after you flip `draft: false`.
- **Images**: Static files go under [`public/`](public) and are referenced as `/images/...` (see existing posts such as [`src/content/posts/2025-07-14-intro-to-vsm-resources.mdx`](src/content/posts/2025-07-14-intro-to-vsm-resources.mdx)).

## Implementation steps

1. **Add image assets to the repo**  
   Copy the two PNGs from the Cursor assets folder into a dated folder, e.g. `public/images/2026-03-24/`:
   - Source (already on your machine):
     `~/.cursor/projects/Users-migueldias-ws-personal-landing-page/assets/image-483d640d-62e1-4e21-b621-b7b6f194bdf5.png`
     `~/.cursor/projects/Users-migueldias-ws-personal-landing-page/assets/image-f0ac5504-6016-4493-8aa0-2ff2d8732a23.png`
   - Target names (readable): e.g. `trello-board-context-1.png` and `trello-board-context-2.png` (or keep original hashes if you prefer no rename).

2. **Create `src/content/posts/2026-03-24-board-hygiene-runbook.mdx`**
   - **Frontmatter**:
     - `title`: `Board Hygiene Runbook`
     - `description`: one-line summary (the italic tagline works well for SEO cards).
     - `date`: `"2026-03-24"`
     - `image`: `/images/2026-03-24/<first-screenshot>.png` (used for blog card preview).
     - `draft: true` (per your choice).
   - **Body structure**:
     - Do **not** repeat `# Board Hygiene Runbook` in the MDX body—the post template already renders `<h1>` from `title` ([`src/pages/blog/[...slug].astro`](src/pages/blog/[...slug].astro)). Start with the subtitle line `*A reference for keeping your Trello board lean, actionable, and flowing.*`, then `---`, then **both images** (markdown `![]()` or `<img alt="...">` with meaningful alt text, e.g. Trello board showing category columns vs flow), then the rest of the article exactly as provided.
   - **MDX safety**: Phrases like `S (<1hr)` contain `<` which can confuse MDX. Escape or rephrase (e.g. `S (under 1 hr)` or `S (&lt;1hr)`) wherever `<` could be parsed as JSX.

3. **Verify**
   - **Commit**: [`.githooks/pre-commit`](.githooks/pre-commit) runs `ensure_server.py` (Docker up if needed) and `python -m unittest discover tests/`. That is the main gate — no separate manual Docker checklist required for this task.
   - **Draft UX**: Optionally open `/blog` in the browser locally to confirm `DRAFT:` prefix and images; not covered by CI for drafts (see below).

## Blog coverage tests (reference)

**Do we have a test that requests every blog post?** No. [`tests/test_site.py`](tests/test_site.py) only hits specific `/blog/...` URLs where behavior matters (e.g. `test_vsm_origin_story_post_loads`, `test_marco_testimonial_cover_image_loads`, testimonial links returning 200).

**Should we add a crawler over all posts?** Optional. **Published** posts: a test that loads `/blog`, collects every `a[href^="/blog/"]` to post pages (not anchors on same page), dedupes, and `GET`s each with 200 would catch missing routes and many runtime failures. It would not run in **production CI** for **draft** posts, because production build omits draft routes — drafts only exist when the site runs with `DEV` and the index lists them.

**Drafts only?** Usually not in CI: GitHub Pages build has `draft: false` filter, so draft URLs are not generated. Validating drafts is local/dev (or a separate workflow with `DEV` / include drafts). **Astro already fails the build** if MDX for a *published* post is invalid.

## Optional follow-up (not in initial scope)

- Set `draft: false` when you want the article on GitHub Pages.
- If you want automated regression on this page later, add a `data-*` attribute in the MDX and a small test in [`tests/test_site.py`](tests/test_site.py) (project convention).
