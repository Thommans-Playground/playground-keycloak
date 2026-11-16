"""`Runner` backed by a subprocess, for the project's own test command."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from ..ports import RunResult

TIMEOUT = 900  # seconds; a test suite longer than this should not gate a commit
TAIL_LINES = 15


class ShellRunner:
    def __init__(self, root: Path) -> None:
        self.root = root

    def run(self, command: str) -> RunResult:
        try:
            argv = shlex.split(command)
            done = subprocess.run(argv, cwd=self.root, capture_output=True, text=True, timeout=TIMEOUT)
        except (OSError, ValueError) as e:
            return RunResult(127, f"could not start `{command}`: {e}")
        except subprocess.TimeoutExpired:
            return RunResult(124, f"`{command}` did not finish within {TIMEOUT} seconds")
        lines = (done.stdout + done.stderr).strip().splitlines()
        return RunResult(done.returncode, "\n".join(lines[-TAIL_LINES:]))
