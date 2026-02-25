import json
import subprocess
import unittest
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path

from tests.base import SiteTestCase


class TestSecurity(SiteTestCase):
    """Security tests for the landing page.

    Tests CSP headers, X-Content-Type-Options, Dockerfile Node version,
    and dependency pinning in requirements.txt.
    """

    # All pages that should have security meta tags
    ALL_PAGES = [
        "/",
        "/about",
        "/contact",
        "/privacy",
        "/blog",
        "/workshops/intro",
        "/workshops/facilitation",
        "/lean-coffee",
    ]

    # --- CSP ---

    # Known sources that our CSP must allow (and nothing else)
    ALLOWED_SCRIPT_SOURCES = {
        "'self'",
        "'unsafe-inline'",
        "https://www.googletagmanager.com",
        "https://www.google-analytics.com",
        "https://js.supascribe.com",
    }

    ALLOWED_CONNECT_SOURCES = {
        "'self'",
        "https://www.google-analytics.com",
        "https://region1.google-analytics.com",
        "https://supascribe.com",
    }

    ALLOWED_FRAME_SOURCES = {
        "https://www.youtube.com",
    }

    def test_csp_meta_tag_present(self):
        """Every page must have a Content-Security-Policy meta tag."""
        for page in self.ALL_PAGES:
            with self.subTest(page=page):
                response = requests.get(f"{self.BASE_URL}{page}", timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                csp = soup.find("meta", attrs={"http-equiv": "Content-Security-Policy"})
                self.assertIsNotNone(
                    csp,
                    f"Page {page} is missing <meta http-equiv='Content-Security-Policy'>",
                )

    def test_csp_allows_only_known_script_sources(self):
        """CSP script-src must only whitelist known domains."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        csp = soup.find("meta", attrs={"http-equiv": "Content-Security-Policy"})
        self.assertIsNotNone(csp, "CSP meta tag not found")

        content = csp.get("content", "")
        script_src = self._parse_csp_directive(content, "script-src")
        self.assertIsNotNone(script_src, "CSP must include a script-src directive")

        sources = set(script_src.split())
        self.assertEqual(
            sources,
            self.ALLOWED_SCRIPT_SOURCES,
            f"script-src has unexpected sources.\n"
            f"  Expected: {self.ALLOWED_SCRIPT_SOURCES}\n"
            f"  Got:      {sources}\n"
            f"  Extra:    {sources - self.ALLOWED_SCRIPT_SOURCES}\n"
            f"  Missing:  {self.ALLOWED_SCRIPT_SOURCES - sources}",
        )

    def test_csp_allows_only_known_connect_sources(self):
        """CSP connect-src must only whitelist known domains."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        csp = soup.find("meta", attrs={"http-equiv": "Content-Security-Policy"})
        self.assertIsNotNone(csp, "CSP meta tag not found")

        content = csp.get("content", "")
        connect_src = self._parse_csp_directive(content, "connect-src")
        self.assertIsNotNone(connect_src, "CSP must include a connect-src directive")

        sources = set(connect_src.split())
        self.assertEqual(
            sources,
            self.ALLOWED_CONNECT_SOURCES,
            f"connect-src has unexpected sources.\n"
            f"  Expected: {self.ALLOWED_CONNECT_SOURCES}\n"
            f"  Got:      {sources}",
        )

    def test_csp_allows_only_known_frame_sources(self):
        """CSP frame-src must only whitelist YouTube."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        csp = soup.find("meta", attrs={"http-equiv": "Content-Security-Policy"})
        self.assertIsNotNone(csp, "CSP meta tag not found")

        content = csp.get("content", "")
        frame_src = self._parse_csp_directive(content, "frame-src")
        self.assertIsNotNone(frame_src, "CSP must include a frame-src directive")

        sources = set(frame_src.split())
        self.assertEqual(
            sources,
            self.ALLOWED_FRAME_SOURCES,
            f"frame-src has unexpected sources.\n"
            f"  Expected: {self.ALLOWED_FRAME_SOURCES}\n"
            f"  Got:      {sources}",
        )

    def test_csp_default_src_is_self(self):
        """CSP default-src must be 'self' only."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        csp = soup.find("meta", attrs={"http-equiv": "Content-Security-Policy"})
        self.assertIsNotNone(csp, "CSP meta tag not found")

        content = csp.get("content", "")
        default_src = self._parse_csp_directive(content, "default-src")
        self.assertIsNotNone(default_src, "CSP must include a default-src directive")
        self.assertEqual(default_src.strip(), "'self'", "default-src must be 'self' only")

    # --- X-Content-Type-Options ---

    def test_x_content_type_options_meta(self):
        """Every page must have X-Content-Type-Options: nosniff meta tag."""
        for page in self.ALL_PAGES:
            with self.subTest(page=page):
                response = requests.get(f"{self.BASE_URL}{page}", timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                meta = soup.find(
                    "meta",
                    attrs={
                        "http-equiv": "X-Content-Type-Options",
                        "content": "nosniff",
                    },
                )
                self.assertIsNotNone(
                    meta,
                    f"Page {page} is missing <meta http-equiv='X-Content-Type-Options' content='nosniff'>",
                )

    # --- Dockerfile Node version ---

    def test_dockerfile_uses_supported_node(self):
        """Dockerfile must use a supported (non-EOL) Node.js version (>= 20)."""
        dockerfile = self.PROJECT_ROOT / "Dockerfile"
        self.assertTrue(dockerfile.exists(), "Dockerfile not found")

        content = dockerfile.read_text()
        match = re.search(r"FROM\s+node:(\d+)", content)
        self.assertIsNotNone(match, "Could not find Node version in Dockerfile (expected FROM node:<version>)")

        node_version = int(match.group(1))
        self.assertGreaterEqual(
            node_version,
            20,
            f"Dockerfile uses Node {node_version} which is end-of-life. "
            f"Update to node:20-alpine or newer.",
        )

    # --- Requirements pinning ---

    def test_no_unpinned_critical_deps_in_requirements(self):
        """Critical packages in requirements.txt must have upper-bound version pins."""
        requirements = self.PROJECT_ROOT / "requirements.txt"
        self.assertTrue(requirements.exists(), "requirements.txt not found")

        content = requirements.read_text()

        # Packages that must have an upper bound (>= X,< Y or == X)
        critical_packages = ["requests", "urllib3", "certifi"]

        for pkg in critical_packages:
            # Find the line for this package (case-insensitive)
            pattern = re.compile(rf"^{re.escape(pkg)}\s*(.*)", re.IGNORECASE | re.MULTILINE)
            match = pattern.search(content)
            if match is None:
                continue  # Package not in requirements, skip

            version_spec = match.group(1).strip()

            # Bad: >=X.Y.Z with no upper bound
            if ">=" in version_spec and "<" not in version_spec and "==" not in version_spec:
                self.fail(
                    f"Package '{pkg}' has unbounded version '{version_spec}'. "
                    f"Add an upper bound, e.g. {pkg}>=X.Y.Z,<X+1"
                )

    # --- Secret scanning ---

    SECRETS_EXCLUDE_FILES = r"(package-lock\.json|\.min\.js$|\.secrets\.baseline)"

    def test_no_secrets_in_working_tree(self):
        """Working tree must not contain hardcoded secrets (API keys, tokens, passwords)."""
        try:
            result = subprocess.run(
                [
                    "detect-secrets", "scan",
                    "--exclude-files", self.SECRETS_EXCLUDE_FILES,
                ],
                capture_output=True,
                text=True,
                cwd=self.PROJECT_ROOT,
            )
        except (FileNotFoundError, OSError):
            self.fail(
                "detect-secrets is not installed. "
                "Install with: pip install detect-secrets"
            )

        try:
            scan = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(
                f"detect-secrets produced invalid JSON:\n{result.stdout[:500]}\n"
                f"stderr: {result.stderr[:500]}"
            )

        findings = scan.get("results", {})
        if findings:
            summary = "\n".join(
                f"  {path}: {', '.join(s['type'] + ' (line ' + str(s['line_number']) + ')' for s in secrets)}"
                for path, secrets in findings.items()
            )
            self.fail(
                f"detect-secrets found potential secrets:\n{summary}\n\n"
                f"If these are false positives, add them to a .secrets.baseline file:\n"
                f"  detect-secrets scan --exclude-files '{self.SECRETS_EXCLUDE_FILES}' > .secrets.baseline"
            )

    # --- Helpers ---

    @staticmethod
    def _parse_csp_directive(csp_content, directive):
        """Extract the value of a specific CSP directive from the full policy string.

        Returns None if the directive is not found.
        """
        # CSP directives are separated by semicolons
        for part in csp_content.split(";"):
            part = part.strip()
            if part.startswith(directive):
                # Remove the directive name, return just the sources
                return part[len(directive):].strip()
        return None


class TestDependencyAudit(unittest.TestCase):
    """Dependency vulnerability scanning — mirrors the CI security.yml jobs.

    These tests do NOT need Docker; they run against lockfiles and manifests.
    """

    PROJECT_ROOT = Path(__file__).parent.parent

    def test_npm_audit_no_moderate_or_higher_vulnerabilities(self):
        """npm audit must find zero moderate+ vulnerabilities (mirrors CI npm-audit job)."""
        result = subprocess.run(
            ["npm", "audit", "--audit-level=moderate", "--json"],
            capture_output=True,
            text=True,
            cwd=self.PROJECT_ROOT,
        )
        if result.returncode != 0:
            try:
                audit = json.loads(result.stdout)
                vulns = audit.get("vulnerabilities", {})
                summary = "\n".join(
                    f"  - {name} ({info.get('severity', '?')}): "
                    f"{', '.join(t.get('title', t) if isinstance(t, dict) else t for t in info.get('via', []))}"
                    for name, info in vulns.items()
                )
            except (json.JSONDecodeError, AttributeError):
                summary = result.stdout[:500]

            self.fail(
                f"npm audit found vulnerabilities (audit-level=moderate):\n{summary}\n\n"
                f"Run 'npm audit' for details, then 'npm audit fix' to resolve."
            )

    def test_pip_audit_no_vulnerabilities(self):
        """pip-audit must find zero vulnerabilities in requirements.txt (mirrors CI pip-audit job)."""
        requirements = self.PROJECT_ROOT / "requirements.txt"
        self.assertTrue(requirements.exists(), "requirements.txt not found")

        try:
            result = subprocess.run(
                ["pip-audit", "-r", str(requirements)],
                capture_output=True,
                text=True,
                cwd=self.PROJECT_ROOT,
            )
        except (FileNotFoundError, NotADirectoryError, OSError):
            self.fail(
                "pip-audit is not installed. "
                "Install with: pip install pip-audit"
            )

        if result.returncode != 0:
            self.fail(
                f"pip-audit found vulnerabilities in requirements.txt:\n"
                f"{result.stdout}\n{result.stderr}\n\n"
                f"Run 'pip-audit -r requirements.txt' for details."
            )


if __name__ == "__main__":
    unittest.main()
