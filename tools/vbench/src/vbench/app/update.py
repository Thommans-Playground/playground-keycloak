"""Use case: move the installed CLI to a newer release."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.errors import UpdateError
from ..ports import Installer, InstallInfo, Releases

TAG = re.compile(r"v?(\d+)\.(\d+)\.(\d+)$")


def tag_key(tag: str) -> tuple[int, int, int]:
    m = TAG.match(tag)
    return (int(m[1]), int(m[2]), int(m[3])) if m else (-1, -1, -1)


@dataclass
class UpdatePlan:
    current: str
    target: str
    newer: bool
    source: str  # the requirement to install, e.g. git+https://…@v0.2.0


def plan_update(current: str, info: InstallInfo, releases: Releases, to: str | None = None) -> UpdatePlan:
    origin = info.origin()
    if origin is None:
        raise UpdateError(
            "vbench was not installed from a Git URL (no install record). "
            'Install with: uv tool install "git+<repo-url>@<tag>"'
        )
    if not origin.is_git:
        raise UpdateError(f"vbench was installed from {origin.url}, not from Git; update it from there.")
    target = to
    if not target:
        tags = [t for t in releases.tags(origin.url) if TAG.match(t)]
        if not tags:
            raise UpdateError(f"no release tags (vX.Y.Z) found at {origin.url}")
        target = max(tags, key=tag_key)
    base = origin.url if origin.url.startswith("git+") else f"git+{origin.url}"
    newer = bool(to) or tag_key(target) > tag_key(current)
    return UpdatePlan(current, target, newer, f"{base}@{target}")


def apply_update(plan: UpdatePlan, installer: Installer) -> None:
    if not installer.available():
        raise UpdateError("uv not found on PATH. Install it from https://docs.astral.sh/uv/")
    installer.install(plan.source)
