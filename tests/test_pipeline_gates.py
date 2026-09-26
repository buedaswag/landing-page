"""Prove the `# pipeline:` annotations describe what the hooks actually do.

Everything else in this feature trusts those annotations: the scanner reads
them, the diagram draws them, and a reader believes the diagram. If an
annotation is wrong, the generated documentation is wrong with more authority
than the hand-written version it replaced.

This is the test that would have caught the drift that started all of it --
CLAUDE.md claiming the pre-commit hook gated commits for weeks after it
stopped. It checks the claim, not the prose.

The hooks are run for real, with `python` stubbed on PATH. That keeps it
hermetic in the two ways that matter: no Docker rebuild, and no recursion --
these tests run *inside* pre-commit, so a hook that actually invoked the suite
would call itself forever.
"""

import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).parent.parent

# `python <anything matching KEY>` exits FAIL_CODE; everything else succeeds.
STUB = """#!/bin/sh
case "$*" in
  *{key}*) exit {code} ;;
  *) exit 0 ;;
esac
"""


class HookGateTestCase(unittest.TestCase):
    """Run a real hook with a chosen command rigged to fail."""

    def run_hook(self, hook, failing):
        """Run `.githooks/<hook>` with `python *<failing>*` failing.

        Returns the completed process so a test can assert on the exit code.
        """
        with TemporaryDirectory() as stub_dir:
            stub = Path(stub_dir) / "python"
            stub.write_text(STUB.format(key=failing, code=1))
            stub.chmod(0o755)
            return subprocess.run(
                ["sh", str(PROJECT_ROOT / ".githooks" / hook)],
                cwd=PROJECT_ROOT,
                env={"PATH": f"{stub_dir}:/usr/bin:/bin", "HOME": str(Path.home())},
                capture_output=True,
                text=True,
                timeout=60,
            )


class TestPreCommitGates(HookGateTestCase):
    """`.githooks/pre-commit` — one gate, one report."""

    def test_a_failing_suite_does_not_block_the_commit(self):
        """`# pipeline: advisory` on the unittest line.

        A commit is a local save point; blocking it grew the worktree without
        catching anything pre-push and CI didn't already catch.
        """
        result = self.run_hook("pre-commit", failing="unittest")
        self.assertEqual(
            result.returncode, 0,
            "pre-commit is annotated `advisory` for the test suite but exited "
            f"{result.returncode} when the suite failed.\n{result.stdout[-400:]}",
        )

    def test_a_failing_suite_still_says_so(self):
        """Advisory must not mean silent, or the banner becomes wallpaper."""
        result = self.run_hook("pre-commit", failing="unittest")
        self.assertIn("PUSH WILL BLOCK", result.stdout)

    def test_the_lockfile_check_does_block_the_commit(self):
        """`# pipeline: blocks` on the ensure_server line."""
        result = self.run_hook("pre-commit", failing="ensure_server")
        self.assertNotEqual(
            result.returncode, 0,
            "pre-commit is annotated `blocks` for ensure_server.py but exited "
            "0 when it failed.",
        )


class TestPrePushGates(HookGateTestCase):
    """`.githooks/pre-push` — the release boundary, so everything gates."""

    def test_a_failing_suite_blocks_the_push(self):
        result = self.run_hook("pre-push", failing="unittest")
        self.assertNotEqual(
            result.returncode, 0,
            "pre-push is annotated `blocks` for the test suite but exited 0 "
            "when the suite failed. deploy.yml fires on push to main, so this "
            "is the gate standing between a red suite and production.",
        )

    def test_a_failing_preview_build_blocks_the_push(self):
        result = self.run_hook("pre-push", failing="ensure_server")
        self.assertNotEqual(result.returncode, 0)


class TestAnnotationsMatchTheScan(HookGateTestCase):
    """Tie the two together: what the scanner reports is what the hook does.

    Without this, the tests above could pass while the scanner read the
    annotations wrongly, and the diagram would still lie.
    """

    def test_scanned_gating_agrees_with_observed_gating(self):
        from scripts.pipeline_scan import scan

        stages = {s.name: s for s in scan(PROJECT_ROOT)}
        for hook, failing in [
            ("pre-commit", "unittest"),
            ("pre-commit", "ensure_server"),
            ("pre-push", "unittest"),
        ]:
            with self.subTest(hook=hook, failing=failing):
                scanned = next(
                    step.blocks
                    for step in stages[hook].steps
                    if failing in step.command
                )
                observed = self.run_hook(hook, failing).returncode != 0
                self.assertEqual(
                    scanned, observed,
                    f"{hook} is scanned as "
                    f"{'blocks' if scanned else 'advisory'} for `{failing}` "
                    f"but actually {'blocked' if observed else 'did not block'}.",
                )


if __name__ == "__main__":
    unittest.main()
