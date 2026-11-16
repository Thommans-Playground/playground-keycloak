"""`Bundle` read from the installed vbench package: its Python code and the dashboard source."""

from __future__ import annotations

from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent  # .../vbench
SKIP_DIRS = {"__pycache__", "node_modules", "dist", ".vite", ".mypy_cache", ".pytest_cache"}
SKIP_FILES = {".DS_Store"}
SKIP_SUFFIXES = (".pyc", ".tsbuildinfo")


class PackageBundle:
    def __init__(self, package: Path = PACKAGE) -> None:
        self.package = package

    def files(self) -> list[str]:
        out = []
        for p in sorted(self.package.rglob("*")):
            rel = p.relative_to(self.package)
            if not p.is_file() or SKIP_DIRS & set(rel.parts) or p.name in SKIP_FILES or p.name.endswith(SKIP_SUFFIXES):
                continue
            try:
                p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue  # only text is staged
            out.append(f"{self.package.name}/{rel.as_posix()}")
        return out

    def read(self, rel: str) -> str:
        return (self.package.parent / rel).read_text(encoding="utf-8")
