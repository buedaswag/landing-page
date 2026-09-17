# Astro Migration: 5 → 7

Astro 5 has open critical advisories with no 5.x backport. The npm-audit gate is
silenced until this lands.

**One ticked box = one commit.** Where work cannot be split without breaking the
site, it is one box with several actions inside. Updated 2026-09-16.

**Rules:** anything verifiable under astro 5 happens before the bump. The bump
itself is atomic — dropping `tailwind()` leaves the site unstyled until
`common.css` is imported, so there is no working state in between.

---

- [x] **1. Styling guards** — `tests/test_styling.py`. Tailwind utilities used in
      the markup must compile to real rules, all 10 routes, dev and preview.

- [x] **2. Delete dead `BlogLayout.astro`** — it was `common.css`'s only importer,
      so `common.css` reaches **no page** today. All 10 routes use `Layout.astro`.

- [x] **3. Per-route health tests** — `tests/test_page_health.py`. Every route
      renders, no error page, no blank shell; previously only `/` was checked.

- [x] **4. Read the upgrade guides** — Astro 6, Astro 7, `@astrojs/mdx` 5 → 8.
      Four findings apply; they are actions 5–8 in box 7. Everything else in
      those guides misses this repo: no adapter, no View Transitions, no
      `Astro.glob`, no `src/fetch.ts`, no remark/rehype/recma plugins, no
      Container API, no `@astrojs/db`, no i18n, no images through `astro:assets`.
      Node 25.6.1 clears the ≥22.12 floor, and `content.config.ts` is already in
      the v5 shape (new path, `loader`, no `type:`), so the Content Layer
      migration v6 forces on legacy collections is a no-op here.

- [x] **5. Make `common.css` the Tailwind entry** — directives at the top of
      `common.css`, `tailwind({ applyBaseStyles: false })`, imported in
      `Layout.astro`. All 10 subtests green, shared bundle 34KB (the ~45KB
      estimate was high), suite green against a clean preview build.
      The visual delta was one real regression, caught only by reading computed
      styles — screenshots missed it. `FieldNotesPrompt2026`'s `.pain-table` is
      ruled by horizontal lines alone and declares only `border-bottom`, so the
      newly-live `article th, article td { border: 2px solid #333 }` shorthand
      painted the other three sides; the component now says `border: 0` before
      re-declaring the edge it wants. `/privacy` has no table — the plan was
      wrong about that. The markdown tables that these rules were written for
      are in `goldratt-evaporating-cloud` and `consulting-market-strategy`.

- [ ] **6. Pin the v4-sensitive classes** — 34 uses that render identically in v3
      and v4, so v4 cannot change them silently. Counts are a floor: static scan
      of `class="…"`, misses `class:list` and dynamic classes.
      - `border` → `border-gray-200` (18 uses; else defaults to `currentColor`).
      - `flex-shrink-0` → `shrink-0` (16 uses; removed in v4).
      *Done when:* nothing moved visually and the suite is green.
      *Not here:* `rounded` (3) and `shadow-sm` (2) are v3↔v4 scale renames —
      applying them now would change rendering. They belong in box 7.
      `space-y-*` (15) changes selector only; verify after the bump, no rewrite.

- [ ] **7. The bump** — one commit, eight changes. 5–8 come from box 4.
      1. Deps: `astro` ^7.3.2, `@astrojs/mdx` ^8.0.1, `tailwindcss` ^4,
         `@tailwindcss/typography` ^0.5.16+. Add `@tailwindcss/vite`, remove
         `@astrojs/tailwind`. Node ≥22.12 already satisfied.
      2. `astro.config.mjs`: drop `tailwind()` and the `applyBaseStyles` flag from
         box 5; add `vite: { plugins: [tailwindcss()] }`.
      3. Delete `tailwind.config.cjs` and `.mjs` — safe, both have empty
         `theme.extend`; only the typography registration matters, replaced below.
      4. `common.css`: replace the box-5 directives with `@import "tailwindcss";`
         and `@plugin "@tailwindcss/typography";` Apply the two renames from box 6.
      5. `src/content.config.ts:1`: `z` is no longer exported from
         `astro:content` — `import { z } from 'astro/zod'`. The schema itself is
         Zod-4 clean: `.startsWith('/')` survives, and the two
         `.optional().default(false)` defaults already match their output type.
      6. `astro.config.mjs`: set `compressHTML: true`. The v7 default becomes
         `'jsx'`, which strips whitespace between inline elements — this repo is
         dense with `<strong>`/`<em>`/`<br>` runs inside prose, so keep the old
         behaviour in the bump and change it deliberately later, if ever.
      7. Nothing to do for the Rust compiler, recorded so it isn't re-argued: it
         errors on unclosed non-void tags instead of repairing them, and a
         tag-balance scan of all 20 `.astro` files is clean. The `<br>` runs in
         the two FieldNotes components are void elements and stay legal.
      8. Nothing to do for Sätteri either. It replaces remark/rehype as the
         default Markdown pipeline and `@astrojs/mdx` 8 needs no config change,
         but no plugins are configured for it to drop — so the risk is silent
         rendering drift across the 41 `.mdx` posts, not a build break.
      *Done when:* `npm run build` passes, the full suite is green, and `prose` on
      `blog/[...slug]`, tables on `/privacy`, and the cookie banner
      (`CookieBanner.astro:33`, the one `define:vars` use) all look right.
      *Watch:* v6 renders styles in declaration order rather than reversed, so
      confirm `Layout.astro`'s `is:global` `:root` block still wins over the
      `common.css` box 5 imports above it.

---

## Notes

- **A green suite meant nothing here.** With Tailwind unhooked, `test_site.py`
  passed all 51 tests against a completely unstyled site. Boxes 1 and 3 exist to
  close that; don't trust green without them.
- **Content collections** carry over unchanged. No View Transitions, server
  islands, `astro:assets` or spread props, so most astro 5 CVEs don't apply —
  this is about leaving an unsupported line, not patching live exploits.
- **Dependabot**: 14 stale open PRs, #30 actively wrong. PRs are never built or
  tested (only `security.yml` runs on `pull_request`), which is how #30 sat green.
  `gh pr list --state open --json number -q '.[].number' | xargs -n1 gh pr close`
