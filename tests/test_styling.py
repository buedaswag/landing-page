"""Guards that CSS actually reaches the browser on every page.

These exist for the astro 5 -> 7 migration (see ASTRO_MIGRATION.md). Today
Tailwind arrives via `@astrojs/tailwind`'s auto-injection; after the migration
it must arrive via `common.css` being imported in `Layout.astro`. Swapping the
delivery mechanism is a silent failure — the build succeeds and every other
test passes while pages ship unstyled. These tests are what make it loud.

The CSS-gathering helper handles both server modes on purpose: `astro dev`
(pre-commit) inlines styles in <style> blocks, `astro preview` (pre-push)
emits <link rel="stylesheet"> to /_astro/*.css.
"""

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from tests.base import SiteTestCase


# Every route on the site. All of them render through Layout.astro, so a
# delivery-mechanism break hits all of them at once.
PAGES = [
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

# Tailwind utilities used in the markup of every page, paired with the
# declaration they must compile to. Chosen to be stable across Tailwind 3
# and 4 so the migration doesn't have to rewrite this list.
SENTINELS = {
    "flex": "display:flex",
    "grid": "display:grid",
    "hidden": "display:none",
    "font-bold": "font-weight:700",
    "text-center": "text-align:center",
}

# A page with no CSS at all still carries Layout.astro's small :root block,
# so "styles exist" is too weak a check. Real pages ship tens of KB.
MIN_CSS_BYTES = 10_000


class StylingTestCase(SiteTestCase):

    def css_for(self, path):
        """Return all CSS the browser would apply on `path`, concatenated.

        Collects inline <style> blocks (dev server) and fetches every
        <link rel="stylesheet"> (preview server), so the same assertions
        hold in both modes.
        """
        response = requests.get(urljoin(self.BASE_URL, path), timeout=10)
        self.assertEqual(
            response.status_code, 200, f"{path} did not load"
        )
        soup = BeautifulSoup(response.text, "html.parser")

        chunks = [tag.get_text() for tag in soup.find_all("style")]

        for link in soup.find_all("link", rel="stylesheet", href=True):
            href = urljoin(urljoin(self.BASE_URL, path), link["href"])
            if not href.startswith(self.BASE_URL):
                continue  # third-party stylesheet, not ours to assert on
            sheet = requests.get(href, timeout=10)
            self.assertEqual(
                sheet.status_code, 200,
                f"{path} links stylesheet {href} which returned "
                f"{sheet.status_code}",
            )
            chunks.append(sheet.text)

        return "\n".join(chunks)

    @staticmethod
    def normalize(css):
        """Strip whitespace so dev (pretty) and preview (minified) match."""
        return re.sub(r"\s+", "", css)


class TestTailwindDelivery(StylingTestCase):

    def test_every_page_ships_substantial_css(self):
        """A page that loses its stylesheet still returns 200. Catch that."""
        for path in PAGES:
            with self.subTest(page=path):
                css = self.css_for(path)
                self.assertGreater(
                    len(css), MIN_CSS_BYTES,
                    f"{path} shipped only {len(css)} bytes of CSS — "
                    f"Tailwind is probably not reaching this page",
                )

    def test_tailwind_utilities_resolve_on_every_page(self):
        """Utilities used in the markup must compile to real rules.

        This is the guard for ASTRO_MIGRATION.md step 5. If the
        `@astrojs/tailwind` integration is removed without `common.css`
        being imported in Layout.astro, every subTest here fails.
        """
        for path in PAGES:
            with self.subTest(page=path):
                css = self.normalize(self.css_for(path))
                for utility, declaration in SENTINELS.items():
                    expected = f".{utility}{{{declaration}"
                    # assertTrue, not assertIn: assertIn would dump the whole
                    # stylesheet into the failure message.
                    self.assertTrue(
                        expected in css,
                        f"{path} uses `{utility}` but no rule compiles it "
                        f"(looked for `{expected}` in {len(css)} bytes of CSS)",
                    )

    def test_typography_plugin_is_registered(self):
        """`prose` styling drives every blog post's readability.

        Tailwind 4 registers this in CSS (`@plugin "@tailwindcss/typography"`)
        rather than in the JS config, so the migration can drop it silently.
        """
        css = self.normalize(self.css_for("/blog/2025-05-19-what-is-vsm"))
        self.assertTrue(
            ".prose" in css,
            "typography plugin output missing — blog posts lose `prose` "
            f"styling ({len(css)} bytes of CSS searched)",
        )


class TestCommonStylesheet(StylingTestCase):

    def test_common_css_reaches_every_page(self):
        """`common.css` must actually be delivered, not merely imported.

        After the migration `common.css` is the file carrying
        `@import "tailwindcss"`, so if it stops reaching a page, that page
        loses everything. `--max-width` is defined only here, which makes it
        a reliable fingerprint for "this file shipped".
        """
        for path in PAGES:
            with self.subTest(page=path):
                css = self.normalize(self.css_for(path))
                self.assertTrue(
                    "--max-width" in css,
                    f"{path} is not receiving common.css "
                    f"({len(css)} bytes of CSS, none of it from common.css)",
                )


class TestBorderPinning(StylingTestCase):
    """Guards for ASTRO_MIGRATION.md box 6.

    Tailwind 3's preflight defaults every border-color to `#e5e7eb`
    (gray-200); Tailwind 4 defaults it to `currentColor`. So bare `border`
    renders grey today and would silently turn text-coloured after the bump.
    Box 6 pins the colour ahead of the bump, while v3 and v4 still agree.

    The trap is that `border` and `border-gray-200` are disjoint utilities —
    the first sets only `border-width`, the second only `border-color`.
    Pinning by *replacing* the class removes the border. These tests are what
    make that loud, because nothing else in the suite would notice.
    """

    def test_border_utilities_stay_disjoint(self):
        """The premise of the test below. If Tailwind ever merges these two
        utilities, the pin stops being necessary and this stops being true."""
        css = self.normalize(self.css_for("/"))
        self.assertTrue(
            ".border{border-width:1px}" in css,
            "`.border` no longer compiles to just a width — re-check whether "
            "box 6's pin is still the right shape",
        )

    def test_pinned_borders_keep_their_width(self):
        """`border-gray-200` must never appear without `border` beside it.

        Colour without width is an invisible border: the element loses its
        outline and every existing test still passes.
        """
        for path in PAGES:
            with self.subTest(page=path):
                response = requests.get(
                    urljoin(self.BASE_URL, path), timeout=10
                )
                soup = BeautifulSoup(response.text, "html.parser")
                for el in soup.find_all(class_="border-gray-200"):
                    classes = el.get("class", [])
                    self.assertIn(
                        "border", classes,
                        f"{path} has an element pinned to `border-gray-200` "
                        f"with no width utility beside it, so it renders no "
                        f"border at all: class=\"{' '.join(classes)}\"",
                    )


if __name__ == "__main__":
    import unittest
    unittest.main()
