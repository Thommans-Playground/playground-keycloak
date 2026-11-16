"""`Installer` that shells out to `uv tool install`."""

from __future__ import annotations

import shutil
import subprocess

from ..domain.errors import UpdateError


class UvInstaller:
    def available(self) -> bool:
        return shutil.which("uv") is not None

    def install(self, source: str) -> None:
        try:
            subprocess.run(["uv", "tool", "install", "--force", source], check=True)
        except (OSError, subprocess.CalledProcessError) as e:
            raise UpdateError(f"uv tool install failed: {e}") from e
