# Astro Migration: 5 → 7

**From** `astro@5.17.2` · **To** `astro@7.3.2` · Scanned 2026-09-12 · Replanned 2026-09-15

Motivation: astro 5 has open **critical** advisories (AVIF RCE `GHSA-26w7-cxv4-gfx2`, XSS, SSRF) with no 5.x backport — the advisory range is `astro <=7.2.7`. The npm-audit gate is silenced until this lands (see README backlog).

## Version targets

| Package | From | To | Note |
|---|---|---|---|
| `astro` | ^5.17.2 | ^7.3.2 | **skips major 6** — read both upgrade guides |
| `@astrojs/mdx` | ^4.0.0 | ^8.0.1 | **four majors** (5, 6, 7, 8); peers `astro ^7.2.6` |
| `@astrojs/tailwind` | ^5.1.0 | **removed** | EOL at v6, peers `astro ^3\|\|^4\|\|^5` |
| `tailwindcss` | ^3.4.1 | ^4 | + `@tailwindcss/vite` |
| `@tailwindcss/typography` | ^0.5.10 | ^0.5.16+ | registered in CSS, not JS |

Node ≥22.12 required — already satisfied (Node 22 in CI and Dockerfile).

## The actual risk profile

Every serious failure mode here is **silent**: the build succeeds, the test suite
passes, and the site renders wrong. Measured, not assumed — with Tailwind
deliberately unhooked, `test_site.py` passed all 51 of its tests against a
completely unstyled site.

Two independent silent risks, not one:

- **Delivery** — Tailwind currently arrives via `@astrojs/tailwind`'s
  auto-injection. After the migration it must arrive via `common.css` being
  imported in `Layout.astro`. Nothing fails loudly if it doesn't.
- **Semantics** — 54 class uses in `src/` change meaning under Tailwind 4.
  Same class, different rendering, no error.

| Class | Uses | Change in v4 |
|---|---|---|
| `border` | 18 | default color `gray-200` → `currentColor` (light borders turn dark) |
| `flex-shrink-0` | 16 | removed; renamed to `shrink-0` (elements start shrinking) |
| `space-y-*` | 15 | selector changed to `:not([hidden]) ~ *` |
| `rounded` | 3 | scale renamed → `rounded-sm` |
| `shadow-sm` | 2 | scale renamed → `shadow-xs` |

## Ordering principle

Two rules, both learned by getting them wrong:

1. **Anything verifiable under astro 5 happens before the bump.** Each of those is
   an ordinary reviewable diff with a working site on both sides.
2. **What's left is atomic.** The old plan said "do one step at a time, build and
   eyeball between each" — impossible. The moment the `tailwind()` integration is
   dropped, the site is unstyled until `common.css` is imported. There is no
   eyeball-able state in between. Those steps are one commit.

## Phase 0 — pre-bump, under astro 5 (incremental, independently verifiable)

- [x] **0.1 Styling guard tests** — `tests/test_styling.py`. Asserts that Tailwind
      utilities used in the markup compile to real rules, on all 10 routes, in
      both dev (inline `<style>`) and preview (`<link rel=stylesheet>`) modes.
      Verified to fire: 31 failures against a deliberately broken site.
- [x] **0.2 Delete dead `BlogLayout.astro`** — referenced by nothing in the repo.
      It was the only importer of `common.css`, which made the old plan's
      blog / non-blog distinction misleading: *all 10 pages* route through
      `Layout.astro`, so `common.css` currently reaches **no page at all**.
- [ ] **0.3 Wire up `common.css`** — import it in `Layout.astro`. This is the old
      step 5, pulled forward. **Not a no-op**: it activates ~80 lines of CSS that
      have never shipped — a site-wide `body { color:#333; font-family:… }` and
      global `:where(table)` / `main table` border rules landing on `/privacy` and
      `FieldNotesPrompt2026`. Review that visual delta on its own, and confirm
      `@apply` still resolves in the build.
      Turns `test_common_css_reaches_every_page` (currently red by design) green.
- [ ] **0.4 Make v4-sensitive classes explicit** — rewrite the 54 uses above into
      forms that render identically in v3 and v4 (`flex-shrink-0` → `shrink-0`,
      bare `border` → `border-gray-200`). Land under v3, confirm nothing moves,
      and v4 can no longer change them silently.
- [ ] **0.5 Read the upgrade guides** — astro 6 *and* 7, `@astrojs/mdx` 5→8. The
      jump spans five majors across two packages and this plan has no line-item
      for what they contain. Fold anything found into Phase 1.

## Phase 1 — the bump (one atomic commit)

1. **Deps** — bump the table above; add `@tailwindcss/vite`, remove `@astrojs/tailwind`.
2. **`astro.config.mjs`** — drop the `tailwind()` integration, add `vite: { plugins: [tailwindcss()] }`.
3. **Delete `tailwind.config.cjs` and `tailwind.config.mjs`.** Safe: both have an
   empty `theme.extend`; the only live content is the typography plugin
   registration, which step 4 replaces. (Only `.cjs` is wired up today.)
4. **`src/styles/common.css`** — add at the top:
   ```css
   @import "tailwindcss";
   @plugin "@tailwindcss/typography";
   ```

## Phase 2 — verify

`npm run build`, then the full suite (`test_site.py` is 51; plus
`test_styling.py`, `test_security.py`, `test_claude_guard.py`), then eyeball
`prose` rendering on `blog/[...slug]`, `privacy`, and the `define:vars` cookie
banner.

## What does NOT need changing

- **Content collections** — `src/content.config.ts` already uses the Content Layer API (`glob` from `astro/loaders`). Carries over unchanged.
- **Advisory surface** — the site uses no View Transitions, no server islands, no `astro:assets` / `<Image>`, no spread props. Most of the astro 5 CVEs don't apply here; the upgrade is about getting off an unsupported line, not patching live exploits.
- **`define:vars`** — one use, `src/components/CookieBanner.astro:33`. Astro 7 tightens escaping; behaviour should be identical, but it's the one spot to smoke-test.
- **`@apply`** — 3 uses in `common.css` (lines 63, 73, 79). Still supported in Tailwind 4.

## Related

- **Close the 14 open Dependabot PRs** — every open PR on this repo is Dependabot's, spanning #1 (2026-02-13) to #30 (2026-09-09). All are stale against current `main`, and the astro one (#30) is actively wrong. Dependabot reopens what still matters on its next run: `gh pr list --state open --json number -q '.[].number' | xargs -n1 gh pr close`
- We should also run the full pipeline on Dependabot PRs and auto-merge them when it passes — today only `security.yml` runs on `pull_request`, so PRs are never built or tested, which is exactly how PR #30 (astro 5→7) sat open looking green while bumping `astro` alone and leaving `@astrojs/mdx` and `@astrojs/tailwind` pinned to astro-5-only versions.
