# Generate the pipeline diagram from the pipeline

## Problem

The gate behaviour is written down in five places:

1. `README.md:71–85` — the "Where the gates are" table
2. `README.md:90–96` — the mermaid diagram
3. `CLAUDE.md:35,39–40` — "the pre-commit hook runs the suite"
4. `.githooks/pre-commit:2–15` — 14 lines of comment over ~5 lines of code
5. `scripts/ensure_server.py:5–17,126–128` — docstring and inline comments

**One behaviour change therefore costs five edits**, each in a different file, with nothing
connecting them and nothing checking them. Miss one and it doesn't break — it just quietly
starts lying. That already happened: moving the test gate to pre-push (`6026fed`) updated
places 1, 2, 4 and 5 and missed place 3, so `CLAUDE.md:35` still claims the pre-commit hook
gates commits. It hasn't since that commit.

The fix isn't to write those five more carefully; it's to stop hand-writing them. One edit to
the pipeline should produce one edit to its description, automatically.

## Scope: keystroke to live site

The diagram covers the whole path, in five stages:

| Stage | Source scanned | Note |
|---|---|---|
| 0. Agent | `guard-rules.json` | `PreToolUse` guard rewrites commands *before* they run |
| 1. Commit | `core.hooksPath`/`pre-commit` | lockfile blocks; suite advisory |
| 2. Push | `core.hooksPath`/`pre-push` | suite blocks, against a clean preview build |
| 3. CI | `.github/workflows/deploy.yml` | 4 parallel jobs → `deploy` (`needs:` all 4) |
| 4. Live | `deploy.yml` + `health-check.yml` | Pages → migueldias.eu, polled every 30 min |

Stage 0 is named, not explained. The diagram says a guard exists and points at
`guard-rules.json`; what it rewrites is the guard's business and is already in the README.

**Scan the rules, not the registration.** The hook is registered in `~/.claude/settings.json`
and the engine lives in `~/ws/dev-setup` — both outside the repo and per-machine. Reading them
would make the output differ between machines, which breaks the drift test for anyone but the
author. `guard-rules.json` is tracked, so it's the only reproducible evidence that stage 0
exists, and its presence is what activates the engine anyway.

Known gap, accepted: the engine exits clean when it finds no rules file, so deleting
`guard-rules.json` silently removes stage 0. Not closable in the global hook without breaking
every project that has no rules. Tolerable only because the file is tracked — its removal shows
up in a diff, unlike a missing dev-setup clone.

## Approach

Two steps, deliberately separate. **The scanping is the deliverable; mermaid is just the first
renderer.**

**1. scan** — `scripts/pipeline_scan.py` walks the sources above and builds one model: a list of
stages, each with its name, source file, the commands it runs (`ensure_server.py <sub>`,
`unittest discover`, each `run:`), what it depends on (`needs:`), and whether it blocks. This
step knows about git hooks and GitHub workflows; it knows nothing about diagrams.

**2. Render** — `scripts/pipeline_diagram.py` turns that model into mermaid.

Keeping them apart matters because the scan answers questions a picture can't: *does anything
un-gated reach production?* is a graph query, not a visual. Same reason the blocking-annotation
test below reads the scan rather than the rendered text.

**Blocking is declared, not inferred.** Deciding statically whether a shell script fails its
caller means analysing `exit`, `||`, `&&` in the general case — a rabbit hole that fails
quietly, which is the exact failure mode being killed here. A hook carries the line above
the command it describes:

```sh
# pipeline: advisory   (or: pipeline: blocks)
```

**Per command, not per hook** — corrected during implementation. `pre-commit` gates on the
lockfile policy and only reports the test suite; one flag per hook cannot say that, and
picking either would restate the exact lie CLAUDE.md told. An annotation covers every
command under it until the next one, so a hook that does one thing still needs one line.

Workflows need no annotation — `continue-on-error: true` already says it declaratively.
The annotation is one hand-written fact, so it can still lie; that's what the second test is for.

## Output

Between `<!-- pipeline:start -->` / `<!-- pipeline:end -->` in `README.md`. `--check` exits
non-zero when stale; bare invocation rewrites.

README keeps the rationale prose (not derivable from code) and the CI table (GitHub owns that
YAML). It gains a line saying `CLAUDE.md` holds the agent rules and that Claude Code's own
settings add stage 0.

## Tests

`tests/test_pipeline_scan.py` — against a fixture directory, no Docker:

- **Discovery** — a hook added to the fixture's hooks dir appears in the scan.
- **Shape** — `needs:` becomes edges; `continue-on-error: true` becomes a non-blocking stage.

`tests/test_pipeline_diagram.py` — against the real repo:

- **Drift** — `--check` passes; editing a hook without regenerating fails it.
- **Annotations are true** — run the real `pre-commit` against a deliberately failing test dir,
  assert exit 0; same for `pre-push`, assert non-zero. Asserts the `# pipeline:` lines match
  what the hooks actually do. This is the claim that went stale, and the only test that guards it.

Unit-level, no Docker: point the scanner at a fixture directory.

## Docs to strip once it lands

- `CLAUDE.md:35` — cut the mechanism clause, keep "commit often, in small batches".
- `CLAUDE.md:39–40` — replace with a pointer to the diagram.
- `.githooks/pre-commit:2–15` — keep the rationale, drop the mechanism restatement.

## Not doing yet

- Parsing arbitrary shell to infer blocking. Annotation + behaviour test covers it.
- Generating the README's CI table. Duplicating GitHub-owned YAML buys nothing.
- Reading `settings.local.json`. Machine-specific and gitignored; note the gap, don't scan it.

## Open

- **PyYAML isn't in `requirements.txt`.** Needed to parse workflows properly. Add it (Docker
  installs it) rather than regexing YAML. Confirm before starting.
