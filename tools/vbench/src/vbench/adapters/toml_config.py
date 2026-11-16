"""Find the project root and read `.vbench/config.toml` into a `Config`."""

from __future__ import annotations

import tomllib
from pathlib import Path

from ..domain.config import CONFIG_PATH, Config
from ..domain.errors import ConfigError


def find_root(start: Path | None = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for d in [cur, *cur.parents]:
        if (d / CONFIG_PATH).is_file():
            return d
    raise ConfigError(f"No {CONFIG_PATH} found in {cur} or any parent. Run `vbench init` first.")


def load_config(root: Path) -> Config:
    try:
        raw = tomllib.loads((root / CONFIG_PATH).read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{CONFIG_PATH} is not valid TOML: {e}") from e
    return Config.from_raw(raw)
