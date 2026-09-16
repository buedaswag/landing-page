"""Tests for the PreToolUse command guard.

The guard is a static regex check -- no LLM, no network -- so these run fast and
do not need the Docker container up, unlike the rest of the suite.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "scripts" / "claude_guard.py"
DOCKER_UP = "docker compose up --build -d"


def decide(command, tool_name="Bash"):
    """Run the guard the way Claude Code does: JSON on stdin, JSON on stdout."""
    payload = json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {"command": command, "description": "test"},
        }
    )
    result = subprocess.run(
        [sys.executable, str(GUARD)], input=payload, capture_output=True, text=True
    )
    assert result.returncode == 0, f"guard exited {result.returncode}: {result.stderr}"
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]


class TestDeniedCommands(unittest.TestCase):
    """Installs never happen on the host -- deps go in package.json."""

    def test_npm_install_is_denied(self):
        out = decide("npm install")
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("package.json", out["permissionDecisionReason"])

    def test_npm_install_with_package_is_denied(self):
        self.assertEqual(decide("npm install lodash")["permissionDecision"], "deny")

    def test_npm_shorthand_install_is_denied(self):
        self.assertEqual(decide("npm i lodash")["permissionDecision"], "deny")

    def test_npm_ci_is_denied(self):
        self.assertEqual(decide("npm ci")["permissionDecision"], "deny")

    def test_yarn_and_pnpm_install_are_denied(self):
        self.assertEqual(decide("yarn install")["permissionDecision"], "deny")
        self.assertEqual(decide("pnpm install")["permissionDecision"], "deny")

    def test_npm_init_is_not_mistaken_for_install(self):
        self.assertNotEqual(decide("npm init -y")["permissionDecision"], "deny")


class TestRewrittenCommands(unittest.TestCase):
    """Everything else becomes the one command the README documents."""

    def test_npm_run_build_is_rewritten(self):
        out = decide("npm run build")
        self.assertEqual(out["permissionDecision"], "allow")
        self.assertEqual(out["updatedInput"]["command"], DOCKER_UP)

    def test_rewrite_preserves_trailing_pipeline(self):
        """Was `drops`: the rewrite used to discard everything after the pipe.

        Dropping neighbours is the bug this guard was fixed for. A pipe consumes
        output rather than running after the server is up, so no readiness wait.
        """
        out = decide("npm run build 2>&1 | tail -15")
        rewritten = out["updatedInput"]["command"]
        self.assertIn(DOCKER_UP, rewritten)
        self.assertIn("| tail -15", rewritten)
        self.assertNotIn("localhost:4444", rewritten)

    def test_npm_run_dev_is_rewritten(self):
        self.assertEqual(decide("npm run dev")["updatedInput"]["command"], DOCKER_UP)

    def test_npm_start_is_rewritten(self):
        self.assertEqual(decide("npm start")["updatedInput"]["command"], DOCKER_UP)

    def test_npm_run_preview_is_rewritten(self):
        self.assertEqual(decide("npm run preview")["updatedInput"]["command"], DOCKER_UP)

    def test_npm_test_is_rewritten(self):
        self.assertEqual(decide("npm test")["updatedInput"]["command"], DOCKER_UP)

    def test_astro_build_is_rewritten(self):
        self.assertEqual(decide("npx astro build")["updatedInput"]["command"], DOCKER_UP)
        self.assertEqual(decide("astro dev")["updatedInput"]["command"], DOCKER_UP)

    def test_rewrite_is_detached(self):
        """A foreground `up` never exits and would hang the agent to its timeout."""
        self.assertIn(" -d", decide("npm run build")["updatedInput"]["command"])

    def test_rewrite_preserves_other_tool_input_fields(self):
        out = decide("npm run build")
        self.assertEqual(out["updatedInput"]["description"], "test")

    def test_rewrite_explains_itself(self):
        out = decide("npm run build")
        self.assertIn("README", out["permissionDecisionReason"])


class TestPassThrough(unittest.TestCase):
    """Anything the table does not match runs untouched."""

    def test_unrelated_command_is_untouched(self):
        self.assertIsNone(decide("git status"))

    def test_npm_inside_docker_is_untouched(self):
        self.assertIsNone(decide("docker compose run --rm web npm ci"))

    def test_npm_as_an_argument_is_untouched(self):
        self.assertIsNone(decide('grep "npm install" README.md'))

    def test_python_tests_are_untouched(self):
        self.assertIsNone(decide("python -m unittest discover tests/"))

    def test_non_bash_tools_are_untouched(self):
        self.assertIsNone(decide("npm install", tool_name="Read"))


class TestMalformedInput(unittest.TestCase):
    """A broken hook must never block the agent."""

    def test_garbage_stdin_exits_clean(self):
        result = subprocess.run(
            [sys.executable, str(GUARD)], input="not json", capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")


class TestTextIsNotCode(unittest.TestCase):
    """Text being written INTO a file is data, not a command to intercept.

    Regression: a heredoc writing ASTRO_MIGRATION.md contained the English
    phrase "PR #30 (astro 5->7)". CMD_POS treats "(" as a command position, so
    the parenthetical matched NODE_CMD, and the whole script -- including the
    `cat >` that wrote the file -- was replaced by the Docker command. The file
    was never written and the output looked like a clean build.
    """

    def test_heredoc_body_mentioning_astro_is_untouched(self):
        command = (
            "cat > NOTES.md <<'MD'\n"
            "This is exactly how PR #30 (astro 5->7) sat open looking green.\n"
            "MD\n"
            "git status --short"
        )
        self.assertIsNone(decide(command))

    def test_parenthetical_before_a_tool_name_is_untouched(self):
        self.assertIsNone(decide("echo 'upgrade (astro 5->7) is pending'"))

    def test_heredoc_body_mentioning_npm_install_is_untouched(self):
        command = "cat > NOTES.md <<'MD'\nRun npm install to set up.\nMD"
        self.assertIsNone(decide(command))

    def test_comment_mentioning_npm_is_untouched(self):
        self.assertIsNone(decide("git status  # not npm run build"))


class TestCompoundCommands(unittest.TestCase):
    """Rewrite only the offending segment; never discard its neighbours."""

    def test_compound_preserves_neighbours(self):
        out = decide("cd /app && npm run build && git status --short")
        rewritten = out["updatedInput"]["command"]
        self.assertIn("cd /app", rewritten)
        self.assertIn("docker compose up --build", rewritten)
        self.assertIn("git status --short", rewritten)

    def test_compound_containing_an_install_is_denied_entirely(self):
        """Rewriting the build half while dropping the install is the same bug."""
        out = decide("npm install lodash && npm run build")
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("package.json", out["permissionDecisionReason"])

    def test_a_following_segment_gets_a_readiness_wait(self):
        """`&&` means "after that finished", but `-d` returns immediately.

        Without a wait, the next segment races a server that is not up yet.
        """
        out = decide("npm run build && python -m unittest tests.test_site")
        rewritten = out["updatedInput"]["command"]
        self.assertIn("localhost:4444", rewritten)
        self.assertIn("python -m unittest tests.test_site", rewritten)

    def test_bare_command_needs_no_wait(self):
        """Nothing follows it, so the plain detached form stays."""
        self.assertEqual(decide("npm run build")["updatedInput"]["command"], DOCKER_UP)


if __name__ == "__main__":
    unittest.main()
