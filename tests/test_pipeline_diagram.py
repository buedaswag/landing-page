"""The README's pipeline diagram must match the pipeline it describes.

A generated diagram is only worth more than a hand-written one if something
notices when it stops matching. That is what `--check` is for, and what
`.githooks/pre-commit` runs it for.

These tests are about the *renderer*; whether the underlying model is true to
the hooks is `test_pipeline_gates.py`'s job.
"""

import re
import unittest
from dataclasses import replace
from pathlib import Path

from scripts.pipeline_diagram import END, START, main, render
from scripts.pipeline_scan import Group, Stage, Step, scan

PROJECT_ROOT = Path(__file__).parent.parent
README = PROJECT_ROOT / "README.md"


class TestDiagramIsCurrent(unittest.TestCase):

    def test_readme_matches_the_pipeline(self):
        """The whole point. Change a hook, regenerate, or this fails.

            python scripts/pipeline_diagram.py
        """
        self.assertEqual(
            main(["--check"]), 0,
            "README.md's diagram no longer matches the hooks and workflows. "
            "Run `python scripts/pipeline_diagram.py` and commit the result.",
        )

    def test_markers_are_present(self):
        text = README.read_text()
        self.assertIn(START, text)
        self.assertIn(END, text)

    def test_check_notices_a_changed_pipeline(self):
        """Proof the check isn't vacuous: perturb the model, lose the match."""
        current = render(scan(PROJECT_ROOT))
        perturbed = render(scan(PROJECT_ROOT) + [
            Stage(
                name="new-gate",
                group=Group.COMMIT,
                source=".githooks/new-gate",
                steps=[Step(command="echo hi", blocks=True)],
            )
        ])
        self.assertNotEqual(current, perturbed)
        self.assertNotIn(perturbed, README.read_text())


class TestRendering(unittest.TestCase):
    """Things that make the diagram wrong rather than merely ugly."""

    def setUp(self):
        self.stages = scan(PROJECT_ROOT)
        self.diagram = render(self.stages)

    def test_every_stage_appears(self):
        for stage in self.stages:
            with self.subTest(stage=stage.key):
                self.assertIn(stage.name, self.diagram)

    def test_node_ids_are_unique(self):
        """`npm-audit` is defined in both workflows.

        Mermaid silently merges two nodes that share an id, which would draw
        the pull-request audit and the deploy-gating audit as one box.
        """
        ids = re.findall(r"^\s+([A-Za-z0-9_]+)\[", self.diagram, re.MULTILINE)
        self.assertEqual(sorted(ids), sorted(set(ids)))

    def test_mermaid_control_characters_are_escaped(self):
        """Real commands contain `"`, `|` and braces; raw, they break the graph.

        `health-check` runs `curl --write-out "%{http_code}"`, which has all
        three.
        """
        for label in re.findall(r'\["(.*?)"\]', self.diagram):
            with self.subTest(label=label[:40]):
                for char in '"|{}':
                    self.assertNotIn(char, label)

    def test_non_blocking_stages_are_marked(self):
        """`npm-audit` is `continue-on-error`, and the diagram must show it."""
        reporting = [s for s in self.stages if not s.blocks]
        self.assertTrue(reporting, "expected at least one reporting stage")
        for stage in reporting:
            with self.subTest(stage=stage.key):
                self.assertIn("reports, does not block", self.diagram)

    def test_the_deploy_reaches_the_live_site(self):
        deploying = [s for s in self.stages if s.deploys]
        self.assertEqual(len(deploying), 1, "expected exactly one deploy stage")
        self.assertRegex(self.diagram, rf"{deploying[0].key.replace(':', '_').replace('-', '_')} --> live")

    def test_needs_are_drawn_within_their_own_workflow(self):
        """`needs: [npm-audit]` in deploy.yml must not point at security.yml."""
        self.assertIn("deploy_npm_audit --> deploy_deploy", self.diagram)
        self.assertNotIn("security_npm_audit --> deploy_deploy", self.diagram)


if __name__ == "__main__":
    unittest.main()
