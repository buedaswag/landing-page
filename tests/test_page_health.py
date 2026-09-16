"""Every route must actually render -- no error page, no blank shell.

Written after importing `common.css` into `Layout.astro` took the whole site to
HTTP 500 with a postcss `CssSyntaxError`. The existing suite covered that only
by accident: `base.py` pings `/` in setUpClass, and `test_all_pages_load` reads
links out of the homepage rather than fetching each page. Break one route and
the suite can still pass.

Deliberately does NOT inherit SiteTestCase. That base raises in setUpClass when
the server is unhealthy, which turns a precise "/privacy is 500" into a class
level error covering everything. Here each route fails on its own terms.
"""

import unittest

import requests

BASE_URL = "http://localhost:4444"

ROUTES = [
    "/",
    "/about",
    "/contact",
    "/privacy",
    "/workshops",
    "/workshops/intro",
    "/workshops/facilitation",
    "/lean-coffee",
    "/blog",
    "/blog/2025-05-19-what-is-vsm",
]

# Astro/Vite render failures as a served page. Some arrive as a 500, but the dev
# overlay can also come back 200 with the error only in the body, so status
# alone is not enough.
ERROR_MARKERS = (
    "CssSyntaxError",
    "[postcss]",
    "vite-error-overlay",
    "Internal server error",
    "Cannot find module",
)

# The 500 error page is a title plus a script tag -- well under this.
MIN_HTML_BYTES = 2_000


def fetch(path):
    return requests.get(BASE_URL + path, timeout=10)


class TestPageHealth(unittest.TestCase):

    def test_every_route_returns_200(self):
        for path in ROUTES:
            with self.subTest(route=path):
                response = fetch(path)
                self.assertEqual(
                    response.status_code, 200,
                    f"{path} returned {response.status_code}",
                )

    def test_no_route_serves_an_error_page(self):
        """A build error renders as a page; catch it by content, not status."""
        for path in ROUTES:
            with self.subTest(route=path):
                body = fetch(path).text
                for marker in ERROR_MARKERS:
                    self.assertNotIn(
                        marker, body,
                        f"{path} is serving an error page (found `{marker}`)",
                    )

    def test_every_route_renders_a_body(self):
        """Guards the blank-shell case: 200, no marker, but nothing rendered."""
        for path in ROUTES:
            with self.subTest(route=path):
                body = fetch(path).text
                self.assertGreater(
                    len(body), MIN_HTML_BYTES,
                    f"{path} rendered only {len(body)} bytes of HTML",
                )
                self.assertIn("</body>", body, f"{path} has no closing body tag")


if __name__ == "__main__":
    unittest.main()
