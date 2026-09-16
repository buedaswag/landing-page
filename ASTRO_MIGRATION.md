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

- [ ] **4. Read the upgrade guides** — free, zero-risk, and the only
      unknown-unknown left. Findings can change every box below, so it goes first.
      - Astro 6, then Astro 7.
      - `@astrojs/mdx` 5 → 8.
      *Done when:* anything found is written into box 7 as a numbered action, and
      that edit is committed.

- [ ] **5. Make `common.css` the Tailwind entry** — one commit; the parts do not
      work alone. A bare import 500s, because `@layer base` (line 57) is only
      legal in an entry file.
      - Add `@tailwind base; @tailwind components; @tailwind utilities;` to the
        top of `common.css`.
      - Set `tailwind({ applyBaseStyles: false })` in `astro.config.mjs` so
        Tailwind is not injected twice.
      - Import `common.css` in `Layout.astro`.
      *Done when:* site returns 200, CSS back to ~45KB, the 10 red
      `test_common_css_reaches_every_page` subtests are green — **and** the visual
      delta is reviewed. This activates ~80 lines of never-shipped CSS: site-wide
      `body { color:#333 }`, table borders on `/privacy` and `FieldNotesPrompt2026`.

- [ ] **6. Pin the v4-sensitive classes** — 34 uses that render identically in v3
      and v4, so v4 cannot change them silently. Counts are a floor: static scan
      of `class="…"`, misses `class:list` and dynamic classes.
      - `border` → `border-gray-200` (18 uses; else defaults to `currentColor`).
      - `flex-shrink-0` → `shrink-0` (16 uses; removed in v4).
      *Done when:* nothing moved visually and the suite is green.
      *Not here:* `rounded` (3) and `shadow-sm` (2) are v3↔v4 scale renames —
      applying them now would change rendering. They belong in box 7.
      `space-y-*` (15) changes selector only; verify after the bump, no rewrite.

- [ ] **7. The bump** — one commit, four changes.
      1. Deps: `astro` ^7.3.2, `@astrojs/mdx` ^8.0.1, `tailwindcss` ^4,
         `@tailwindcss/typography` ^0.5.16+. Add `@tailwindcss/vite`, remove
         `@astrojs/tailwind`. Node ≥22.12 already satisfied.
      2. `astro.config.mjs`: drop `tailwind()` and the `applyBaseStyles` flag from
         box 5; add `vite: { plugins: [tailwindcss()] }`.
      3. Delete `tailwind.config.cjs` and `.mjs` — safe, both have empty
         `theme.extend`; only the typography registration matters, replaced below.
      4. `common.css`: replace the box-5 directives with `@import "tailwindcss";`
         and `@plugin "@tailwindcss/typography";` Apply the two renames from box 6.
      *Done when:* `npm run build` passes, the full suite is green, and `prose` on
      `blog/[...slug]`, tables on `/privacy`, and the cookie banner
      (`CookieBanner.astro:33`, the one `define:vars` use) all look right.

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
