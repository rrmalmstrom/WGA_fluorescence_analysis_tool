"""
Unit tests for launch_gui.py environment detection and restart logic.
All tests run on Mac via mocked environment variables.

Steps 1 & 2 tests written first (TDD), then Steps 3 & 4 make them GREEN.

Import strategy: launch_gui.py is now fully guarded by `if __name__ == '__main__'`
so importing it is safe — no argparse, no git calls, no GUI launch at import time.
"""
import sys
from unittest.mock import patch, MagicMock, call


def _get_launch_gui():
    """
    Return a freshly imported launch_gui module.
    Safe to call because all side-effecting code is inside main().
    """
    if "launch_gui" in sys.modules:
        del sys.modules["launch_gui"]
    import launch_gui  # noqa: PLC0415
    return launch_gui


# ---------------------------------------------------------------------------
# Step 1: Environment detection tests
# ---------------------------------------------------------------------------

class TestDetectEnvironment:
    """Tests for the detect_environment() helper."""

    def test_detect_conda_env_correct(self):
        """CONDA_DEFAULT_ENV=wga-fluorescence-gui, VIRTUAL_ENV unset → ('conda', 'wga-fluorescence-gui')"""
        mod = _get_launch_gui()
        env = {"CONDA_DEFAULT_ENV": "wga-fluorescence-gui"}
        with patch.dict("os.environ", env, clear=True):
            result = mod.detect_environment()
        assert result == ("conda", "wga-fluorescence-gui")

    def test_detect_conda_env_wrong_name(self):
        """CONDA_DEFAULT_ENV=base, VIRTUAL_ENV unset → ('none', '')"""
        mod = _get_launch_gui()
        env = {"CONDA_DEFAULT_ENV": "base"}
        with patch.dict("os.environ", env, clear=True):
            result = mod.detect_environment()
        assert result == ("none", "")

    def test_detect_conda_env_absent(self):
        """Both env vars unset → ('none', '')"""
        mod = _get_launch_gui()
        with patch.dict("os.environ", {}, clear=True):
            result = mod.detect_environment()
        assert result == ("none", "")

    def test_detect_venv_active(self):
        r"""CONDA_DEFAULT_ENV unset, VIRTUAL_ENV=C:\tool\.venv → ('venv', '.venv')"""
        mod = _get_launch_gui()
        env = {"VIRTUAL_ENV": r"C:\tool\.venv"}
        with patch.dict("os.environ", env, clear=True):
            result = mod.detect_environment()
        assert result == ("venv", ".venv")

    def test_detect_venv_active_unix_path(self):
        """VIRTUAL_ENV=/home/user/tool/.venv → ('venv', '.venv')"""
        mod = _get_launch_gui()
        env = {"VIRTUAL_ENV": "/home/user/tool/.venv"}
        with patch.dict("os.environ", env, clear=True):
            result = mod.detect_environment()
        assert result == ("venv", ".venv")

    def test_detect_conda_takes_priority_over_venv(self):
        """Both CONDA_DEFAULT_ENV=wga-fluorescence-gui and VIRTUAL_ENV set → conda wins"""
        mod = _get_launch_gui()
        env = {
            "CONDA_DEFAULT_ENV": "wga-fluorescence-gui",
            "VIRTUAL_ENV": "/some/path/.venv",
        }
        with patch.dict("os.environ", env, clear=True):
            result = mod.detect_environment()
        assert result == ("conda", "wga-fluorescence-gui")

    def test_detect_wrong_conda_with_venv_fallback(self):
        """CONDA_DEFAULT_ENV=base, VIRTUAL_ENV set → venv is accepted"""
        mod = _get_launch_gui()
        env = {
            "CONDA_DEFAULT_ENV": "base",
            "VIRTUAL_ENV": "/home/user/tool/.venv",
        }
        with patch.dict("os.environ", env, clear=True):
            result = mod.detect_environment()
        assert result == ("venv", ".venv")


# ---------------------------------------------------------------------------
# Step 2: Restart behavior and update-command branching tests
# ---------------------------------------------------------------------------

