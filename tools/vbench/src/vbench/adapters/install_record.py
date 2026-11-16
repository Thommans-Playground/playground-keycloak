"""`InstallInfo` from the PEP 610 record (`direct_url.json`) that uv and pip write for VCS installs."""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, distribution

from ..ports import Origin


class DirectUrlInstallInfo:
    def origin(self) -> Origin | None:
        try:
            raw = distribution("vbench").read_text("direct_url.json")
        except PackageNotFoundError:
            return None
        if not raw:
            return None
        info = json.loads(raw)
        return Origin(url=info["url"], is_git="vcs_info" in info)
