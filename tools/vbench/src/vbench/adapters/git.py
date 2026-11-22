"""`Releases` and `Repo` backed by the `git` executable."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from ..domain.errors import UpdateError, UsageError


class GitReleases:
    def tags(self, url: str) -> list[str]:
        try:
            out = subprocess.run(
                ["git", "ls-remote", "--tags", "--refs", url.removeprefix("git+")],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            ).stdout
        except (OSError, subprocess.SubprocessError) as e:
            raise UpdateError(f"could not list tags at {url}: {e}") from e
        return [line.split("refs/tags/", 1)[1] for line in out.splitlines() if "refs/tags/" in line]


class GitRepo:
    def __init__(self, root: Path) -> None:
        self.root = root

    def branch(self) -> str:
        try:
            return subprocess.run(
                ["git", "branch", "--show-current"], cwd=self.root, capture_output=True, text=True, timeout=10
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    def commits(self, base: str) -> list[str]:
        for ref in (base, f"origin/{base}"):
            try:
                r = subprocess.run(
                    ["git", "log", "--format=%s", f"{ref}..HEAD"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except (OSError, subprocess.SubprocessError):
                break
            if r.returncode == 0:
                return [line for line in r.stdout.splitlines() if line]
        raise UsageError(
            f"cannot resolve base `{base}`. In CI, fetch full history (fetch-depth: 0) "
            "and pass --base origin/<target-branch>."
        )

    def branch_age_days(self, base: str) -> int | None:
        for ref in (base, f"origin/{base}"):
            try:
                r = subprocess.run(
                    ["git", "log", "--format=%ct", f"{ref}..HEAD"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except (OSError, subprocess.SubprocessError):
                return None
            if r.returncode == 0:
                stamps = [int(x) for x in r.stdout.split() if x.isdigit()]
                return max(0, int((time.time() - min(stamps)) // 86400)) if stamps else None
        return None

    def stale_worktrees(self) -> list[str]:
        try:
            out = subprocess.run(
                ["git", "worktree", "list", "--porcelain"], cwd=self.root, capture_output=True, text=True, timeout=10
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return []
        stale, path = [], ""
        for line in out.splitlines():
            if line.startswith("worktree "):
                path = line[len("worktree ") :]
            elif line.startswith("prunable"):
                stale.append(path)
        return stale

    def behind(self, base: str) -> int | None:
        for ref in (base, f"origin/{base}"):
            try:
                r = subprocess.run(
                    ["git", "rev-list", "--count", f"HEAD..{ref}"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except (OSError, subprocess.SubprocessError):
                return None
            if r.returncode == 0 and r.stdout.strip().isdigit():
                return int(r.stdout.strip())
        return None

    def _names(self, *args: str) -> list[str]:
        try:
            r = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as e:
            raise UsageError(f"git could not be run: {e}") from e
        if r.returncode:
            raise UsageError(f"git {args[0]} failed: {(r.stderr.strip() or r.stdout.strip())[:300]}")
        return sorted(name for name in r.stdout.split("\0") if name)

    def staged(self) -> list[str]:
        return self._names("diff", "--cached", "--name-only", "--relative", "-z")

    def unstaged(self) -> list[str]:
        return sorted(
            {
                *self._names("diff", "--name-only", "--relative", "-z"),
                *self._names("ls-files", "--others", "--exclude-standard", "-z"),
            }
        )

    def commit_staged(self, message: str) -> str:
        try:
            done = subprocess.run(
                ["git", "commit", "-m", message], cwd=self.root, capture_output=True, text=True, timeout=120
            )
            if done.returncode:
                raise UsageError(f"git commit failed: {(done.stderr.strip() or done.stdout.strip())[:600]}")
            return subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"], cwd=self.root, capture_output=True, text=True, timeout=10
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError) as e:
            raise UsageError(f"git could not be run: {e}") from e
