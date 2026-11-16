#!/usr/bin/env python3
"""Check that PlantUML diagrams parse, and that each one fits an A4 portrait page.

Usage: python3 check_diagrams.py <folder or .puml file> [more ...]

It renders each diagram to a temporary folder (nothing is written into the repo), reads the
image size, and reports it in millimetres at the size the diagram was drawn.

A diagram passes when:
  1. PlantUML parses it.
  2. It is portrait: taller than it is wide. A diagram may ask for landscape instead, with a
     line `' page: landscape` in the file (a use case diagram does, so it reads on a laptop).
     A diagram that is a composite overview for the screen says `' page: overview` and is only parsed, not fitted.
     A landscape diagram must be wider than tall and about 3:2 (no wider than 1.65 to 1).
  3. It fits the printable area of an A4 page, 180 x 267 mm portrait or 267 x 180 mm landscape
     (A4 is 210 x 297 mm, with a 15 mm margin), at its drawn size. No shrinking, so the text
     stays as readable as designed.

It needs Java and the PlantUML jar. The jar ships with the VS Code PlantUML extension. Set
PLANTUML_JAR to use another one.

Exit code: 0 if every diagram passes, 1 otherwise, 2 if it could not run.
"""

import glob
import os
import struct
import subprocess
import sys
import tempfile

MAX_W_MM = 180.0
MAX_H_MM = 267.0
INCH_MM = 25.4
DEFAULT_DPI = 150.0


def find_jar():
    env = os.environ.get("PLANTUML_JAR")
    if env and os.path.exists(env):
        return env
    found = sorted(glob.glob(os.path.expanduser("~/.vscode/extensions/jebbs.plantuml-*/plantuml.jar")))
    return found[-1] if found else None


def png_size(path):
    """Return (width_px, height_px, dpi) read from a PNG file."""
    with open(path, "rb") as f:
        data = f.read(4096)
    width, height = struct.unpack(">II", data[16:24])
    dpi = DEFAULT_DPI
    pos = data.find(b"pHYs")
    if pos != -1:
        px_per_m = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        if px_per_m:
            dpi = px_per_m * 0.0254
    return width, height, dpi


def collect(args):
    files = []
    for arg in args:
        if os.path.isdir(arg):
            files += sorted(p for p in glob.glob(os.path.join(arg, "*.puml")) if not os.path.basename(p).startswith("_"))
        elif arg.endswith(".puml"):
            files.append(arg)
    return files


def main(args):
    if not args:
        print(__doc__)
        return 2
    jar = find_jar()
    if not jar:
        print("PlantUML jar not found. Install the VS Code PlantUML extension or set PLANTUML_JAR.")
        return 2
    files = collect(args)
    if not files:
        print("No .puml files found.")
        return 2

    failed = False
    with tempfile.TemporaryDirectory() as out:
        for path in files:
            folder = os.path.dirname(os.path.abspath(path))
            name = os.path.basename(path)
            run = subprocess.run(
                ["java", "-Djava.awt.headless=true", "-jar", jar, "-tpng", "-o", out, name],
                cwd=folder, capture_output=True, text=True,
            )
            png = os.path.join(out, os.path.splitext(name)[0] + ".png")
            if run.returncode != 0 or not os.path.exists(png) or "Error" in run.stdout + run.stderr:
                print(f"FAIL  {name}: does not parse")
                print("      " + (run.stdout + run.stderr).strip().replace("\n", "\n      ")[:400])
                failed = True
                continue
            w, h, dpi = png_size(png)
            w_mm, h_mm = w / dpi * INCH_MM, h / dpi * INCH_MM
            if "' page: overview" in open(path, encoding="utf-8").read():
                print(f"ok    {name}: {w_mm:.0f} x {h_mm:.0f} mm (an overview for the screen, not fitted to a page)")
                continue
            problems = []
            landscape = "' page: landscape" in open(path, encoding="utf-8").read()
            max_w, max_h = (MAX_H_MM, MAX_W_MM) if landscape else (MAX_W_MM, MAX_H_MM)
            if landscape and h > w:
                problems.append("portrait, but the file says landscape")
            if not landscape and h < w:
                problems.append("landscape, needs to be portrait")
            if landscape and w > h * 1.65:
                problems.append("wider than about 3:2")
            if w_mm > max_w:
                problems.append(f"{w_mm - max_w:.0f} mm too wide")
            if h_mm > max_h:
                problems.append(f"{h_mm - max_h:.0f} mm too tall")
            status = "ok   " if not problems else "FAIL "
            note = "" if not problems else "  (" + ", ".join(problems) + ")"
            print(f"{status} {name}: {w_mm:.0f} x {h_mm:.0f} mm{note}")
            failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
