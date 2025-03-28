#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def setup_hooks():
    """Install git hooks from the hooks directory to .git/hooks."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    hooks_dir = project_root / "hooks"
    git_hooks_dir = project_root / ".git" / "hooks"

    # Create .git/hooks directory if it doesn't exist
    git_hooks_dir.mkdir(parents=True, exist_ok=True)

    # Copy each hook file
    for hook_file in hooks_dir.glob("*"):
        if hook_file.is_file():
            target_file = git_hooks_dir / hook_file.name
            print(f"Installing hook: {hook_file.name}")
            shutil.copy2(hook_file, target_file)
            # Make the hook executable
            os.chmod(target_file, 0o755)

if __name__ == "__main__":
    setup_hooks() 