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

Three rules keep the rewrite honest, all three learned from a real failure where
a heredoc writing ASTRO_MIGRATION.md was silently replaced by the Docker command
because the prose inside it contained "PR #30 (astro 5->7)":

  1. Text is not code. Heredoc bodies, quoted strings and comments are masked
     out before matching, so writing *about* npm never looks like running it.
  2. Rewrite the segment, not the script. Only the offending segment of a
     compound command is replaced; its neighbours survive untouched.
  3. Never drop an install. If any segment is an install, the whole command is
     denied -- rewriting one half while discarding the other is the same bug.

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

# `&&` means "after that finished", but a detached `up` returns immediately, so a
# following segment would race a server that is not serving yet. When something
# follows, block until it actually answers.
READY_WAIT = "until curl -sf localhost:4444 >/dev/null; do sleep 1; done"
DOCKER_UP_THEN_WAIT = f"{DOCKER_UP} && {READY_WAIT}"

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

# Top-level separators. Splitting on these lets us rewrite one segment and leave
# the rest of the script alone.
SEPARATOR = re.compile(r"&&|\|\||;|\n|\|")

HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def mask_data(command):
    """Blank out everything that is data, keeping length and structure intact.

    Returns a string the same length as `command` with heredoc bodies, quoted
    strings and comments replaced by spaces. Offsets still line up, so a match
    found in the mask points at the same place in the original.
    """
    chars = list(command)

    def blank(start, end):
        for i in range(start, min(end, len(chars))):
            if chars[i] != "\n":
                chars[i] = " "

    # Heredoc bodies first: they can contain quotes and #, and must not be read
    # as either. This is the case that caused the original failure.
    for match in HEREDOC.finditer(command):
        delimiter = match.group(2)
        body_start = command.find("\n", match.end())
        if body_start == -1:
            continue
        terminator = re.compile(r"^\s*" + re.escape(delimiter) + r"\s*$", re.M)
        end = terminator.search(command, body_start + 1)
        blank(body_start + 1, end.start() if end else len(command))

    masked = "".join(chars)

    # Quoted strings. `sh -c "npm run build"` is a real invocation, so a quoted
    # string used as a -c payload stays visible; everything else is data.
    def mask_quoted(match):
        preceding = masked[: match.start()].rstrip()
        if preceding.endswith("-c"):
            return match.group(0)
        body = match.group(0)
        return body[0] + " " * (len(body) - 2) + body[-1]

    masked = re.sub(r"'[^']*'", mask_quoted, masked)
    masked = re.sub(r'"[^"]*"', mask_quoted, masked)

    # Comments last -- any # inside a string or heredoc is already gone.
    masked = re.sub(r"#[^\n]*", lambda m: " " * len(m.group(0)), masked)

    return masked


# A pipe consumes the previous segment's output; `&&`, `;` and a newline are
# sequential steps that can race a server that has not finished coming up.
SEQUENTIAL = {"&&", "||", ";", "\n"}


def split_segments(masked):
    """Yield (start, end, separator_after) for each top-level segment."""
    spans = []
    start = 0
    for match in SEPARATOR.finditer(masked):
        spans.append((start, match.start(), match.group(0)))
        start = match.end()
    spans.append((start, len(masked), ""))
    return spans


def decide(command):
    """Return (decision, reason, new_command) for a Bash command, or None.

    `new_command` is only meaningful for an "allow" decision.
    """
    masked = mask_data(command)
    spans = split_segments(masked)

    to_rewrite = []
    for index, (start, end, _separator) in enumerate(spans):
        segment = masked[start:end]
        if not segment.strip():
            continue
        # Already containerised -- `docker compose run web npm ci` is exactly right.
        if "docker" in segment:
            continue
        if INSTALL.search(segment.lstrip()):
            return "deny", DENY_REASON, None
        if NODE_CMD.search(segment.lstrip()):
            to_rewrite.append((index, start, end))

    if not to_rewrite:
        return None

    # Splice the replacements into the ORIGINAL text, back to front so the
    # earlier spans keep their offsets.
    result = command
    for index, start, end in reversed(to_rewrite):
        separator_after = spans[index][2]
        follows_sequentially = separator_after in SEQUENTIAL and any(
            masked[s:e].strip() for s, e, _ in spans[index + 1:]
        )
        replacement = DOCKER_UP_THEN_WAIT if follows_sequentially else DOCKER_UP
        # Replace only the segment's content, keeping the whitespace that sits
        # against the separators -- otherwise `... && npm run build && ...`
        # splices into `...&&docker compose up...`, which is valid but unreadable.
        segment = command[start:end]
        lead = len(segment) - len(segment.lstrip())
        trail = len(segment) - len(segment.rstrip())
        result = result[:start + lead] + replacement + result[end - trail:]

    return "allow", REWRITE_REASON, result


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
    decision, reason, new_command = verdict

    output = {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }
    if decision == "allow":
        # Carry the rest of the tool input through; only the command changes.
        output["updatedInput"] = {**tool_input, "command": new_command}

    json.dump({"hookSpecificOutput": output}, sys.stdout)


if __name__ == "__main__":
    main()
