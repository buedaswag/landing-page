"""Words either side of an inline element must stay apart.

Guard for ASTRO_MIGRATION.md box 7. Astro 7 changes the `compressHTML` default
to `'jsx'`, which drops whitespace containing a newline between elements --
so `text\\n<strong>bold</strong>\\nmore` renders as `text<strong>bold</strong>more`.
The FieldNotes posts break prose across lines like that. The bump pins
`compressHTML: true`; this is what notices if the pin goes.

`<br>` is excluded: a line break glued to the text before it is the normal case.
"""

import re
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
    # The two posts with newline-separated inline runs in their markup.
    "/blog/2026-04-16-field-notes-prompt-2026-html",
    "/blog/2026-05-12-field-notes-outputs-to-outcomes-html",
]

INLINE = r"(?:strong|em|a|code)"
GLUED = re.compile(
    rf"[A-Za-z0-9]<{INLINE}[\s>]|</{INLINE}>[A-Za-z0-9]"
)


class TestInlineWhitespace(unittest.TestCase):

    def test_no_word_is_glued_to_an_inline_element(self):
        for path in ROUTES:
            with self.subTest(route=path):
                html = requests.get(BASE_URL + path, timeout=10).text
                glued = [
                    html[max(m.start() - 25, 0):m.end() + 15]
                    for m in GLUED.finditer(html)
                ]
                self.assertEqual(
                    glued, [],
                    f"{path}: whitespace around inline elements was stripped",
                )


if __name__ == "__main__":
    unittest.main()
