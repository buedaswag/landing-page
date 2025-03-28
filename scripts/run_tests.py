#!/usr/bin/env python3
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime
import signal

def log(message):
    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] {'='*50}")
    print(f"[{timestamp}] {message}")
    print(f"[{timestamp}] {'='*50}\n")

def run_command(cmd, cwd=None, timeout=60):
    """Run a command and return its output."""
    try:
        log(f"Running command: {cmd}")
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        log(f"Command timed out after {timeout} seconds: {cmd}")
        return None
    except subprocess.CalledProcessError as e:
        log(f"Error running command: {cmd}")
        log(f"Error output: {e.stderr}")
        return None

def wait_for_server(url="http://localhost:4444"):
    """Wait for the server to be ready."""
    import requests
    log(f"Checking if server is ready at {url}...")
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            log("Server is ready!")
            return True
        else:
            log(f"Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        log(f"Server not ready: {str(e)}")
        return False

def cleanup():
    """Clean up Docker containers."""
    log("Cleaning up Docker containers...")
    run_command("docker compose down", timeout=5)

def signal_handler(signum, frame):
    """Handle cleanup on signal."""
    log("Received signal to terminate")
    cleanup()
    sys.exit(0)

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    log("Starting pre-push test suite")
    
    try:
        # Get the project root directory
        project_root = Path(__file__).parent.parent

        # Stop any existing containers
        log("Stopping existing containers...")
        run_command("docker compose down", cwd=project_root, timeout=5)

        # Build and start the containers
        log("Building and starting containers...")
        build_output = run_command("docker compose up --build -d", cwd=project_root, timeout=60)
        if not build_output:
            log("Failed to build and start containers")
            cleanup()
            sys.exit(1)

        # Wait for container logs to indicate readiness
        log("Waiting for container logs to indicate readiness...")
        logs_output = run_command("docker compose logs -f", cwd=project_root, timeout=10)
        if not logs_output or "Server is running at" not in logs_output:
            log("Server startup message not found in logs")
            cleanup()
            sys.exit(1)

        # Verify server is responding
        if not wait_for_server():
            log("Server failed to respond")
            cleanup()
            sys.exit(1)

        # Run the tests
        log("Running tests...")
        test_output = run_command("pytest tests/ -v", cwd=project_root, timeout=10)
        if not test_output:
            log("Tests failed")
            cleanup()
            sys.exit(1)

        # Stop the containers
        cleanup()

        log("All checks passed successfully!")
        sys.exit(0)

    except Exception as e:
        log(f"Unexpected error: {str(e)}")
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    # Main function that runs the pre-push test suite
    # - Stops any existing Docker containers
    # - Builds and starts containers with timeouts
    # - Waits for container logs to indicate readiness
    # - Verifies server is responding
    # - Runs pytest tests
    # - Cleans up containers on completion or failure
    # - Exits with status code 0 on success, 1 on failure
    main()