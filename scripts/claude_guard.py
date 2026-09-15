#!/usr/bin/env python3
"""PreToolUse guard: keep npm off the host.

`How I Work` says everything runs in Docker, but prose is a suggestion -- agents
read it and still ask to run `npm run build`, and someone has to say No at the
permission prompt. This makes it a static check instead.

Claude Code pipes the pending Bash command here as JSON before the prompt is
shown. We match it against RULES and print one of three decisions:

    nothing   the command was not matched; it runs untouched
    deny      with a reason the agent can act on (edit package.json)
    allow     carrying `updatedInput` -- a rewritten command, which is what runs

The rewrite path is the point: no prompt appears, the documented Docker command
runs instead, and the agent's turn continues. No LLM in the loop.

The replacement is whatever the README documents. When the README changes, change
DOCKER_UP to match -- the README is the source of truth, not this file.

Wired up in `.claude/settings.json`. Tests in `tests/test_claude_guard.py`.
"""

import json
import re
import sys

# `-d` is not optional here: a foreground `up` streams logs and never exits, so an
# agent rewritten into it blocks until its tool timeout and learns nothing. Detached
# returns immediately and the agent can poll http://localhost:4444 for readiness.
DOCKER_UP = "docker compose up --build -d"

REWRITE_REASON = (
    f"Blocked by scripts/claude_guard.py: this repo builds and runs in Docker only. "
    f"Rewritten to the command in the README: `{DOCKER_UP}`. See .cursor/rules/how-i-work.mdc."
)

DENY_REASON = (
    "Blocked by scripts/claude_guard.py: never install packages on the host. "
    "Add the dependency to package.json (or requirements.txt for Python) and let the "
    f"Dockerfile install it on the next `{DOCKER_UP}`. See .cursor/rules/how-i-work.mdc."
)

# A command only counts when it sits in command position -- start of the line, or
# right after a separator. Keeps `grep "npm install" README.md` from matching.
CMD_POS = r"(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+|\bsh\s+-c\s+['\"]?)"

# `npm i` is install, `npm init` is not -- \b after the alternation handles that.
INSTALL = re.compile(CMD_POS + r"(?:npm|yarn|pnpm)\s+(?:install|i|ci|add)\b")
NODE_CMD = re.compile(CMD_POS + r"(?:npm|npx|yarn|pnpm|astro)\b")


def decide(command):
    """Return (decision, reason) for a Bash command, or None to leave it alone."""
    # Already containerised -- `docker compose run web npm ci` is exactly right.
    if "docker" in command:
        return None
    if INSTALL.search(command):
        return "deny", DENY_REASON
    if NODE_CMD.search(command):
        return "allow", REWRITE_REASON
    return None


def main():
    try:
        payload = json.load(sys.stdin)
        tool_input = payload["tool_input"]
        command = tool_input["command"]
        if payload["tool_name"] != "Bash":
            return
    except (json.JSONDecodeError, KeyError, TypeError):
        # A broken guard must never block the agent: say nothing, exit clean.
        return

    verdict = decide(command)
    if verdict is None:
        return
    decision, reason = verdict

    output = {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }
    if decision == "allow":
        # Carry the rest of the tool input through; only the command changes.
        output["updatedInput"] = {**tool_input, "command": DOCKER_UP}

    json.dump({"hookSpecificOutput": output}, sys.stdout)


if __name__ == "__main__":
    main()
