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

Tests run against the live Docker container using requests + BeautifulSoup. Use `data-*`
attributes on HTML elements to make them testable.

Commit often, in small batches.

## The pipeline

Described only by the README's generated diagram — don't restate it anywhere else.

Adding a step to a git hook? Put `# pipeline: blocks` or `# pipeline: advisory` above it.
The scan refuses to guess.
