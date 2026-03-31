#!/usr/bin/env python3
"""
Simplified Fluorescence Data Analysis Tool
Main application entry point

This is a clean, desktop-based fluorescence analysis tool designed to replace
the overly complex existing system with a simple, reliable solution.
"""

import subprocess
import sys
import tkinter as tk
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))


def check_for_updates() -> bool:
    """
    Check whether the local repository is behind the remote and offer to pull.

    Returns True in all cases so the caller can always proceed to launch the
    GUI — update failures are non-fatal warnings, not hard errors.
    """

    # ------------------------------------------------------------------
    # Step 1: Fetch the latest refs from origin (silently).
    # If git is unavailable or there is no network, warn and continue.
    # ------------------------------------------------------------------
    try:
        fetch_result = subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True,
            text=True,
        )
        if fetch_result.returncode != 0:
            print(
                "⚠ Could not check for updates (git fetch failed). Continuing..."
            )
            return True
    except FileNotFoundError:
        # git is not installed / not on PATH
        print(
            "⚠ Could not check for updates (no git or no network). Continuing..."
        )
        return True
    except Exception:
        print(
            "⚠ Could not check for updates (no git or no network). Continuing..."
        )
        return True

    # ------------------------------------------------------------------
    # Step 2: Check whether the local branch is behind the remote.
    # ------------------------------------------------------------------
    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain=v1", "--branch"],
            capture_output=True,
            text=True,
        )
    except Exception:
        print(
            "⚠ Could not check for updates (no git or no network). Continuing..."
        )
        return True

    status_output = status_result.stdout

    # The first line of --porcelain=v1 --branch output looks like:
    #   ## main...origin/main [behind 3]
    # We check for the word "behind" on that line.
    branch_line = status_output.splitlines()[0] if status_output else ""
    is_behind = branch_line.startswith("##") and "behind" in branch_line

    if not is_behind:
        print("✅ Up to date.")
        return True

    # ------------------------------------------------------------------
    # Step 3: Updates are available — inform the user.
    # ------------------------------------------------------------------
    print("🔄 Updates are available from GitHub.")

    # Check for local uncommitted changes (any non-branch lines in porcelain output)
    local_changes = [
        line for line in status_output.splitlines()
        if line and not line.startswith("##")
    ]
    if local_changes:
        print(
            "⚠ You have local changes that may conflict with the update."
        )

    # ------------------------------------------------------------------
    # Step 4: Ask the user whether to pull now.
    # ------------------------------------------------------------------
    try:
        answer = input("Pull updates now? [y/N]: ").strip()
    except (EOFError, KeyboardInterrupt):
        # Non-interactive environment or user pressed Ctrl-C
        answer = ""

    if answer.lower() == "y":
        try:
            pull_result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True,
                text=True,
            )
            if pull_result.returncode == 0:
                print("✅ Updated successfully.")
            else:
                print(
                    f"⚠ git pull failed:\n{pull_result.stderr.strip()}\n"
                    "Launching with current version."
                )
        except Exception as exc:
            print(f"⚠ git pull encountered an error: {exc}\nLaunching with current version.")
    else:
        print("Skipping update. Launching with current version.")

    return True


def main():
    """Main application entry point."""
    try:
        # Import GUI components
        from fluorescence_tool.gui.main_window import MainWindow
        
        # Create and run the application
        app = MainWindow()
        app.run()
        
    except ImportError as e:
        print(f"Error importing application components: {e}")
        print("Please ensure all dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check for updates before launching the GUI
    check_for_updates()

    main()
