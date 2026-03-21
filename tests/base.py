import unittest
import time
import requests
from pathlib import Path


class SiteTestCase(unittest.TestCase):
    """Base test class that ensures the site is reachable at localhost:4444.

    The server must be started before running tests (via Docker, npx serve, etc.).
    """

    BASE_URL = "http://localhost:4444"
    PROJECT_ROOT = Path(__file__).parent.parent

    @classmethod
    def setUpClass(cls):
        cls._wait_for_server()

    @classmethod
    def _wait_for_server(cls, timeout=60):
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(cls.BASE_URL, timeout=2)
                if response.status_code == 200:
                    print(f"Server ready after {int(time.time() - start_time)}s")
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)

        raise RuntimeError(
            f"Server not responding at {cls.BASE_URL} after {timeout}s. "
            f"Start it first: docker compose up --build"
        )
