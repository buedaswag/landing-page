import unittest
import subprocess
import time
import requests
from pathlib import Path


class SiteTestCase(unittest.TestCase):
    """Base test class that ensures the Docker container is running.

    All test classes that need the live site should inherit from this.
    """

    BASE_URL = "http://localhost:4444"
    PROJECT_ROOT = Path(__file__).parent.parent

    @classmethod
    def setUpClass(cls):
        """Ensure Docker containers are running before tests."""
        cls._we_started_containers = False

        if cls._is_server_running():
            print("Docker Compose is already running — skipping build.")
        else:
            print("Server not running — starting Docker Compose...")
            subprocess.run(["docker", "compose", "up", "--build", "-d"], check=True)
            cls._we_started_containers = True

        cls._wait_for_server()

    @classmethod
    def tearDownClass(cls):
        """Leave containers running after tests for faster dev cycles."""
        print("Leaving containers running.")

    @classmethod
    def _is_server_running(cls):
        """Check if docker compose is already running and serving requests."""
        try:
            response = requests.get(cls.BASE_URL, timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @classmethod
    def _wait_for_server(cls, timeout=60):
        """Wait for server to be ready with up to 60 second timeout."""
        start_time = time.time()
        message_found = False
        server_responding = False

        print(f"Waiting up to {timeout} seconds for server to start...")

        while time.time() - start_time < timeout:
            # Check for startup message in logs
            if not message_found:
                result = subprocess.run(
                    ["docker", "compose", "logs"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if "localhost:4444" in result.stdout:
                    message_found = True
                    print("Found server startup message in logs!")

            # Check if server is responding
            if not server_responding:
                try:
                    response = requests.get(cls.BASE_URL, timeout=2)
                    if response.status_code == 200:
                        server_responding = True
                        print("Server is responding to HTTP requests!")
                except requests.exceptions.RequestException:
                    pass

            # If both checks passed, we're good
            if message_found and server_responding:
                print(f"Server is ready after {int(time.time() - start_time)} seconds")
                return True

            # Wait before trying again
            time.sleep(3)
            print(f"Still waiting... ({int(time.time() - start_time)}s elapsed)")

        # Final check with detailed error messages
        if not message_found:
            result = subprocess.run(
                ["docker", "compose", "logs"],
                capture_output=True,
                text=True,
                check=False,
            )
            raise RuntimeError(
                f"Server startup message not found after {timeout} seconds.\n"
                f"Expected: 'localhost:4444' in logs\n"
                f"Last 1000 chars of logs:\n{result.stdout[-1000:]}"
            )

        if not server_responding:
            raise RuntimeError(
                f"Server not responding at {cls.BASE_URL} after {timeout} seconds"
            )
