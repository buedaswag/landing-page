# This repo

How I work generally — plans, TDD, small batches, enforcing rules instead of writing them
down — is in `~/.claude/CLAUDE.md`, mirrored in `~/ws/dev-setup`. This file is only what is
true of this repo.

## Docker

Everything runs in Docker. Never install anything on the host.

- Node deps: add to `package.json` (installed via Dockerfile)
- Python test deps: add to `requirements.txt` (installed via Dockerfile with pip)

To check if a change works:

```bash
docker compose up --build -d
```

Then wait for http://localhost:4444 to respond before testing.

This is enforced, not trusted: the shared `PreToolUse` guard in `~/ws/dev-setup` reads
[`guard-rules.json`](guard-rules.json) from this repo and rewrites `npm`/`npx`/`astro` calls to
the command above, denying installs outright. See the README's "Agent guardrails".

## Tests

```bash
python -m unittest discover tests/
```

Tests in `tests/test_site.py`, run against the live Docker container using requests +
BeautifulSoup. Use `data-*` attributes on HTML elements to make them testable.

Commit often — the pre-commit hook runs the suite, so small batches mean it runs often.

## CI

GitHub Actions deploys to GitHub Pages on push to main. The pre-push hook runs the full suite;
if tests fail, the push is blocked. A Docker rebuild happens on push.
