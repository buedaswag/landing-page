# Landing Page

```bash
# -d (detached) starts the containers and gives you your prompt back.
# Without it, the command stays in the foreground streaming logs and only
# ends on Ctrl+C -- which also stops the site. Agents hit that as a hang:
# the tool call blocks until it times out, so the guard always adds -d.
docker compose up --build -d
```

```bash
http://localhost:4444
```

```bash
docker compose logs -f web   # follow the logs
docker compose down          # stop it
```

Draft posts are visible on localhost and hidden on the live site.

## Lean Coffee Email Signup

The lean coffee page (`/lean-coffee`) collects emails via [Supascribe](https://supascribe.com), which syncs subscribers to the Substack publication at [valuestreammapping.substack.com](https://valuestreammapping.substack.com).

**Dashboard & config:**
- Supascribe embed settings: https://supascribe.com/embed/XGvhahzgY3hvGZSrhva9
- Substack publication dashboard: https://valuestreammapping.substack.com/publish
- Export subscribers anytime from Substack: Dashboard → Settings → Exports

**To change widget styling** (colors, button text, success message), edit the embed in the [Supascribe dashboard](https://supascribe.com/embed/XGvhahzgY3hvGZSrhva9). Changes are live instantly — no code changes needed.

## Run locally

```bash
docker compose up --build -d
```

## Agent guardrails

How to work in this repo — Docker-only, TDD, small batches — is written down in
[`.cursor/rules/how-i-work.mdc`](.cursor/rules/how-i-work.mdc).

The Docker-only part is enforced rather than trusted. `scripts/claude_guard.py` is a
`PreToolUse` hook (registered in `.claude/settings.json`) that checks every Bash command an
agent proposes, statically, before the permission prompt appears:

| Command                              | What happens                                                    |
| ------------------------------------ | --------------------------------------------------------------- |
| `npm install` / `npm ci` / `npm add` | Denied — add the dep to `package.json`, Docker installs it.       |
| any other `npm` / `npx` / `astro`    | Rewritten to `docker compose up --build -d` and run.              |
| anything containing `docker`         | Untouched.                                                        |

No prompt to answer and no LLM in the loop — it's a regex table in one file. The run command at
the top of this README is the source of truth; if it changes there, change `DOCKER_UP` in the
script to match. Tests: `tests/test_claude_guard.py`.

Plans for non-trivial work go in [`.claude/plans/`](.claude/plans/), one page each.

## Install git hooks

Use git's "half-arsed-builtin" version control for git hooks (this is too verbose?)
```bash
touch .githooks/pre-push
chmod +x .githooks/pre-push
git config core.hooksPath .githooks
```

## Deployment Pipeline

```mermaid
graph LR
    subgraph local ["Local"]
        Dev["Dev server"] --> PreCommit["Pre-commit"]
        PreCommit --> Commit
        Commit --> PrePush["Pre-push"]
        PrePush --> Push
    end

    subgraph ci ["CI (parallel)"]
        Security["Security Audit"]
        Test["Build + Test"]
    end

    Deploy

    subgraph prod ["Production"]
        CDN["GitHub Pages"]
        Health["Health Check"]
    end

    Push --> Security
    Push --> Test
    Security --> Deploy
    Test --> Deploy
    Deploy --> CDN
    Health -->|"every 30 min"| CDN
```

## Migration

- **[Astro 5 → 7](ASTRO_MIGRATION.md)** — pending. Astro 5 is on an unsupported line with open critical advisories; the npm-audit gate is silenced until this lands.

## Backlog

- **Upgrade astro 5 → 7 (breaking) — the npm-audit gate is currently OFF.** Astro 5 and its transitive `sharp` have open advisories (XSS, SSRF, AVIF RCE, libvips/libheif CVEs). They have now escalated from *high* to **critical** (`GHSA-26w7-cxv4-gfx2`), so the earlier `--audit-level=critical` relaxation no longer covers them, and there is no 5.x backport — the advisory range is `astro <=7.2.7`. As a stopgap the gate is silenced, not relaxed:
  - `tests/test_security.py` — `test_npm_audit_no_high_or_higher_vulnerabilities` is `@unittest.skip`ped.
  - `.github/workflows/security.yml` and `deploy.yml` — the `npm-audit` job is `continue-on-error: true`. **This un-gates `deploy`, which `needs: npm-audit`; deploys now proceed on a failing audit.**

  Undo all three once the migration lands, and restore the level to `high`. Scope and steps: **[ASTRO_MIGRATION.md](ASTRO_MIGRATION.md)**.
- Smaller, independent win: a package.json `override` bumping `sharp` to `^0.35.4` clears the one `high` (libvips + libheif CVEs) without touching astro. Doesn't unblock the gate on its own, but this site does run images through sharp at build time.
- Pre-push waits ~60s before failing — should fail fast (shorter timeout).
- `scripts/ensure_server.py:67` failure message is useless: `Service 'web' not ready after 60s. Check: docker compose logs` tells you nothing about *why*. It should print the actual error — dump the tail of `docker compose logs web` (and the container's status/exit code) inline so `gacp` shows the real failure instead of making you go dig for it.
- Make `git push` faster (parallelize tests, skip checks CI already runs).
- `requirements.txt` hand-pins the full transitive dependency tree, so removing a direct dep (e.g. selenium) leaves orphaned sub-deps behind as dead weight and unnecessary attack surface. Fix: declare only direct deps in a `requirements.in` and generate a locked `requirements.txt` with `uv`/`pip-compile` (`--generate-hashes`), so transitive deps and version hashes are managed automatically.
- Static check on worktree size after each LLM call, wired as a `PostToolUse`/`Stop` hook. Diff size (files changed + lines) accumulates silently across an agent session until the working tree is too big to review or revert cleanly. The hook would measure `git status --porcelain` / `git diff --stat` against a threshold and fire an alert into the transcript so the agent knows it's time to commit. Natural extension, and consistent with continuous delivery: once the threshold trips, commit automatically (small, frequent, always-green commits) rather than just warning — gated on the existing pre-commit checks passing, so a red tree alerts instead of committing.
- Automate the security vulnerability scan: run it periodically (scheduled GitHub Action) and have it open — and, when checks pass, auto-merge — a PR with the fixes, à la Steve Yegge's auto-maintenance workflow for his open-source projects. Could combine Dependabot/`npm audit fix` with an agent-driven step plus auto-merge on green CI.
