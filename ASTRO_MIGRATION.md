# Astro Migration: 5 → 7

**From** `astro@5.17.2` · **To** `astro@7.3.2` · Scanned 2026-09-12

Motivation: astro 5 has open **critical** advisories (AVIF RCE `GHSA-26w7-cxv4-gfx2`, XSS, SSRF) with no 5.x backport — the advisory range is `astro <=7.2.7`. The npm-audit gate is silenced until this lands (see README backlog).

## Version targets

| Package | From | To | Note |
|---|---|---|---|
| `astro` | ^5.17.2 | ^7.3.2 | |
| `@astrojs/mdx` | ^4.0.0 | ^8.0.1 | peers `astro ^7.2.6` |
| `@astrojs/tailwind` | ^5.1.0 | **removed** | EOL at v6, peers `astro ^3\|\|^4\|\|^5` |
| `tailwindcss` | ^3.4.1 | ^4 | + `@tailwindcss/vite` |
| `@tailwindcss/typography` | ^0.5.10 | ^0.5.16+ | registered in CSS, not JS |

Node ≥22.12 required — already satisfied (Node 22 in CI and Dockerfile).

## Steps

1. **Deps** — bump the table above; add `@tailwindcss/vite`, remove `@astrojs/tailwind`.
2. **`astro.config.mjs`** — drop the `tailwind()` integration, add `vite: { plugins: [tailwindcss()] }`.
3. **Delete `tailwind.config.cjs` and `tailwind.config.mjs`.** Tailwind 4 is CSS-first. (Both exist today; only `.cjs` is live — the `.mjs` is dead weight and has no typography plugin.)
4. **`src/styles/common.css`** — add at the top:
   ```css
   @import "tailwindcss";
   @plugin "@tailwindcss/typography";
   ```
5. **⚠ Import `common.css` in `src/layouts/Layout.astro`.** It currently imports **no CSS** — every non-blog page (`index`, `about`, `contact`, `workshops/*`, `privacy`) gets Tailwind only from `@astrojs/tailwind`'s auto-injection. Remove that integration without this step and those pages ship unstyled. **This is the most likely way the migration silently breaks.**
6. **Verify** — `npm run build`, then the 62-test suite, then eyeball `prose` rendering on `blog/[...slug]`, `privacy`, and `common.css`.

## What does NOT need changing

- **Content collections** — `src/content.config.ts` already uses the Content Layer API (`glob` from `astro/loaders`). Carries over unchanged.
- **Advisory surface** — the site uses no View Transitions, no server islands, no `astro:assets` / `<Image>`, no spread props. Most of the astro 5 CVEs don't apply here; the upgrade is about getting off an unsupported line, not patching live exploits.
- **`define:vars`** — one use, `src/components/CookieBanner.astro:33`. Astro 7 tightens escaping; behaviour should be identical, but it's the one spot to smoke-test.
- **`@apply`** — 3 uses in `common.css` (lines 63, 73, 79). Still supported in Tailwind 4.

## Approach

Incremental. Do one step at a time, build and eyeball locally between each — the failure mode here is silent (step 5 breaks styling without failing the build or the tests). **When a visual check catches something, write the automated test for it before moving on**, so the suite ends the migration stronger than it started. That test coverage is the real deliverable; the version bump is the easy part.

## Related

- **Close the 14 open Dependabot PRs** — every open PR on this repo is Dependabot's, spanning #1 (2026-02-13) to #30 (2026-09-09). All are stale against current `main`, and the astro one (#30) is actively wrong. Dependabot reopens what still matters on its next run: `gh pr list --state open --json number -q '.[].number' | xargs -n1 gh pr close`
- We should also run the full pipeline on Dependabot PRs and auto-merge them when it passes — today only `security.yml` runs on `pull_request`, so PRs are never built or tested, which is exactly how PR #30 (astro 5→7) sat open looking green while bumping `astro` alone and leaving `@astrojs/mdx` and `@astrojs/tailwind` pinned to astro-5-only versions.
