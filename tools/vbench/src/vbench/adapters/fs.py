"""`Workspace` backed by a directory on disk."""

from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from collections.abc import Sequence
from pathlib import Path


class FsWorkspace:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def files(self, dirs: Sequence[str], exts: Sequence[str]) -> list[str]:
        out: list[Path] = []
        for d in dirs:
            base = self.root / d
            if base.is_dir():
                out += [p for p in base.rglob("*") if p.is_file() and p.suffix in exts]
        return [p.relative_to(self.root).as_posix() for p in sorted(out)]

    def _inside(self, rel: str) -> Path:
        """The path on disk, refused if it (or a symlink on the way) leaves the project."""
        path = (self.root / rel).resolve()
        if path != self.root and self.root not in path.parents:
            raise ValueError(f"{rel!r} is outside the project")
        return path

    def read(self, rel: str) -> str:
        return self._inside(rel).read_text(encoding="utf-8", errors="replace")

    def exists(self, rel: str) -> bool:
        try:
            return self._inside(rel).exists()
        except ValueError:
            return False

    def write(self, rel: str, text: str, overwrite: bool = True) -> bool:
        dst = self._inside(rel)
        if dst.exists() and not overwrite:
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        # write beside the target and rename, so a crash never leaves a half-written file
        fd, tmp = tempfile.mkstemp(dir=dst.parent, prefix=f".{dst.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            if dst.exists():
                os.chmod(tmp, dst.stat().st_mode & 0o7777)
            else:
                os.chmod(tmp, 0o644)
            os.replace(tmp, dst)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise
        return True

    def clear(self, rel: str) -> None:
        target = (self.root / rel).resolve()
        if target == self.root or self.root not in target.parents:
            raise ValueError(f"refusing to clear {rel!r}: not inside the project")
        shutil.rmtree(target, ignore_errors=True)
