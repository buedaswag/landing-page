#!/usr/bin/env python3
"""Ensure the server is running at localhost:4444.

Usage:
    python scripts/ensure_server.py pre-commit
    python scripts/ensure_server.py pre-push
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


def wait_for_server():
    print(f"Waiting up to {TIMEOUT}s for server...")
    start = time.time()
    while time.time() - start < TIMEOUT:
        if server_is_up():
            print(f"Server ready after {int(time.time() - start)}s")
            return True
        time.sleep(POLL_INTERVAL)
    print(f"Server not responding after {TIMEOUT}s. Check: docker compose logs")
    return False


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
        return False
    return True


def pre_commit():
    """Start dev server if not already running."""
    if server_is_up():
        print("Server already responding — skipping start.")
        return 0

    print("Server not responding — starting dev server...")
    if not run(["docker", "compose", "up", "-d"]):
        return 1
    return 0 if wait_for_server() else 1


def pre_push():
    """Rebuild and start preview server."""
    print("Stopping all containers...")
    run(["docker", "compose", "--profile", "preview", "down"])

    print("Building and starting preview server...")
    if not run(["docker", "compose", "--profile", "preview", "up", "--build", "-d", "preview"]):
        return 1
    return 0 if wait_for_server() else 1


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("pre-commit", "pre-push"):
        print("Usage: python scripts/ensure_server.py <pre-commit|pre-push>")
        return 1

    if sys.argv[1] == "pre-commit":
        return pre_commit()
    else:
        return pre_push()


if __name__ == "__main__":
    sys.exit(main())
