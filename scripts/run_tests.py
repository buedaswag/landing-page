#!/usr/bin/env python3
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime

def log(message):
    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] {'='*50}")
    print(f"[{timestamp}] {message}")
    print(f"[{timestamp}] {'='*50}\n")

def run_command(cmd, cwd=None):
    """Run a command and return its output."""
    try:
        log(f"Running command: {cmd}")
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        log(f"Error running command: {cmd}")
        log(f"Error output: {e.stderr}")
        return None

def wait_for_server(url="http://localhost:4444", max_attempts=30):
    """Wait for the server to be ready."""
    import requests
    for attempt in range(max_attempts):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                log("Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            log(f"Waiting for server... attempt {attempt + 1}/{max_attempts}")
            pass
        time.sleep(1)
    return False

def main():
    log("Starting pre-push test suite")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Stop any existing containers
    log("Stopping existing containers...")
    run_command("docker compose down", cwd=project_root)

    # Build and start the containers
    log("Building and starting containers...")
    build_output = run_command("docker compose up --build -d", cwd=project_root)
    if not build_output:
        log("Failed to build and start containers")
        sys.exit(1)

    # Wait for the server to be ready
    log("Waiting for server to be ready...")
    if not wait_for_server():
        log("Server failed to start")
        sys.exit(1)

    # Install Python dependencies if needed
    log("Installing Python dependencies...")
    run_command("pip install -r requirements.txt", cwd=project_root)

    # Run the tests
    log("Running tests...")
    test_output = run_command("pytest tests/ -v", cwd=project_root)
    if not test_output:
        log("Tests failed")
        sys.exit(1)

    # Stop the containers
    log("Stopping containers...")
    run_command("docker compose down", cwd=project_root)

    log("All checks passed successfully!")

if __name__ == "__main__":
    main() 