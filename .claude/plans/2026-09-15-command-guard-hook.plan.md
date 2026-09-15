# Command guard hook — stop agents running npm locally

## Problem

`How I Work` says "never run npm install locally; everything runs in Docker". Agents read it
and still ask to run `npm run build` / `npm install`. A rule in prose is a suggestion; the
agent decides whether to follow it, and I'm the one who has to say No at the prompt.

## Approach

Make it a static check instead of a prompt. A `PreToolUse` hook on `Bash` runs a regex table
over the command and either **rewrites** it to the Docker equivalent or **denies** it with the
reason. No LLM call, no keystroke — the agent's turn continues with the corrected command.

Rules live in one table in `scripts/claude_guard.py`:

The replacement is whatever the `README` documents — it is the source of truth, and the guard's
job is to route agents to the documented command, not to invent a better one.

| Command matched                                  | Action  | Result                       | Why that one                                                                 |
| ------------------------------------------------ | ------- | ---------------------------- | ----------------------------------------------------------------------------- |
| `npm install` / `npm ci` / `npm add` (+ yarn/pnpm) | deny    | "Add it to `package.json`; Docker installs it." | Nothing to rewrite to — the install is a Dockerfile layer, so the fix is a file edit the agent can make itself. |
| every other `npm` / `astro` invocation           | rewrite | `docker compose up --build`  | The one command in the `README`. Build, dev, preview — they all run inside the container anyway, so they all land here. |

Skipped when the command already contains `docker` (so `docker compose run web npm ci` passes),
and when the npm call isn't in command position (so `grep "npm install" README.md` passes).

## Tests

`tests/test_claude_guard.py` drives the script over stdin and asserts on the JSON decision —
one case per rule, plus the two skip cases. Written first, watched fail, then implemented.

## Docs

`README.md` gains an "Agent guardrails" section pointing at `How I Work`, the guard script and
`.claude/plans/`. `How I Work` gains the plans convention: one page, or the problem isn't
understood well enough yet.

## Not doing yet

`npm test`, `npm audit`, `npx` in general. Start with what actually got asked for at the
prompt; add a row when a new one shows up.

Resolved during the build: the rewrite is `docker compose up --build -d`. A foreground `up`
never exits, so an agent rewritten into it would block to its tool timeout. The `README` and
`How I Work` had drifted apart on this (`-d` in one, not the other); the `README` was the one
that moved, and the table follows it.

Still open: `web` mounts an anonymous volume over `/app/node_modules`, so `up --build` after a
`package.json` change can rebuild the image and still run the old deps. `down` first would fix
it. Not doing it until it actually bites.
