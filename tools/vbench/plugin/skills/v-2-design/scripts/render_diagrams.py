#!/usr/bin/env python3
"""Render the project's PlantUML files to images, if `plantuml` is installed.

Finds every `.puml` in the specs folder and the docs root, skips the `_` includes, and writes one image per
diagram into `<docs>/diagrams/`. Rendering is optional: `vbench check diagrams` needs no renderer.

    render_diagrams.py                 SVG into <docs>/diagrams/
    render_diagrams.py --format png
    render_diagrams.py --out build/diagrams
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

CONFIG = Path(".vbench") / "config.toml"


def project() -> tuple[Path, dict]:
    for d in [Path.cwd(), *Path.cwd().parents]:
        if (d / CONFIG).is_file():
            return d, tomllib.loads((d / CONFIG).read_text(encoding="utf-8")).get("vbench", {})
    sys.exit(f"render_diagrams: no {CONFIG.as_posix()} found. Run `vbench init` first.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--format", choices=["svg", "png"], default="svg")
    ap.add_argument("--out", help="output folder (default: <docs>/diagrams)")
    args = ap.parse_args()

    root, cfg = project()
    docs = root / cfg.get("docs", "docs")
    specs = root / cfg.get("specs", "docs/usecase-diagrams")
    files = sorted({p for base in (specs, docs) for p in base.glob("*.puml") if not p.name.startswith("_")})
    if not files:
        print("No diagrams to render.")
        return 0
    if not shutil.which("plantuml"):
        print(
            "render_diagrams: `plantuml` is not installed (brew install plantuml, or see plantuml.com/download).\n"
            f"{len(files)} diagram(s) were not rendered; `vbench check diagrams` still validates them.",
            file=sys.stderr,
        )
        return 3

    out = Path(args.out) if args.out else docs / "diagrams"
    out = out if out.is_absolute() else root / out
    out.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["plantuml", f"-t{args.format}", "-o", str(out), *map(str, files)], capture_output=True, text=True, cwd=root
    )
    if r.returncode != 0:
        print((r.stdout + r.stderr).strip(), file=sys.stderr)
        return 1
    print(f"Rendered {len(files)} diagram(s) to {out.relative_to(root) if out.is_relative_to(root) else out}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
