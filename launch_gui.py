#!/usr/bin/env python3
"""
launch_gui.py — User-facing launcher for the WGA Fluorescence Analysis Tool.

Usage:
    conda activate wga-fluorescence-gui
    python launch_gui.py [--data-folder /path/to/data]

Or double-click run.command on macOS (handles conda activation and data folder
prompt automatically).

On Windows, double-click run.bat (handles venv activation and data folder
prompt automatically).
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


# =============================================================================
# Helper functions — importable and testable without triggering GUI launch
# =============================================================================

def detect_environment() -> tuple[str, str]:
    """
    Detect whether running inside the expected conda env or an active venv.

    Returns:
        (env_type, env_name) where env_type is one of:
            "conda"  — CONDA_DEFAULT_ENV == "wga-fluorescence-gui"
            "venv"   — VIRTUAL_ENV is set (any path)
            "none"   — neither condition is met
        env_name is the environment name or path basename.
    """
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "")
    if conda_env == "wga-fluorescence-gui":
        return ("conda", conda_env)
    venv_path = os.environ.get("VIRTUAL_ENV", "")
    if venv_path:
        # Use os.path.basename after normalising separators so this works
        # correctly on both macOS (where Path treats \ as a literal char)
        # and Windows (where Path treats \ as a separator).
        normalised = venv_path.replace("\\", "/")
        return ("venv", Path(normalised).name)
    return ("none", "")


def restart_launcher() -> None:
    """
    Restart this script by spawning a new process and exiting the current one.

    Uses subprocess.Popen + sys.exit(0) instead of os.execv for cross-platform
    reliability. os.execv is unreliable on Windows (process replacement via
    CreateProcess + TerminateProcess can leave the window in an inconsistent
    state).
    """
    subprocess.Popen([sys.executable] + sys.argv)
    sys.exit(0)


def check_for_updates(env_type: str = "conda") -> bool:
    """
    Check whether the local repository is behind the remote and offer to pull.

    Always prints status to the terminal so the user knows what is happening.
    Returns True in all cases so the caller can always proceed to launch the
    GUI — update failures are non-fatal warnings, not hard errors.

    Args:
        env_type: "conda" or "venv" — determines which update command to run
                  after a successful git pull.
    """

    print("🔍 Checking for updates...")

    # ------------------------------------------------------------------
    # Step 2a: Fetch the latest refs from origin (silently).
    # If git is unavailable or there is no network, warn and continue.
    # ------------------------------------------------------------------
    try:
        fetch_result = subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True,
            text=True,
        )
        if fetch_result.returncode != 0:
            print("⚠ Could not reach GitHub (no git or no network). Skipping update check.")
            return True
    except FileNotFoundError:
        print("⚠ Could not reach GitHub (no git or no network). Skipping update check.")
        return True
    except Exception:
        print("⚠ Could not reach GitHub (no git or no network). Skipping update check.")
        return True

    # ------------------------------------------------------------------
    # Step 2b: Check whether the local branch is behind the remote.
    # ------------------------------------------------------------------
    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain=v1", "--branch"],
            capture_output=True,
            text=True,
        )
    except Exception:
        print("⚠ Could not reach GitHub (no git or no network). Skipping update check.")
        return True

    status_output = status_result.stdout

    # The first line of --porcelain=v1 --branch output looks like:
    #   ## main...origin/main [behind 3]
    # We check for the word "behind" on that line.
    branch_line = status_output.splitlines()[0] if status_output else ""
    is_behind = branch_line.startswith("##") and "behind" in branch_line

    if not is_behind:
        print("✅ Tool is up to date.")
        return True

    # ------------------------------------------------------------------
    # Step 2c: Updates are available — inform the user.
    # ------------------------------------------------------------------
    print("🔄 A new version is available on GitHub.")

    # Check for local uncommitted changes to tracked files
    # (any non-branch, non-untracked lines in porcelain output)
    local_changes = [
        line for line in status_output.splitlines()
        if line and not line.startswith("##") and not line.startswith("??")
    ]
    if local_changes:
        print("⚠ Warning: You have local changes that may conflict with the update.")

    # ------------------------------------------------------------------
    # Step 2d: Ask the user whether to pull now.
    # ------------------------------------------------------------------
    try:
        answer = input("Pull updates now? [y/N]: ").strip()
    except (EOFError, KeyboardInterrupt):
        answer = ""

    if answer.lower() == "y":
        print("⬇ Downloading update...")
        try:
            pull_result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True,
                text=True,
            )
            if pull_result.returncode == 0:
                print("✅ Update complete. Updating environment packages...")

                # Branch on environment type for the package update command
                if env_type == "conda":
                    update_cmd = ["conda", "env", "update", "-f", "environment.yml", "--prune"]
                else:  # venv
                    update_cmd = ["pip", "install", "-r", "requirements.txt", "-q"]

                update_result = subprocess.run(update_cmd, capture_output=True, text=True)
                if update_result.returncode != 0:
                    print("⚠ Warning: environment update failed. Launching with current packages.")

                print("🔄 Restarting with new version...")
                restart_launcher()
            else:
                print("❌ Update failed. Launching with current version.")
                return True
        except Exception as exc:
            print(f"❌ Update failed: {exc}. Launching with current version.")
            return True
    else:
        print("⏭ Skipping update. Launching with current version.")
        return True

    return True


# =============================================================================
# Main entry point — all top-level execution is guarded here
# =============================================================================

def main() -> None:
    """
    Orchestrate the full launch sequence:
      1. Parse arguments
      2. Detect and validate the active environment
      3. Check for updates
      4. Launch the GUI
    """

    # -------------------------------------------------------------------------
    # Step 1 — Parse command-line arguments
    # -------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="WGA Fluorescence Analysis Tool launcher")
    parser.add_argument(
        "--data-folder",
        metavar="PATH",
        default=None,
        help="Path to the data folder (sets default directory for file dialogs and exports)",
    )
    args = parser.parse_args()
    initial_dir: str | None = args.data_folder

    # -------------------------------------------------------------------------
    # Step 2 — Check and report environment
    # -------------------------------------------------------------------------
    env_type, env_name = detect_environment()

    if env_type == "conda":
        print(f"🐍 Conda environment: {env_name} ✅")
    elif env_type == "venv":
        print(f"🐍 Virtual environment: {env_name} ✅")
    else:
        print("❌ No recognized environment is active.")
        print("")
        print("  Mac/Linux users:")
        print("    conda activate wga-fluorescence-gui")
        print("    python launch_gui.py")
        print("")
        print("  Windows users:")
        print("    Double-click run.bat")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Step 3 — Check for updates
    # -------------------------------------------------------------------------
    check_for_updates(env_type=env_type)

    # -------------------------------------------------------------------------
    # Step 4 — Launch the GUI
    # -------------------------------------------------------------------------
    print("🚀 Launching WGA Fluorescence Analysis Tool...")
    if initial_dir:
        print(f"📂 Data folder: {initial_dir}")

    # Add the project root to sys.path so the package is importable
    sys.path.insert(0, str(Path(__file__).parent))

    try:
        from fluorescence_tool.gui.main_window import MainWindow

        app = MainWindow(initial_dir=initial_dir)
        app.run()

    except KeyboardInterrupt:
        print("\nApplication closed by user.")
    except ImportError as e:
        print(f"Error importing application components: {e}")
        print("Please ensure all dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
