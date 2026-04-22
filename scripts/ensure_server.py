#!/usr/bin/env python3
"""Single source of truth for docker lifecycle around the dev/preview server.

Subcommands:
    pre-commit   Ensure compose `web` is running + serving, run npm audit fix,
                 block if package(-lock).json changed, show remaining vulns.
    pre-push     Rebuild and start compose `preview` cleanly.
    post-push    Switch back to dev mode (preview down, web up). Designed to
                 be called from the pre-push hook's EXIT trap so it runs even
                 when tests fail or the hook is interrupted.

Readiness is gated on BOTH `docker compose ps` reporting the service as
running AND an HTTP 200 at localhost:4444. A stray host `astro dev` on :4444
can satisfy the HTTP check alone, so the compose-status gate is what prevents
tests from hitting the wrong listener. When `docker compose up` fails with
"address already in use", we kill whatever is on :4444 and retry once.
"""

import subprocess
import sys
import time

import requests

BASE_URL = "http://localhost:4444"
PORT = 4444
TIMEOUT = 60


def sh(cmd):
    """Run a command, capture output, never raise."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(cmd, 127, "", str(exc))


def service_running(service):
    r = sh(["docker", "compose", "ps", "--services", "--filter", "status=running"])
    return service in r.stdout.split()


def http_ok():
    try:
        return requests.get(BASE_URL, timeout=2).status_code == 200
    except requests.RequestException:
        return False


def free_port():
    """Kill whatever is LISTENing on :4444. No grace period."""
    subprocess.run(
        f"lsof -ti tcp:{PORT} -sTCP:LISTEN | xargs -r kill -9",
        shell=True,
        check=False,
    )


def wait_ready(service):
    print(f"Waiting up to {TIMEOUT}s for compose service '{service}'...")
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        if service_running(service) and http_ok():
            print(f"Service '{service}' ready.")
            return True
        time.sleep(2)
    print(f"Service '{service}' not ready after {TIMEOUT}s. Check: docker compose logs")
    return False


def ensure(service, up_cmd):
    if service_running(service) and http_ok():
        return True
    r = sh(up_cmd)
    if r.returncode != 0 and "address already in use" in (r.stderr + r.stdout).lower():
        print(f"Port {PORT} held by non-compose process — killing it.")
        free_port()
        sh(up_cmd)
    return wait_ready(service)


def npm_audit_fix():
    """Run `npm audit fix` inside the compose web service.

    Prefer `exec` against the running container (fast, node_modules populated).
    Fall back to a throwaway container that installs deps first: a plain
    `compose run --rm web npm audit fix` bypasses the service's default
    `npm install` command and finds an empty node_modules, so audit silently
    no-ops.
    """
    if service_running("web"):
        cmd = ["docker", "compose", "exec", "-T", "web", "npm", "audit", "fix"]
    else:
        cmd = [
            "docker", "compose", "run", "--rm", "web",
            "sh", "-c", "npm install --no-audit --no-fund && npm audit fix",
        ]
    # `npm audit fix` returns non-zero when vulns remain; that's handled by
    # lockfile_changed + the high-gated test in tests/test_security.py.
    sh(cmd)


def lockfile_changed():
    r = sh(["git", "diff", "--name-only"])
    changed = set(r.stdout.split())
    return "package.json" in changed or "package-lock.json" in changed


def show_remaining_vulns():
    """Non-blocking visibility on moderate+ vulns. The hard gate is `high`."""
    print("\nRemaining moderate+ vulnerabilities (non-blocking)...")
    r = sh(["npm", "audit", "--audit-level=moderate"])
    if r.returncode == 0:
        print("   None.")
        return
    for line in (r.stdout or "").splitlines():
        print(f"   {line}")
    print("   Non-blocking — only high+ blocks commits. Track via Dependabot.")


def pre_commit():
    if not ensure("web", ["docker", "compose", "up", "-d", "web"]):
        return 1
    npm_audit_fix()
    if lockfile_changed():
        print(
            "\nnpm audit fix modified package(-lock).json. Review, "
            "`git add` the changes, and commit again."
        )
        return 1
    show_remaining_vulns()
    return 0


def pre_push():
    print("Stopping preview profile (clean slate for rebuild)...")
    sh(["docker", "compose", "--profile", "preview", "down"])
    up_cmd = [
        "docker", "compose", "--profile", "preview",
        "up", "--build", "-d", "preview",
    ]
    return 0 if ensure("preview", up_cmd) else 1


def post_push():
    """Called from the pre-push hook's EXIT trap to switch back to dev."""
    print("Switching back to dev mode...")
    sh(["docker", "compose", "--profile", "preview", "down"])
    sh(["docker", "compose", "up", "-d"])
    return 0


SUBCOMMANDS = {
    "pre-commit": pre_commit,
    "pre-push": pre_push,
    "post-push": post_push,
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in SUBCOMMANDS:
        print(f"Usage: python scripts/ensure_server.py <{'|'.join(SUBCOMMANDS)}>")
        return 1
    return SUBCOMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    sys.exit(main())