class TestRestartBehavior:
    """Tests for restart_launcher() and the restart path in check_for_updates()."""

    def test_restart_calls_popen_with_sys_argv(self):
        """restart_launcher() calls subprocess.Popen([sys.executable] + sys.argv)
        and then calls sys.exit(0)."""
        mod = _get_launch_gui()
        with patch("subprocess.Popen") as mock_popen, \
             patch("sys.exit") as mock_exit:
            mod.restart_launcher()
        mock_popen.assert_called_once_with([sys.executable] + sys.argv)
        mock_exit.assert_called_once_with(0)

    def test_restart_does_not_call_os_execv(self):
        """os.execv is never called during restart."""
        mod = _get_launch_gui()
        with patch("subprocess.Popen"), \
             patch("sys.exit"), \
             patch("os.execv") as mock_execv:
            mod.restart_launcher()
        mock_execv.assert_not_called()

    def test_restart_not_called_when_pull_fails(self):
        """If git pull returns non-zero, subprocess.Popen is not called for restart."""
        mod = _get_launch_gui()

        ok_fetch = MagicMock(returncode=0, stdout="", stderr="")
        behind_status = MagicMock(
            returncode=0,
            stdout="## main...origin/main [behind 1]\n",
            stderr="",
        )
        failed_pull = MagicMock(returncode=1, stdout="", stderr="conflict")

        def fake_run(cmd, **kwargs):
            if cmd[1] == "fetch":
                return ok_fetch
            if cmd[1] == "status":
                return behind_status
            if cmd[1] == "pull":
                return failed_pull
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run), \
             patch("builtins.input", return_value="y"), \
             patch("subprocess.Popen") as mock_popen, \
             patch("sys.exit") as mock_exit:
            mod.check_for_updates(env_type="conda")

        mock_popen.assert_not_called()
        # sys.exit(0) — the restart exit — must not have been called
        for c in mock_exit.call_args_list:
            assert c != call(0), "sys.exit(0) should not be called when pull fails"

    def test_restart_not_called_when_user_declines(self):
        """If user answers 'n' to the update prompt, no restart occurs."""
        mod = _get_launch_gui()

        ok_fetch = MagicMock(returncode=0, stdout="", stderr="")
        behind_status = MagicMock(
            returncode=0,
            stdout="## main...origin/main [behind 1]\n",
            stderr="",
        )

        def fake_run(cmd, **kwargs):
            if cmd[1] == "fetch":
                return ok_fetch
            if cmd[1] == "status":
                return behind_status
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run), \
             patch("builtins.input", return_value="n"), \
             patch("subprocess.Popen") as mock_popen, \
             patch("sys.exit") as mock_exit:
            mod.check_for_updates(env_type="conda")

        mock_popen.assert_not_called()
        mock_exit.assert_not_called()


class TestUpdateLogic:
    """Tests for the conda vs venv update-command branching in check_for_updates()."""

    def _make_fake_run(self, captured_cmds):
        """Return a fake subprocess.run that records commands and simulates success."""
        ok_fetch = MagicMock(returncode=0, stdout="", stderr="")
        behind_status = MagicMock(
            returncode=0,
            stdout="## main...origin/main [behind 1]\n",
            stderr="",
        )
        ok_pull = MagicMock(returncode=0, stdout="", stderr="")
        ok_update = MagicMock(returncode=0, stdout="", stderr="")

        def fake_run(cmd, **kwargs):
            captured_cmds.append(list(cmd))
            if cmd[1] == "fetch":
                return ok_fetch
            if cmd[1] == "status":
                return behind_status
            if cmd[1] == "pull":
                return ok_pull
            return ok_update

        return fake_run

    def test_update_env_conda_path(self):
        """When env_type == 'conda', the update command is conda env update."""
        mod = _get_launch_gui()
        captured_cmds = []

        with patch("subprocess.run", side_effect=self._make_fake_run(captured_cmds)), \
             patch("builtins.input", return_value="y"), \
             patch("subprocess.Popen"), \
             patch("sys.exit"):
            mod.check_for_updates(env_type="conda")

        assert ["conda", "env", "update", "-f", "environment.yml", "--prune"] in captured_cmds

    def test_update_env_venv_path(self):
        """When env_type == 'venv', the update command is pip install -r requirements.txt."""
        mod = _get_launch_gui()
        captured_cmds = []

        with patch("subprocess.run", side_effect=self._make_fake_run(captured_cmds)), \
             patch("builtins.input", return_value="y"), \
             patch("subprocess.Popen"), \
             patch("sys.exit"):
            mod.check_for_updates(env_type="venv")

        assert ["pip", "install", "-r", "requirements.txt", "-q"] in captured_cmds
