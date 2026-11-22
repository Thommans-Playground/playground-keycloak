"""The ports: what the core and the use cases need from the outside world, as small Protocols.

Driven (secondary) ports are implemented in `adapters/`. The driving side is `cli.py`. Nothing in
`domain/` or `app/` imports an adapter; `tests/test_architecture.py` enforces that.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class Workspace(Protocol):
    """The project tree. All paths are relative to the project root, in POSIX form."""

    def files(self, dirs: Sequence[str], exts: Sequence[str]) -> list[str]:
        """Sorted files under `dirs` (recursive) with one of `exts`; missing dirs yield nothing."""

    def read(self, rel: str) -> str: ...

    def exists(self, rel: str) -> bool: ...

    def write(self, rel: str, text: str, overwrite: bool = True) -> bool:
        """Create parents and write. Return False (leaving the file) when it exists and not `overwrite`."""

    def clear(self, rel: str) -> None:
        """Remove the directory `rel` and everything in it. Nothing happens when it does not exist."""


class Templates(Protocol):
    """The scaffold files shipped with vbench."""

    def read(self, name: str) -> str: ...

    def names(self, prefix: str) -> list[str]:
        """Template names under `prefix`, e.g. `docs/00-naming-conventions.md`."""


@dataclass(frozen=True)
class Origin:
    """Where the running vbench was installed from."""

    url: str
    is_git: bool


class InstallInfo(Protocol):
    def origin(self) -> Origin | None:
        """None when there is no install record (editable or source checkout)."""


class Releases(Protocol):
    def tags(self, url: str) -> list[str]:
        """Tag names at `url`. Raises `UpdateError` when the remote cannot be listed."""


class Installer(Protocol):
    def available(self) -> bool: ...

    def install(self, source: str) -> None:
        """Install (replace) vbench from `source`, a pip-style requirement such as `git+https://…@v1.2.3`."""


class Repo(Protocol):
    def branch(self) -> str:
        """Current branch, or an empty string when unknown."""

    def commits(self, base: str) -> list[str]:
        """Subjects of the commits in `base..HEAD`. Raises `UsageError` when `base` cannot be resolved."""

    def staged(self) -> list[str]:
        """Project-relative paths in the index (what a commit would record)."""

    def unstaged(self) -> list[str]:
        """Project-relative paths changed in the working tree but not staged, including untracked ones."""

    def branch_age_days(self, base: str) -> int | None:
        """Days since the oldest commit in `base..HEAD`; None when there is none or `base` cannot be resolved."""

    def stale_worktrees(self) -> list[str]:
        """Linked worktrees git itself marks prunable (their folder is gone)."""

    def behind(self, base: str) -> int | None:
        """How many commits `base` (or `origin/<base>`) has that HEAD lacks; None when it cannot be told."""


@dataclass(frozen=True)
class RunResult:
    code: int
    tail: str  # the last lines of output, for a failure message


class Runner(Protocol):
    """Runs the project's own command (its test suite) and reports whether it passed."""

    def run(self, command: str) -> RunResult:
        """Run `command` in the project root. Never raises: a command that cannot start is a non-zero result."""


class Committer(Protocol):
    """Records files in the repository's history."""

    def commit_staged(self, message: str) -> str:
        """Commit what is already staged, nothing more; return the short hash. Raises `UsageError` when git refuses."""


class Bundle(Protocol):
    """The vbench package itself (its code and the dashboard source), to stage for a container build."""

    def files(self) -> list[str]:
        """Text files to stage, as paths relative to the package's parent folder, e.g. `vbench/cli.py`."""

    def read(self, rel: str) -> str: ...
