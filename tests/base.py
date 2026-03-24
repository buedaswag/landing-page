import unittest

import requests
from pathlib import Path


class SiteTestCase(unittest.TestCase):
    """Base test class that ensures the site is reachable at localhost:4444.

    Fails immediately if the server is not responding.
    Use scripts/ensure_server.py to start it before running tests.
    """

    BASE_URL = "http://localhost:4444"
    PROJECT_ROOT = Path(__file__).parent.parent

    @classmethod
    def setUpClass(cls):
        try:
            response = requests.get(cls.BASE_URL, timeout=5)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Server returned {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Server not responding at {cls.BASE_URL}. "
                f"Run: python scripts/ensure_server.py"
            ) from e
