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

def wait_for_server(url="http://localhost:4444", max_attempts=10):
    """Wait for the server to be ready."""
    import requests
    for attempt in range(max_attempts):
        try:
            log(f"Attempting to connect to {url}...")
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                log("Server is ready!")
                return True
            else:
                log(f"Server returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            log(f"Connection error: {str(e)}")
        except requests.exceptions.Timeout as e:
            log(f"Timeout error: {str(e)}")
        except Exception as e:
            log(f"Unexpected error: {str(e)}")
        
        if attempt < max_attempts - 1:
            log(f"Waiting 2 seconds before next attempt ({attempt + 1}/{max_attempts})")
            time.sleep(2)
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

        # Install Python dependencies first
        log("Installing Python dependencies...")
        # Try to use a virtual environment if it exists
        venv_pip = os.path.join(project_root, "venv", "bin", "pip")
        if os.path.exists(venv_pip):
            pip_cmd = f"{venv_pip} install -r requirements.txt"
        else:
            pip_cmd = "pip install -r requirements.txt"
        
        if not run_command(pip_cmd, cwd=project_root, timeout=30):
            log("Failed to install Python dependencies")
            sys.exit(1)

        # Stop any existing containers
        log("Stopping existing containers...")
        run_command("docker compose down", cwd=project_root, timeout=5)

        # Build and start the containers with a 60-second timeout
        log("Building and starting containers (timeout: 60s)...")
        build_output = run_command("docker compose up --build -d", cwd=project_root, timeout=60)
        if not build_output:
            log("Failed to build and start containers within 60 seconds")
            cleanup()
            sys.exit(1)

        # Wait a bit for the container to fully start
        log("Waiting for container to fully start...")
        time.sleep(5)

        # Wait for the server to be ready
        log("Waiting for server to be ready...")
        if not wait_for_server():
            log("Server failed to start")
            cleanup()
            sys.exit(1)

        # Run the tests sequentially
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
    main() 