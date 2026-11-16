"""`Templates` read from the `templates/` directory shipped inside the package."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "templates"


class PackageTemplates:
    def read(self, name: str) -> str:
        return (ROOT / name).read_text(encoding="utf-8")

    def names(self, prefix: str) -> list[str]:
        return sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / prefix).rglob("*") if p.is_file())
