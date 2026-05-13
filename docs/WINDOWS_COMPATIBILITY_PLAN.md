# Windows Compatibility Plan — WGA Fluorescence Analysis Tool

> **Branch:** `feature/windows-compatibility`
> **Status:** ⏳ Awaiting GATE 10A — Windows smoke test (all code complete; pending manual validation before merge to `main`)
> **Last updated:** 2026-05-13
>
> ### Implementation Progress
>
> | Step | Description | Status |
> |---|---|---|
> | Step 0 | Branch setup | ✅ Complete |
> | Step 1 | TDD — Environment detection tests (RED) | ✅ Complete |
> | Step 2 | TDD — Restart behavior tests (RED) | ✅ Complete |
> | Step 3 | Refactor `launch_gui.py` — environment detection (GREEN) | ✅ Complete |
> | Step 4 | Refactor `launch_gui.py` — replace `os.execv`, add update branching (GREEN) | ✅ Complete |
> | Step 5 | Add `requirements.in` | ✅ Complete |
> | Step 6 | Add `tk` to `environment.yml` | ✅ Complete |
> | Step 7 | Add `setup.bat` | ✅ Complete |
> | Step 8 | Add `run.bat` | ✅ Complete |
> | Step 9 | GitHub Actions CI workflow | ✅ Complete — push to remote to trigger CI |
> | **Step 10** | **Manual validation gate — Windows smoke test** | **⏳ BLOCKING — awaiting your confirmation** |
> | Step 11 | Update `docs/INSTALLATION.md` | ⬜ Not started (blocked by Step 10) |
> | Step 12 | Update `README.md` | ⬜ Not started (blocked by Step 10) |
> | Step 13 | Final review and merge to `main` | ⬜ Not started (blocked by Step 10) |
>
> ### ➡️ Your Next Action
>
> **Complete GATE 10A** (see [Step 10](#step-10-manual-validation-gate--windows-smoke-test) below):
> 1. On a Windows 10/11 machine: install Python 3.11 (check "Add Python to PATH") + Git for Windows
> 2. Clone the repo and double-click `setup.bat` — confirm "Setup complete!"
> 3. Double-click `run.bat` — confirm the GUI opens
> 4. Load `test_data\RM5097.96HL.BNCT.1.CSV` + `test_data\RM5097_layout.csv`, click "Process Files"
> 5. Check GitHub Actions tab — confirm CI is GREEN on both `macos-latest` and `windows-latest`
> 6. Report results — then Steps 11–13 (docs + merge) can proceed

---

## Table of Contents

1. [Overview and Goals](#1-overview-and-goals)
2. [Architecture Decisions and Justifications](#2-architecture-decisions-and-justifications)
3. [Risk Register](#3-risk-register)
4. [File Inventory — What Gets Created or Changed](#4-file-inventory--what-gets-created-or-changed)
5. [Implementation Steps](#5-implementation-steps)
   - [Step 0: Branch Setup](#step-0-branch-setup)
   - [Step 1: TDD — Environment Detection Tests](#step-1-tdd--environment-detection-tests)
   - [Step 2: TDD — Restart Behavior Tests](#step-2-tdd--restart-behavior-tests)
   - [Step 3: Refactor launch_gui.py — Environment Detection](#step-3-refactor-launch_guipy--environment-detection)
   - [Step 4: Refactor launch_gui.py — Replace os.execv](#step-4-refactor-launch_guipy--replace-osexecv)
   - [Step 5: Add requirements.in](#step-5-add-requirementsin)
   - [Step 6: Add environment.yml tk dependency](#step-6-add-environmentyml-tk-dependency)
   - [Step 7: Add setup.bat](#step-7-add-setupbat)
   - [Step 8: Add run.bat](#step-8-add-runbat)
   - [Step 9: GitHub Actions CI Workflow](#step-9-github-actions-ci-workflow)
   - [Step 10: Manual Validation Gate — Windows Smoke Test](#step-10-manual-validation-gate--windows-smoke-test)
   - [Step 11: Update docs/INSTALLATION.md](#step-11-update-docsinstallationmd)
   - [Step 12: Update README.md](#step-12-update-readmemd)
   - [Step 13: Final Review and Merge](#step-13-final-review-and-merge)
6. [Manual Validation Gates Summary](#6-manual-validation-gates-summary)
7. [Appendix: Key Code Snippets](#7-appendix-key-code-snippets)

---

## 1. Overview and Goals

### What This Plan Achieves

This plan adds Windows 10/11 compatibility to the WGA Fluorescence Analysis Tool while leaving the existing macOS conda path **completely unchanged**. Windows users get a parallel pip + venv path that is equally simple: install Python 3.11 and Git for Windows once, double-click `setup.bat` once, then double-click `run.bat` on every subsequent launch.

### User Experience Targets

| Scenario | macOS (existing) | Windows (new) |
|---|---|---|
| First-time setup | `bash setup.sh` | Double-click `setup.bat` |
| Daily launch | Double-click `run.command` | Double-click `run.bat` |
| Auto-update | `git pull` + `conda env update` | `git pull` + `pip install -r requirements.txt` |
| Environment manager | conda | Python venv (built-in) |
| Prerequisite software | conda + git | Python 3.11 + Git for Windows |

### Non-Goals

- No Docker, no containerization
- No changes to the macOS conda path
- No GUI test automation (tkinter is headless-untestable; all TDD focuses on non-GUI logic)
- No support for Windows 7/8

---

## 2. Architecture Decisions and Justifications

### Decision 1: requirements.txt — Commit to Repo vs. Regenerate on Each Install

**Decision: Commit `requirements.txt` to the repository, generated once by a GitHub Actions Windows runner and committed back.**

**Justification:**

The pip-tools documentation explicitly states: *"To generate accurate requirements.txt files for different environments, execute pip-compile separately within each target environment."* This means `requirements.txt` for Windows **must** be generated on a Windows machine — the developer's Mac cannot produce a correct Windows-pinned file.

Two options were evaluated:

| Option | Pros | Cons |
|---|---|---|
| **A: Commit to repo** (chosen) | `setup.bat` is fast and offline-capable; reproducible installs; no pip-tools needed on user machine | Requires a CI workflow to regenerate when `requirements.in` changes; file must not be hand-edited |
| **B: Regenerate on each install** | Always fresh | Requires pip-tools on user machine; slow first-run; network-dependent; non-deterministic across installs |

Option A is the standard industry pattern (used by Django, Flask, and most major Python projects). The CI workflow runs `pip-compile` on a `windows-latest` runner and commits the result back to the branch whenever `requirements.in` changes.

**Implication for the coding agent:** The `requirements.txt` file will NOT exist in the repo until the CI workflow runs for the first time on the feature branch. `setup.bat` must handle the case where `requirements.txt` is absent and print a clear error.

---

### Decision 2: Environment Detection Logic in launch_gui.py

**Decision: Replace the hard-coded conda env name check with a two-branch detector that accepts either the conda env OR an active venv.**

**Current logic (lines 39–52 of `launch_gui.py`):**
```python
REQUIRED_ENV = "wga-fluorescence-gui"
current_env = os.environ.get("CONDA_DEFAULT_ENV", "")
if current_env == REQUIRED_ENV:
    ...
else:
    sys.exit(1)
```

**New logic (pseudocode):**
```python
def detect_environment() -> tuple[str, str]:
    # Returns (env_type, env_name) where env_type is "conda" | "venv" | "none"
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "")
    if conda_env == "wga-fluorescence-gui":
        return ("conda", conda_env)
    venv_path = os.environ.get("VIRTUAL_ENV", "")
    if venv_path:
        return ("venv", Path(venv_path).name)
    return ("none", "")
```

The update logic then branches on `env_type`:
- `"conda"` → `conda env update -f environment.yml --prune`
- `"venv"` → `pip install -r requirements.txt -q`
- `"none"` → exit with instructions for both platforms

---

### Decision 3: Replace os.execv with subprocess.Popen + sys.exit(0)

**Decision: Replace `os.execv(sys.executable, [sys.executable] + sys.argv)` with `subprocess.Popen([sys.executable] + sys.argv)` followed by `sys.exit(0)`.**

**Why `os.execv` is problematic on Windows:**
- `os.execv` replaces the current process image. On Unix this is a true exec syscall. On Windows, Python implements it as `CreateProcess` + `TerminateProcess`, which is unreliable: the parent process may terminate before the child is fully initialized, leaving no visible window.
- In a `.bat` file context, the parent cmd.exe session may also close prematurely.
- `subprocess.Popen` + `sys.exit(0)` is the cross-platform idiom: spawn the new process, then cleanly exit the current one.

**New restart snippet:**
```python
import subprocess, sys
subprocess.Popen([sys.executable] + sys.argv)
sys.exit(0)
```

This is testable on Mac: a test can mock `subprocess.Popen` and `sys.exit` and verify both are called with the correct arguments.

---

### Decision 4: tk in environment.yml

**Decision: Add `- tk` as an explicit conda dependency in `environment.yml`.**

**Why:** On some conda environments (particularly minimal conda installs or certain Linux configurations), tkinter is not bundled with the Python package. Adding `tk` explicitly ensures it is always present. This is a one-line, zero-risk change. The conda-forge `tk` package is the standard way to ensure tkinter availability.

---

## 3. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | `requirements.txt` not yet committed when user runs `setup.bat` | Medium | High | `setup.bat` checks for file existence and prints a clear error with GitHub URL |
| R2 | Windows Python installer not added to PATH by user | High | High | `setup.bat` checks `python --version` and prints exact installer instructions if missing |
| R3 | Git for Windows not installed | Medium | High | `setup.bat` checks `git --version` and prints download URL |
| R4 | `pip install` fails due to missing Visual C++ build tools | Low | Medium | All dependencies (numpy, scipy, pandas, matplotlib) ship pre-built wheels for Windows — no compilation needed |
| R5 | tkinter not available in user's Python install | Low | Medium | `setup.bat` runs `python -c "import tkinter"` as a post-install check and prints fix instructions |
| R6 | CI commit-back workflow creates merge conflicts | Low | Low | Workflow only runs on `requirements.in` changes; uses `--no-edit` merge strategy |
| R7 | `subprocess.Popen` restart leaves zombie processes on Mac | Low | Low | Tested explicitly; `sys.exit(0)` ensures parent exits cleanly |
| R8 | Windows antivirus flags `.bat` files | Low | Medium | Documented in INSTALLATION.md; users right-click → Run as administrator if needed |
| R9 | conda env update after git pull fails silently | Low | Medium | Already handled in existing code; venv path uses same pattern |
| R10 | Developer cannot test Windows path locally | High | Medium | GitHub Actions CI provides the Windows test environment; manual gate requires Windows user confirmation |

---

### Decision 5: Python Version for Windows

**Decision: Target Python 3.11 for Windows users.**

**Why:** Python 3.11 is the current LTS-equivalent release with the best Windows installer UX (the official installer adds Python to PATH by default when the checkbox is checked). It is within the `>=3.9,<3.13` range specified in `environment.yml`. `requirements.in` will specify `python_requires >=3.9,<3.13` and the CI will compile on 3.11.

---

### Decision 6: requirements.txt Regeneration Trigger

**Decision: The CI workflow regenerates `requirements.txt` only when `requirements.in` changes (path filter), not on every push.**

**Why:** Regenerating on every push would create noisy commits. The workflow uses a `paths` filter:
```yaml
on:
  push:
    paths:
      - 'requirements.in'
```
A separate job in the same workflow runs the full pytest suite on every push regardless.

---

## 5. Implementation Steps

> **TDD Rule:** For every new piece of logic, the test is written first, then the implementation, then `pytest` is run to confirm green. GUI code is excluded from TDD (untestable headlessly).
>
> **Commit Rule:** Each step ends with a `git commit`. The coding agent writes a short check-in message to the developer at the end of each step.
>
> **Branch:** All work happens on `feature/windows-compatibility`. Do not merge to `main` until Step 13.

---

### Step 0: Branch Setup

**What the coding agent does:**

1. Create and check out the feature branch:
   ```bash
   git checkout -b feature/windows-compatibility
   ```
2. Verify the existing test suite passes on Mac before any changes:
   ```bash
   pytest -v
   ```
3. Commit (empty commit to mark branch start):
   ```bash
   git commit --allow-empty -m "chore: start feature/windows-compatibility branch"
   ```

**Check-in message to developer:**
> The feature branch `feature/windows-compatibility` has been created and all existing tests pass on Mac. No code has been changed yet. Next step: write the unit tests for the new environment detection and restart logic in `launch_gui.py` before touching any implementation code.

**Manual validation gate:** None — this is a local-only step.

---

### Step 1: TDD — Environment Detection Tests

**TDD phase: RED — write failing tests first.**

**What the coding agent does:**

Create `tests/unit/test_launcher.py`. This file tests the environment detection helper that will be extracted from `launch_gui.py`. The tests use `unittest.mock.patch` to control environment variables, so they run correctly on Mac regardless of what environment is actually active.

The test file must cover:

1. **`test_detect_conda_env_correct`** — `CONDA_DEFAULT_ENV=wga-fluorescence-gui`, `VIRTUAL_ENV` unset → returns `("conda", "wga-fluorescence-gui")`
2. **`test_detect_conda_env_wrong_name`** — `CONDA_DEFAULT_ENV=base`, `VIRTUAL_ENV` unset → returns `("none", "")`
3. **`test_detect_conda_env_absent`** — both env vars unset → returns `("none", "")`
4. **`test_detect_venv_active`** — `CONDA_DEFAULT_ENV` unset, `VIRTUAL_ENV=C:\tool\.venv` → returns `("venv", ".venv")`
5. **`test_detect_venv_active_unix_path`** — `VIRTUAL_ENV=/home/user/tool/.venv` → returns `("venv", ".venv")`
6. **`test_detect_conda_takes_priority_over_venv`** — both `CONDA_DEFAULT_ENV=wga-fluorescence-gui` and `VIRTUAL_ENV` set → returns `("conda", "wga-fluorescence-gui")` (conda wins)
7. **`test_detect_wrong_conda_with_venv_fallback`** — `CONDA_DEFAULT_ENV=base`, `VIRTUAL_ENV` set → returns `("venv", ...)` (venv is accepted when conda name is wrong)

**Skeleton the coding agent must implement:**

```python
# tests/unit/test_launcher.py
"""
Unit tests for launch_gui.py environment detection and restart logic.
All tests run on Mac via mocked environment variables.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# The function under test will live in launch_gui module.
# We import it after refactoring in Step 3.
# For now these tests will FAIL (RED phase) — that is expected.


class TestDetectEnvironment:
    """Tests for the detect_environment() helper."""

    def test_detect_conda_env_correct(self):
        ...

    def test_detect_conda_env_wrong_name(self):
        ...

    # ... (all 7 cases above)


class TestUpdateLogic:
    """Tests for the update_environment() helper (conda vs venv branch)."""
    # Written in Step 2 — placeholder class here
    pass
```

**Run tests (expect RED — ImportError or AttributeError since function doesn't exist yet):**
```bash
pytest tests/unit/test_launcher.py -v
```

**Commit:**
```bash
git add tests/unit/test_launcher.py
git commit -m "test: add RED tests for environment detection (Step 1 TDD)"
```

**Check-in message to developer:**
> `tests/unit/test_launcher.py` has been created with 7 failing tests for the new `detect_environment()` function. These tests are intentionally RED — the function doesn't exist yet. Next step: write the restart behavior tests (also RED), then implement both functions together in Step 3.

**Manual validation gate:** None.

---

### Step 2: TDD — Restart Behavior Tests

**TDD phase: RED — write failing tests for the restart logic.**

**What the coding agent does:**

Add a `TestRestartBehavior` class to `tests/unit/test_launcher.py`. These tests verify that after a successful `git pull`, the launcher calls `subprocess.Popen` with the correct arguments and then calls `sys.exit(0)` — and critically, does **not** call `os.execv`.

Tests to add:

1. **`test_restart_calls_popen_with_sys_argv`** — after a successful pull, `subprocess.Popen` is called with `[sys.executable] + sys.argv` and `sys.exit(0)` is called.
2. **`test_restart_does_not_call_os_execv`** — `os.execv` is never called during restart.
3. **`test_restart_not_called_when_pull_fails`** — if `git pull` returns non-zero, neither `subprocess.Popen` nor `sys.exit` is called for restart purposes.
4. **`test_restart_not_called_when_user_declines`** — if user answers `n` to the update prompt, no restart occurs.
5. **`test_update_env_conda_path`** — when `env_type == "conda"`, the update command is `["conda", "env", "update", "-f", "environment.yml", "--prune"]`.
6. **`test_update_env_venv_path`** — when `env_type == "venv"`, the update command is `["pip", "install", "-r", "requirements.txt", "-q"]`.

**Implementation note for the coding agent:** The restart logic must be extracted into a testable function `restart_launcher()` in `launch_gui.py`. The `check_for_updates()` function must accept `env_type` as a parameter so the update command can be branched. Both functions must be importable without triggering the GUI launch (the top-level script logic must be guarded by `if __name__ == "__main__"` or equivalent).

**Critical refactoring requirement:** The current `launch_gui.py` runs all top-level code at import time (argument parsing, env check, `check_for_updates()` call, GUI launch). This makes it untestable. The coding agent must restructure it so that:
- Helper functions (`detect_environment`, `check_for_updates`, `restart_launcher`) are defined at module level and importable
- The script entry point is guarded: `if __name__ == "__main__": main()`
- A `main()` function orchestrates the full launch sequence

**Run tests (expect RED):**
```bash
pytest tests/unit/test_launcher.py -v
```

**Commit:**
```bash
git add tests/unit/test_launcher.py
git commit -m "test: add RED tests for restart behavior and update branching (Step 2 TDD)"
```

**Check-in message to developer:**
> Restart behavior tests and update-branching tests have been added to `test_launcher.py`. All new tests are RED. The tests also reveal a structural requirement: `launch_gui.py` must be refactored to guard top-level execution with `if __name__ == '__main__'` so the helper functions can be imported and tested. This refactoring happens in Step 3. No application behavior changes yet.

**Manual validation gate:** None.

---

### Step 3: Refactor launch_gui.py — Environment Detection

**TDD phase: GREEN — implement until tests pass.**

**What the coding agent does:**

Refactor `launch_gui.py` to make it testable and add the dual conda/venv environment detection. The existing behavior for macOS conda users must be **completely preserved**.

**Specific changes to `launch_gui.py`:**

1. **Add `detect_environment()` function** (new, replaces lines 39–52):

```python
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
        return ("venv", Path(venv_path).name)
    return ("none", "")
```

2. **Replace the inline env check block** with a call to `detect_environment()` and appropriate branching:

```python
env_type, env_name = detect_environment()

if env_type == "conda":
    print(f"Conda environment: {env_name} OK")
elif env_type == "venv":
    print(f"Virtual environment: {env_name} OK")
else:
    print("ERROR: No recognized environment is active.")
    print("")
    print("  Mac/Linux users:")
    print("    conda activate wga-fluorescence-gui")
    print("    python launch_gui.py")
    print("")
    print("  Windows users:")
    print("    Double-click run.bat")
    sys.exit(1)
```

3. **Wrap all top-level execution in `main()`** and guard with `if __name__ == "__main__": main()`. The `detect_environment()`, `check_for_updates()`, and `restart_launcher()` functions remain at module level and importable.

4. **Pass `env_type` to `check_for_updates()`** so the update command can branch (implemented in Step 4).

5. **Do NOT change** the `check_for_updates()` update command yet — that is Step 4. For now, `check_for_updates()` still runs `conda env update` unconditionally. The tests from Step 1 should now go GREEN; the tests from Step 2 that test update branching will still be RED.

**Run tests after implementation:**
```bash
pytest tests/unit/test_launcher.py -v
pytest -v  # full suite — must still be all green
```

Expected: Step 1 tests GREEN, Step 2 update-branching tests still RED (not yet implemented), all pre-existing tests GREEN.

**Commit:**
```bash
git add launch_gui.py tests/unit/test_launcher.py
git commit -m "refactor: extract detect_environment() and guard launch_gui.py with main() (Step 3)"
```

**Check-in message to developer:**
> `launch_gui.py` has been refactored: `detect_environment()` is now a standalone importable function, all top-level execution is wrapped in `main()`, and the environment check now accepts either the conda env or an active venv. The 7 environment detection tests from Step 1 are now GREEN. The full existing test suite still passes. Mac behavior is unchanged — if you double-click `run.command` right now, it works exactly as before. Next: fix `os.execv` and add the update-command branching.

**Manual validation gate:**
> **GATE 3A — Mac smoke test:** Run `run.command` on your Mac and confirm the GUI opens normally. This verifies the refactoring did not break the existing macOS path.

---

### Step 4: Refactor launch_gui.py — Replace os.execv and Add Update Branching

**TDD phase: GREEN — implement until remaining Step 2 tests pass.**

**What the coding agent does:**

1. **Extract `restart_launcher()` function:**

```python
def restart_launcher() -> None:
    """
    Restart this script by spawning a new process and exiting the current one.

    Uses subprocess.Popen + sys.exit(0) instead of os.execv for cross-platform
    reliability. os.execv is unreliable on Windows (process replacement via
    CreateProcess + TerminateProcess can leave the window in an inconsistent state).
    """
    import subprocess
    subprocess.Popen([sys.executable] + sys.argv)
    sys.exit(0)
```

2. **Replace the `os.execv` call** in `check_for_updates()` (currently at line 147):

   **Before:**
   ```python
   os.execv(sys.executable, [sys.executable] + sys.argv)
   ```

   **After:**
   ```python
   restart_launcher()
   ```

3. **Add update-command branching to `check_for_updates()`:**

   Modify the function signature to accept `env_type`:
   ```python
   def check_for_updates(env_type: str = "conda") -> bool:
   ```

   After a successful `git pull`, before restarting, run the appropriate env update:
   ```python
   if env_type == "conda":
       update_cmd = ["conda", "env", "update", "-f", "environment.yml", "--prune"]
   else:  # venv
       update_cmd = ["pip", "install", "-r", "requirements.txt", "-q"]

   update_result = subprocess.run(update_cmd, capture_output=True, text=True)
   if update_result.returncode != 0:
       print("Warning: environment update failed. Launching with current packages.")
   ```

4. **Remove the `import os` usage for `execv`** — verify `os` is still needed for `os.environ.get()` (it is, so keep the import).

**Run tests after implementation:**
```bash
pytest tests/unit/test_launcher.py -v
pytest -v  # full suite
```

Expected: ALL tests in `test_launcher.py` GREEN. All pre-existing tests GREEN.

**Commit:**
```bash
git add launch_gui.py
git commit -m "fix: replace os.execv with subprocess.Popen+sys.exit; add venv update branch (Step 4)"
```

**Check-in message to developer:**
> `os.execv` has been replaced with `subprocess.Popen([sys.executable] + sys.argv)` followed by `sys.exit(0)`. The update logic now branches: conda path runs `conda env update`, venv path runs `pip install -r requirements.txt`. All 13 tests in `test_launcher.py` are now GREEN. The full test suite passes. Next: add the Windows dependency files (`requirements.in`, `environment.yml` tk fix).

**Manual validation gate:**
> **GATE 4A — Mac update smoke test:** On your Mac, temporarily make your local branch appear "behind" by creating a test commit on the remote, then run `python launch_gui.py` and answer `y` to the update prompt. Confirm the tool restarts cleanly without leaving a zombie window. (This can be done by pushing a trivial whitespace commit to a test branch.)

---

### Step 5: Add requirements.in

**TDD phase: No new tests needed** — `requirements.in` is a data file, not executable logic. Its correctness is validated by the CI workflow in Step 9 (pip-compile runs on Windows and produces a valid `requirements.txt`).

**What the coding agent does:**

Create `requirements.in` at the project root:

```
# requirements.in
# Abstract Windows dependencies for the WGA Fluorescence Analysis Tool.
# This file is the source of truth for Windows pip + venv installs.
# DO NOT edit requirements.txt directly — it is auto-generated by pip-compile
# running on a Windows GitHub Actions runner.
#
# To regenerate requirements.txt:
#   Push a change to this file — the CI workflow will run pip-compile on
#   windows-latest and commit the result back to the branch.

numpy>=2.0,<3.0
scipy>=1.13,<2.0
pandas>=2.0,<3.0
matplotlib>=3.9,<4.0
pytest>=7.0
```

**Notes for the coding agent:**
- Do NOT include `python` as a dependency (pip format does not support it)
- Do NOT include `tk` / `tkinter` — tkinter is bundled with the official Python Windows installer; it is not a pip package
- `pip-tools` itself is NOT listed here — it is only needed in CI, not by end users
- The `requirements.txt` file does not exist yet and will not exist until the CI workflow runs in Step 9

**Commit:**
```bash
git add requirements.in
git commit -m "feat: add requirements.in for Windows pip+venv path (Step 5)"
```

**Check-in message to developer:**
> `requirements.in` has been created with the abstract Windows dependencies mirroring `environment.yml`. The pinned `requirements.txt` does not exist yet — it will be generated by the GitHub Actions Windows runner in Step 9 when the CI workflow is added. Next: add `tk` to `environment.yml` for conda reliability.

**Manual validation gate:** None.

---

### Step 6: Add tk to environment.yml

**TDD phase: No new tests needed** — this is a one-line dependency addition. Correctness is validated by the existing test suite (if tkinter is missing, the GUI import tests would fail).

**What the coding agent does:**

Edit `environment.yml` to add `- tk` to the dependencies list:

```yaml
dependencies:
  - python >=3.9,<3.13
  - tk                      # <-- ADD THIS LINE
  - numpy >=2.0,<3.0
  - scipy >=1.13,<2.0
  - pandas >=2.0,<3.0
  - matplotlib >=3.9,<4.0
  - pytest >=7.0
  - pip
```

**Run tests:**
```bash
pytest -v
```

All tests must still pass (this change does not affect the running environment — it only affects future `conda env create` / `conda env update` runs).

**Commit:**
```bash
git add environment.yml
git commit -m "feat: add tk to environment.yml for explicit tkinter dependency (Step 6)"
```

**Check-in message to developer:**
> `tk` has been added to `environment.yml`. This ensures tkinter is explicitly managed by conda on all platforms, preventing rare cases where a minimal conda install omits it. The change takes effect the next time someone runs `conda env create` or `conda env update`. Existing environments are unaffected until updated. All tests pass. Next: create `setup.bat` for Windows first-time setup.

**Manual validation gate:** None.

---

### Step 7: Add setup.bat

**TDD phase: No unit tests** — `.bat` files cannot be unit-tested on Mac. Correctness is validated by the manual Windows gate in Step 10 and the CI smoke test in Step 9.

**What the coding agent does:**

Create `setup.bat` at the project root. This is the Windows first-time setup script — the equivalent of `setup.sh` for Windows users.

**Full content of `setup.bat`:**

```bat
@echo off
REM =============================================================================
REM setup.bat -- WGA Fluorescence Analysis Tool -- Windows First-Time Setup
REM
REM Double-click this file once after cloning the repository.
REM It will create a Python virtual environment and install all dependencies.
REM After setup, double-click run.bat to launch the tool.
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   WGA Fluorescence Analysis Tool -- First-Time Setup
echo ============================================================
echo.

REM -----------------------------------------------------------------------------
REM Check that Python 3 is available
REM -----------------------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on your PATH.
    echo.
    echo   Please install Python 3.11 from https://www.python.org/downloads/
    echo   IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Python found: !PYVER!

REM -----------------------------------------------------------------------------
REM Check that Git is available
REM -----------------------------------------------------------------------------
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git was not found on your PATH.
    echo.
    echo   Please install Git for Windows from https://git-scm.com/download/win
    echo   Use the default options during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=1,2,3 delims= " %%a in ('git --version') do set GITVER=%%a %%b %%c
echo Git found: !GITVER!
echo.

REM -----------------------------------------------------------------------------
REM Check that requirements.txt exists
REM -----------------------------------------------------------------------------
if not exist "%~dp0requirements.txt" (
    echo ERROR: requirements.txt not found.
    echo.
    echo   This file is generated automatically by the project's CI system.
    echo   Please ensure you have the latest version of the repository:
    echo     git pull origin main
    echo.
    echo   If the file is still missing, visit the project page on GitHub.
    pause
    exit /b 1
)

REM -----------------------------------------------------------------------------
REM Create the virtual environment (skip if it already exists)
REM -----------------------------------------------------------------------------
if exist "%~dp0.venv\Scripts\activate.bat" (
    echo Virtual environment already exists. Skipping creation.
) else (
    echo Creating virtual environment...
    python -m venv "%~dp0.venv"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
)
echo.

REM -----------------------------------------------------------------------------
REM Install dependencies from requirements.txt
REM -----------------------------------------------------------------------------
echo Installing dependencies (this may take a few minutes)...
"%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%~dp0.venv\Scripts\pip.exe" install -r "%~dp0requirements.txt" --quiet
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    echo   Check your internet connection and try again.
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

REM -----------------------------------------------------------------------------
REM Verify tkinter is available
REM -----------------------------------------------------------------------------
"%~dp0.venv\Scripts\python.exe" -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo WARNING: tkinter is not available in this Python installation.
    echo   The GUI will not work without tkinter.
    echo   Please reinstall Python 3.11 from https://www.python.org/downloads/
    echo   and ensure "tcl/tk and IDLE" is checked during installation.
    echo.
)

REM -----------------------------------------------------------------------------
REM Success
REM -----------------------------------------------------------------------------
echo ============================================================
echo   Setup complete!
echo.
echo   To launch the tool, double-click run.bat
echo ============================================================
echo.
pause
```

**Key design decisions in `setup.bat`:**
- Uses `%~dp0` (the directory of the `.bat` file itself) for all paths — works regardless of where the user double-clicks from
- Checks for `requirements.txt` existence and prints a clear error if missing (Risk R1)
- Checks Python and Git availability with actionable error messages (Risks R2, R3)
- Verifies tkinter post-install (Risk R5)
- Uses `.venv` as the venv directory name (hidden-ish, conventional)
- `pause` at the end keeps the window open so the user can read the output

**Commit:**
```bash
git add setup.bat
git commit -m "feat: add setup.bat for Windows first-time setup (Step 7)"
```

**Check-in message to developer:**
> `setup.bat` has been created. It checks for Python, Git, and `requirements.txt`, creates a `.venv` virtual environment, installs dependencies, and verifies tkinter. Note that `requirements.txt` does not exist yet — `setup.bat` will print a clear error if a Windows user tries to run it before the CI generates the file. That is intentional and correct. Next: create `run.bat` for the daily Windows launcher.

**Manual validation gate:** None yet — full Windows validation happens at Step 10.

---

### Step 8: Add run.bat

**TDD phase: No unit tests** — `.bat` files cannot be unit-tested on Mac. Validated by manual Windows gate in Step 10.

**What the coding agent does:**

Create `run.bat` at the project root. This is the Windows daily launcher — the equivalent of `run.command` for Windows users.

**Full content of `run.bat`:**

```bat
@echo off
REM =============================================================================
REM run.bat -- WGA Fluorescence Analysis Tool -- Windows Daily Launcher
REM
REM Double-click this file each time you want to use the tool.
REM It activates the virtual environment and launches the GUI.
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   WGA Fluorescence Analysis Tool
echo ============================================================
echo.

REM -----------------------------------------------------------------------------
REM Check that the virtual environment exists
REM -----------------------------------------------------------------------------
if not exist "%~dp0.venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo.
    echo   Please run setup.bat first to set up the tool.
    echo.
    pause
    exit /b 1
)

REM -----------------------------------------------------------------------------
REM Activate the virtual environment
REM -----------------------------------------------------------------------------
call "%~dp0.venv\Scripts\activate.bat"
echo Virtual environment: .venv OK
echo.

REM -----------------------------------------------------------------------------
REM Ask the user for the data folder path
REM -----------------------------------------------------------------------------
echo Please enter the path to your data folder.
echo (You can type the full path, or drag and drop the folder into this window.)
echo (Press Enter to skip and launch without a default data folder.)
echo.
set /p DATA_FOLDER="Data folder: "

REM Strip surrounding quotes if the user drag-dropped a folder
set DATA_FOLDER=%DATA_FOLDER:"=%

REM -----------------------------------------------------------------------------
REM Launch the tool
REM -----------------------------------------------------------------------------
cd /d "%~dp0"

if "!DATA_FOLDER!"=="" (
    echo.
    echo Launching without a default data folder...
    echo.
    python launch_gui.py
) else (
    if not exist "!DATA_FOLDER!" (
        echo.
        echo WARNING: The path does not exist or is not a folder.
        echo Launching without a default data folder.
        echo.
        python launch_gui.py
    ) else (
        echo.
        echo Data folder: !DATA_FOLDER!
        echo.
        python launch_gui.py --data-folder "!DATA_FOLDER!"
    )
)
```

**Key design decisions in `run.bat`:**
- Checks for `.venv` existence and directs user to `setup.bat` if missing
- Mirrors the data-folder prompt UX from `run.command` (same user experience on both platforms)
- Uses `cd /d "%~dp0"` to ensure the working directory is the project root before calling `python launch_gui.py`
- `VIRTUAL_ENV` is set automatically by `activate.bat`, which is what `detect_environment()` in `launch_gui.py` reads
- No `pause` at the end — the terminal window stays open while the GUI is running (Python process is in the foreground), and closes when the GUI exits

**Commit:**
```bash
git add run.bat
git commit -m "feat: add run.bat for Windows daily launcher (Step 8)"
```

**Check-in message to developer:**
> `run.bat` has been created. It activates the `.venv` virtual environment, prompts for a data folder (same UX as `run.command` on Mac), and launches `python launch_gui.py`. When `launch_gui.py` runs, `VIRTUAL_ENV` is set by the venv activation, so `detect_environment()` returns `("venv", ".venv")` and the correct update path is used. Next: add the GitHub Actions CI workflow, which will generate `requirements.txt` for the first time.

**Manual validation gate:** None yet — full Windows validation happens at Step 10.

---

### Step 9: GitHub Actions CI Workflow

**TDD phase: No new unit tests** — the workflow itself is validated by pushing to GitHub and observing the Actions tab. The pytest jobs within the workflow run the existing test suite.

**What the coding agent does:**

Create `.github/workflows/ci.yml`. This workflow has two jobs:

1. **`test`** — runs `pytest` on both `macos-latest` and `windows-latest` on every push to any branch
2. **`compile-requirements`** — runs only on `windows-latest`, only when `requirements.in` changes, generates `requirements.txt` via `pip-compile`, and commits it back to the branch

**Full content of `.github/workflows/ci.yml`:**

```yaml
# .github/workflows/ci.yml
# CI for WGA Fluorescence Analysis Tool
# - Runs pytest on macOS and Windows on every push
# - Regenerates requirements.txt on Windows when requirements.in changes

name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:
  # ---------------------------------------------------------------------------
  # Job 1: Run pytest on macOS and Windows
  # ---------------------------------------------------------------------------
  test:
    name: pytest (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [macos-latest, windows-latest]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies (macOS — pip from requirements.in)
        if: runner.os == 'macOS'
        run: |
          python -m pip install --upgrade pip
          pip install numpy>=2.0,<3.0 scipy>=1.13,<2.0 pandas>=2.0,<3.0 matplotlib>=3.9,<4.0 pytest>=7.0

      - name: Install dependencies (Windows — pip from requirements.txt)
        if: runner.os == 'Windows'
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
        # Note: requirements.txt must exist before this step runs.
        # If it does not exist yet (first push of requirements.in),
        # the compile-requirements job below will generate it.
        # On the very first push, this step may fail — that is acceptable.
        # Re-run the workflow after requirements.txt is committed.

      - name: Run pytest
        run: pytest -v --tb=short

  # ---------------------------------------------------------------------------
  # Job 2: Regenerate requirements.txt on Windows when requirements.in changes
  # ---------------------------------------------------------------------------
  compile-requirements:
    name: pip-compile (Windows)
    runs-on: windows-latest
    # Only run when requirements.in changes
    if: |
      github.event_name == 'push' &&
      contains(github.event.head_commit.modified, 'requirements.in') ||
      contains(github.event.head_commit.added, 'requirements.in')

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          # Use a token with write access so we can push the commit back
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install pip-tools
        run: pip install pip-tools

      - name: Compile requirements.txt from requirements.in
        run: pip-compile requirements.in --output-file requirements.txt --quiet

      - name: Commit requirements.txt if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add requirements.txt
          git diff --staged --quiet || git commit -m "chore: regenerate requirements.txt from requirements.in [skip ci]"
          git push
```

**Important notes for the coding agent:**

1. **The `[skip ci]` tag** in the commit message prevents the commit-back from triggering another CI run (infinite loop prevention).

2. **The `if` condition for `compile-requirements`** uses `contains(github.event.head_commit.modified, 'requirements.in')`. This is a string-contains check on the JSON array of modified files. It is slightly fragile — a more robust alternative is to use `paths` filtering at the job level, but GitHub Actions does not support `paths` at the job level (only at the workflow `on:` level). The current approach is the standard workaround.

3. **First-run bootstrap problem:** On the very first push of `requirements.in`, `requirements.txt` does not yet exist. The `test` job's Windows step will fail. The `compile-requirements` job will run and commit `requirements.txt`. The developer must then re-run the failed `test` job (or push a trivial commit) to get a green Windows test run. This is documented in the check-in message.

4. **macOS CI uses direct pip install** (not `requirements.txt`) because `requirements.txt` is Windows-pinned. The macOS job installs from the abstract version constraints directly — this mirrors what conda does on the developer's machine.

5. **`fail-fast: false`** ensures that a Windows test failure does not cancel the macOS job (and vice versa), giving full visibility into both platforms.

**Create the directory and file:**
```bash
mkdir -p .github/workflows
# then create .github/workflows/ci.yml with the content above
```

**Commit:**
```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow for pytest on macOS+Windows and pip-compile (Step 9)"
git push origin feature/windows-compatibility
```

**Check-in message to developer:**
> The GitHub Actions CI workflow has been added and pushed to the remote branch. Two things will now happen automatically on GitHub:
> 1. The `test` job will run pytest on both macOS and Windows. The macOS job should pass immediately. The Windows job will fail on this first push because `requirements.txt` does not exist yet.
> 2. The `compile-requirements` job will run on the Windows runner, generate `requirements.txt` from `requirements.in`, and commit it back to the branch.
>
> **Action required:** Wait for the `compile-requirements` job to complete (check the Actions tab on GitHub). Once `requirements.txt` is committed back, run `git pull` locally to get it, then re-run the failed Windows test job (or push a trivial commit). Confirm both macOS and Windows test jobs are GREEN before proceeding to Step 10.

**Manual validation gate:**
> **GATE 9A — CI green on both platforms:**
> 1. Go to the GitHub Actions tab for the `feature/windows-compatibility` branch
> 2. Confirm the `compile-requirements` job completed and committed `requirements.txt`
> 3. Run `git pull` locally to get `requirements.txt`
> 4. Confirm the `test` job is GREEN on both `macos-latest` and `windows-latest`
> 5. Report back to the coding agent with the result before proceeding to Step 10

---

### Step 10: Manual Validation Gate — Windows Smoke Test

**This step has no code changes.** It is a mandatory pause for real-world Windows validation before documentation is written.

**What the coding agent does:**

Write a check-in message to the developer and wait for confirmation before proceeding.

**Check-in message to developer:**
> All code changes are complete. Before writing the documentation, we need a real Windows user to validate the full setup and launch flow. Please find a Windows 10 or 11 machine (or ask a lab colleague) and follow these steps:
>
> **Prerequisites to install on the Windows machine:**
> 1. Python 3.11 from https://www.python.org/downloads/ — check "Add Python to PATH" during install
> 2. Git for Windows from https://git-scm.com/download/win — use default options
>
> **Setup test:**
> 1. Clone the repository: `git clone https://github.com/rrmalmstrom/WGA_fluorescence_analysis_tool.git`
> 2. Navigate into the folder in File Explorer
> 3. Double-click `setup.bat`
> 4. Confirm: no errors, "Setup complete!" message appears, window stays open until Enter is pressed
>
> **Launch test:**
> 1. Double-click `run.bat`
> 2. Enter a path to any folder when prompted (or press Enter to skip)
> 3. Confirm: the GUI window opens
> 4. Load `test_data\RM5097.96HL.BNCT.1.CSV` as data file
> 5. Load `test_data\RM5097_layout.csv` as layout file
> 6. Click "Process Files" — confirm no errors
> 7. Close the GUI — confirm the `run.bat` window closes cleanly
>
> **Please report back:**
> - Did `setup.bat` complete without errors? (Y/N)
> - Did the GUI open? (Y/N)
> - Did the data load and process correctly? (Y/N)
> - Any error messages or unexpected behavior?
>
> **Do not proceed to Step 11 until you confirm the GUI opens on Windows.**

**Manual validation gate:**
> **GATE 10A — Windows end-to-end smoke test (BLOCKING):**
> A real Windows user must confirm:
> - [ ] `setup.bat` completes without errors
> - [ ] `run.bat` opens the GUI
> - [ ] Sample data loads and processes correctly
> - [ ] GUI closes cleanly
>
> **The coding agent must not proceed to Step 11 until the developer confirms all four items above.**

---

### Step 11: Update docs/INSTALLATION.md

**TDD phase: No tests** — documentation only.

**Prerequisite:** GATE 10A must be confirmed GREEN before writing this section.

**What the coding agent does:**

Add a complete **Windows** section to `docs/INSTALLATION.md`. Insert it after the existing "System Requirements" section and before "Quick Installation". The Windows section must cover:

1. **Windows System Requirements** — Python 3.11 (official installer, not Microsoft Store), Git for Windows, Windows 10 or 11
2. **Windows Quick Installation** — 4-step numbered list: install Python, install Git, clone repo, double-click `setup.bat`
3. **Windows Daily Launch** — double-click `run.bat`; what the launcher does (env check, update check, data folder prompt, GUI launch)
4. **Windows Troubleshooting** — cover each risk from the Risk Register:
   - "python is not recognized" → Python not on PATH → reinstall with PATH checkbox
   - "git is not recognized" → Git not installed → download link
   - "requirements.txt not found" → `git pull origin main` and retry
   - "tkinter not available" → reinstall Python with "tcl/tk and IDLE" checked
   - Antivirus blocking `.bat` → right-click → Run as administrator
   - "Virtual environment not found" → re-run `setup.bat`
5. **Windows Update Behavior** — explain that `run.bat` → `launch_gui.py` checks for updates automatically; if a new version is available, it pulls and restarts
6. **Windows Uninstall** — delete the `.venv` folder and the cloned repository folder

**Also update** the existing "System Requirements" table at the top of `INSTALLATION.md` to add a Windows row.

**Also update** the "Platform-Specific Notes" section to add a Windows subsection.

**Commit:**
```bash
git add docs/INSTALLATION.md
git commit -m "docs: add complete Windows section to INSTALLATION.md (Step 11)"
```

**Check-in message to developer:**
> `docs/INSTALLATION.md` has been updated with a complete Windows installation section covering prerequisites, setup, daily launch, troubleshooting, and update behavior. Next: update `README.md` to mention Windows support.

**Manual validation gate:** None — documentation review happens at Step 13.

---

### Step 13: Final Review and Merge

**What the coding agent does:**

1. Run the full test suite one final time on Mac:
   ```bash
   pytest -v
   ```
   All tests must pass.

2. Review the complete diff of the feature branch against `main`:
   ```bash
   git diff main..feature/windows-compatibility --stat
   ```
   Expected changed files:
   - `launch_gui.py` (modified)
   - `environment.yml` (modified)
   - `requirements.in` (new)
   - `requirements.txt` (new — generated by CI)
   - `setup.bat` (new)
   - `run.bat` (new)
   - `.github/workflows/ci.yml` (new)
   - `tests/unit/test_launcher.py` (new)
   - `docs/INSTALLATION.md` (modified)
   - `README.md` (modified)

3. Confirm CI is GREEN on both platforms (GATE 9A must already be confirmed).

4. Open a pull request from `feature/windows-compatibility` to `main` on GitHub.

**Check-in message to developer:**
> The feature branch is complete. Here is a summary of everything that was done:
>
> **Code changes:**
> - `launch_gui.py` — refactored into testable functions; dual conda/venv environment detection; `os.execv` replaced with `subprocess.Popen + sys.exit(0)`; update command branches on environment type
> - `environment.yml` — added `tk` for explicit tkinter dependency
>
> **New Windows files:**
> - `requirements.in` — abstract Windows dependencies
> - `requirements.txt` — pinned Windows dependencies (auto-generated by CI on Windows runner)
> - `setup.bat` — Windows first-time setup
> - `run.bat` — Windows daily launcher
>
> **CI:**
> - `.github/workflows/ci.yml` — pytest on macOS + Windows on every push; pip-compile on Windows when `requirements.in` changes
>
> **Tests:**
> - `tests/unit/test_launcher.py` — 13 unit tests for environment detection, update branching, and restart behavior; all GREEN on Mac
>
> **Documentation:**
> - `docs/INSTALLATION.md` — complete Windows section added
> - `README.md` — Windows support noted throughout
>
> Please review the pull request and merge when satisfied.

**Manual validation gate:**
> **GATE 13A — Final pre-merge checklist (BLOCKING):**
> - [ ] `pytest -v` passes locally on Mac
> - [ ] CI is GREEN on both `macos-latest` and `windows-latest`
> - [ ] GATE 10A (Windows smoke test) was confirmed
> - [ ] `docs/INSTALLATION.md` Windows section reviewed and accurate
> - [ ] `README.md` changes reviewed
> - [ ] Pull request approved and merged to `main`

---

## 6. Manual Validation Gates Summary

| Gate | Step | Description | Blocking? |
|---|---|---|---|
| GATE 3A | Step 3 | Mac smoke test — `run.command` still works after `launch_gui.py` refactor | Yes |
| GATE 4A | Step 4 | Mac update smoke test — restart after `git pull` works cleanly | Recommended |
| GATE 9A | Step 9 | CI GREEN on both `macos-latest` and `windows-latest`; `requirements.txt` committed | Yes |
| GATE 10A | Step 10 | Windows end-to-end smoke test — `setup.bat` + `run.bat` + GUI opens + data loads | Yes (BLOCKING) |
| GATE 13A | Step 13 | Final pre-merge checklist — all tests pass, CI green, docs reviewed | Yes |

**The coding agent must pause at each blocking gate and wait for developer confirmation before proceeding.**

---

## 7. Appendix: Key Code Snippets

### A. detect_environment() — final form

```python
def detect_environment() -> tuple[str, str]:
    """
    Detect whether running inside the expected conda env or an active venv.

    Returns:
        (env_type, env_name) where env_type is "conda" | "venv" | "none"
    """
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "")
    if conda_env == "wga-fluorescence-gui":
        return ("conda", conda_env)
    venv_path = os.environ.get("VIRTUAL_ENV", "")
    if venv_path:
        return ("venv", Path(venv_path).name)
    return ("none", "")
```

### B. restart_launcher() — final form

```python
def restart_launcher() -> None:
    """
    Restart this script by spawning a new process and exiting the current one.
    Cross-platform replacement for os.execv.
    """
    subprocess.Popen([sys.executable] + sys.argv)
    sys.exit(0)
```

### C. check_for_updates() — signature change

```python
def check_for_updates(env_type: str = "conda") -> bool:
    # ... existing fetch/status/pull logic unchanged ...
    # After successful git pull, before restart:
    if env_type == "conda":
        update_cmd = ["conda", "env", "update", "-f", "environment.yml", "--prune"]
    else:
        update_cmd = ["pip", "install", "-r", "requirements.txt", "-q"]
    subprocess.run(update_cmd, capture_output=True, text=True)
    restart_launcher()
```

### D. main() guard — launch_gui.py structure

```python
# Module-level: imports, function definitions (detect_environment,
#               check_for_updates, restart_launcher)

def main() -> None:
    # argument parsing
    # detect_environment()
    # check_for_updates(env_type)
    # launch GUI

if __name__ == "__main__":
    main()
```

### E. GitHub Actions — pip-compile commit-back pattern

```yaml
- name: Commit requirements.txt if changed
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add requirements.txt
    git diff --staged --quiet || git commit -m "chore: regenerate requirements.txt [skip ci]"
    git push
```

### F. Workflow diagram

```
Developer pushes to feature/windows-compatibility
        |
        +---> CI: test job (macos-latest) -----> pytest -v -----> GREEN/RED
        |
        +---> CI: test job (windows-latest) ---> pytest -v -----> GREEN/RED
        |
        +---> CI: compile-requirements job (only if requirements.in changed)
                    |
                    +--> pip-compile requirements.in -> requirements.txt
                    +--> git commit requirements.txt [skip ci]
                    +--> git push
```

---

*Plan authored by the Architect agent on 2026-05-13. Verified against pip-tools docs (Context7: /websites/pip-tools_readthedocs_io_en_stable) and GitHub Actions docs (Context7: /websites/github_en_actions).*

### Step 12: Update README.md

**TDD phase: No tests** — documentation only.

**What the coding agent does:**

Make the following targeted changes to `README.md`:

1. **Update the "First-Time Setup" section** to add a Windows subsection alongside the existing macOS instructions:

```markdown
**Windows — double-click launcher:**
Double-click `setup.bat` once (first time only), then double-click `run.bat` to launch.
See [docs/INSTALLATION.md](docs/INSTALLATION.md) for full Windows setup instructions.
```

2. **Update the "Any platform — terminal" note** — change the heading from "Any platform" to "macOS/Linux — terminal" since Windows users should use `run.bat`, not the terminal.

3. **Update the project structure table** to add the new Windows files:

```
├── requirements.in              # Abstract Windows dependencies (pip format)
├── requirements.txt             # Pinned Windows dependencies (auto-generated by CI)
├── setup.bat                    # Windows first-time setup (creates venv, installs deps)
├── run.bat                      # Windows daily launcher
└── .github/
    └── workflows/
        └── ci.yml               # CI: pytest on macOS + Windows; pip-compile on Windows
```

4. **Update the "Dependencies" table** to note that `requirements.txt` covers Windows:

Add a row: `Windows deps | see requirements.txt (auto-generated) |`

5. **Update the "Known Issues" section** — add: "Windows support added in v1.1.0. Requires Python 3.11 and Git for Windows."

**Commit:**
```bash
git add README.md
git commit -m "docs: update README.md for Windows support (Step 12)"
```

**Check-in message to developer:**
> `README.md` has been updated to mention Windows support, the new files, and the Windows setup flow. All documentation is now complete. Next: final review and merge to main.

**Manual validation gate:** None — documentation review happens at Step 13.

---
