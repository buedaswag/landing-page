#!/usr/bin/env python3
"""Ensure the dev server is running at localhost:4444.

If not responding, starts Docker Compose and waits for it.
Called by the pre-commit hook before running tests.
"""

import subprocess
import sys
import time

import requests

BASE_URL = "http://localhost:4444"
TIMEOUT = 60
POLL_INTERVAL = 3


def server_is_up():
    try:
        return requests.get(BASE_URL, timeout=2).status_code == 200
    except requests.exceptions.RequestException:
        return False


def main():
    if server_is_up():
        print("Server already responding — skipping start.")
        return 0

    print("Server not responding — starting Docker Compose...")
    result = subprocess.run(
        ["docker", "compose", "up", "-d"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"docker compose up failed:\n{result.stderr}")
        return 1

    print(f"Waiting up to {TIMEOUT}s for server...")
    start = time.time()
    while time.time() - start < TIMEOUT:
        if server_is_up():
            print(f"Server ready after {int(time.time() - start)}s")
            return 0
        time.sleep(POLL_INTERVAL)

    print(f"Server not responding after {TIMEOUT}s. Check: docker compose logs")
    return 1


if __name__ == "__main__":
    sys.exit(main())
