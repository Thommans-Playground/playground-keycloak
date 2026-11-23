#!/usr/bin/env python3
"""terms_tool.py: the term cards in docs/learn/terms/, and what a learner has already seen.

A term card explains one idea (PKCE, a nonce, a session cookie) in plain words and points at the real code that uses it,
so an explanation is tied to this project and not to a textbook. The cards are checked, so they cannot rot.

  terms_tool.py list                    every card, with its one-line meaning and whether it has been seen
  terms_tool.py show TERM               one card, as written
  terms_tool.py find FILE_OR_UC ...     the terms a use case (UC-A1) or a file talks about, best first, two by default
                                        (--limit N for more, --all for every match, --unseen for new ones only).
                                        A term whose prerequisites (card field `prereq`) are not seen is replaced by them.
  terms_tool.py seen TERM ...           record that the learner has met these terms (kept in .learning/terms-seen.txt)
  terms_tool.py due                     terms seen 3 or more days ago and not reviewed, or 14 or more days since a review
  terms_tool.py reviewed TERM ...       record that the learner has been asked about these terms again
  terms_tool.py check                   every card is well formed, every code pointer still exists and the prerequisites
                                        are cards with no cycle (exit 1 if not)

The seen file has one line each: `slug seen 2026-11-22` or `slug reviewed 2026-11-25` (an older `slug 2026-11-22` line
counts as seen).

It reads the cards and the files, and writes only .learning/terms-seen.txt, which is git-ignored and personal.
It never reads or writes anyone's notes. Standard library only."""

import argparse
import datetime
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

CARDS = "docs/learn/terms"
SEEN = ".learning/terms-seen.txt"
GUIDE = "docs/AUTH-STUDY-GUIDE.md"
REQUIRED = ("term", "say", "aliases", "code", "check")  # `guide` is optional: only some terms have a study guide section
SECTIONS = ("In one line", "Why we need it", "In our code", "Look for yourself")


@dataclass
class Card:
    path: Path
    term: str = ""
    say: str = ""
    aliases: list = field(default_factory=list)
    code: list = field(default_factory=list)  # (path, symbol)
    guide: str = ""
    prereq: list = field(default_factory=list)
    check: str = ""
    body: str = ""
    missing: list = field(default_factory=list)

    @property
    def slug(self) -> str:
        return self.path.stem


def _repo_root(start: Path) -> Path:
    for d in [start, *start.parents]:
        if (d / "vbench.json").is_file() or (d / ".git").exists():
            return d
    return start


def parse(path: Path) -> Card:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    card = Card(path=path)
    if not m:
        card.missing = list(REQUIRED)
        return card
    card.body = m.group(2).strip()
    key = None
    for line in m.group(1).splitlines():
        top = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if top:
            key, value = top.group(1), top.group(2).strip()
            if key in ("aliases", "prereq"):
                setattr(card, key, [v.strip() for v in value.strip("[]").split(",") if v.strip()])
            elif key == "code":
                card.code = []
            elif key in ("term", "say", "guide", "check"):
                setattr(card, key, value.strip("\"'"))
        elif key == "code" and line.strip().startswith("-"):
            item = line.strip()[1:].strip()
            file, _, symbol = item.partition("::")
            card.code.append((file.strip(), symbol.strip()))
    card.missing = [k for k in REQUIRED if not getattr(card, k)]
    return card


def cards(root: Path) -> list:
    return [parse(p) for p in sorted((root / CARDS).glob("*.md"))]


def today() -> datetime.date:
    return datetime.date.today()


def records(root: Path) -> list:
    """(slug, kind, date) for each line of the seen file. An old line `slug date` is a `seen`."""
    p = root / SEEN
    out = []
    if not p.is_file():
        return out
    for ln in p.read_text(encoding="utf-8").splitlines():
        parts = ln.split()
        if not parts:
            continue
        kind, stamp = ("seen", parts[1]) if len(parts) == 2 else (parts[1], parts[2]) if len(parts) >= 3 else ("seen", "")
        try:
            day = datetime.date.fromisoformat(stamp)
        except ValueError:
            day = None
        out.append((parts[0].lower(), kind, day))
    return out


def seen(root: Path) -> set:
    return {slug for slug, kind, _ in records(root) if kind == "seen"}


def due(root: Path, now: datetime.date) -> list:
    """Slugs seen 3 or more days ago and not reviewed, or 14 or more days since the last review."""
    first, last = {}, {}
    for slug, kind, day in records(root):
        if day is None:
            continue
        book = first if kind == "seen" else last
        if kind == "seen":
            book.setdefault(slug, day)
        else:
            book[slug] = max(day, book.get(slug, day))
    out = []
    for slug, day in first.items():
        if slug in last:
            if (now - last[slug]).days >= 14:
                out.append(slug)
        elif (now - day).days >= 3:
            out.append(slug)
    return sorted(out)


def find_card(all_cards: list, name: str):
    n = name.lower().strip()
    for c in all_cards:
        if n in (c.slug.lower(), c.term.lower()) or n in [a.lower() for a in c.aliases]:
            return c
    return None


def score(text: str, card: Card) -> int:
    """More mentions score higher, and a longer (more specific) alias counts for more than a short one."""
    total = 0
    for a in {card.term, *card.aliases}:
        n = len(re.findall(rf"(?<![A-Za-z0-9]){re.escape(a)}(?![A-Za-z0-9])", text, re.IGNORECASE))
        total += n * len(a)
    return total


def offered(all_cards: list, hits: list, met: set) -> list:
    """Hits in rank order, each unseen one replaced by its first unseen prerequisite (deep first), no repeats."""
    by_slug = {c.slug: c for c in all_cards}

    def first_ready(c, trail=()):
        for p in c.prereq:
            if p in by_slug and p not in met and p not in trail:
                return first_ready(by_slug[p], (*trail, c.slug))
        return c

    out = []
    for c in hits:
        c = c if c.slug in met else first_ready(c)
        if c not in out:
            out.append(c)
    return out


def _cycle(card: Card, by_slug: dict) -> bool:
    stack = list(card.prereq)
    seen_here = set()
    while stack:
        s = stack.pop()
        if s == card.slug:
            return True
        if s in seen_here or s not in by_slug:
            continue
        seen_here.add(s)
        stack.extend(by_slug[s].prereq)
    return False


def problems(root: Path, all_cards: list) -> list:
    out = []
    guide = (root / GUIDE).read_text(encoding="utf-8") if (root / GUIDE).is_file() else ""
    headings = [ln for ln in guide.splitlines() if ln.startswith("#")]
    owner = {}
    for c in all_cards:
        where = c.path.relative_to(root).as_posix()
        if c.missing:
            out.append(f"{where}: missing {', '.join(c.missing)}")
        for s in SECTIONS:
            if f"## {s}" not in c.body:
                out.append(f"{where}: no '## {s}' section")
        for file, symbol in c.code:
            f = root / file
            if not f.is_file():
                out.append(f"{where}: code pointer {file} does not exist")
            elif symbol and symbol not in f.read_text(encoding="utf-8", errors="replace"):
                out.append(f"{where}: {file} no longer contains '{symbol}'")
        for p in c.prereq:
            if p not in {x.slug for x in all_cards}:
                out.append(f"{where}: prereq '{p}' is not a card")
        if _cycle(c, {x.slug: x for x in all_cards}):
            out.append(f"{where}: prereq cycle through '{c.slug}'")
        if c.guide and not any(c.guide.lower() in h.lower() for h in headings):
            out.append(f"{where}: no heading '{c.guide}' in {GUIDE}")
        if c.slug != re.sub(r"[^a-z0-9]+", "-", c.term.lower()).strip("-"):
            out.append(f"{where}: file name should be '{re.sub(r'[^a-z0-9]+', '-', c.term.lower()).strip('-')}.md'")
        for a in [c.term, *c.aliases]:
            if a.lower() in owner and owner[a.lower()] != c.slug:
                out.append(f"{where}: '{a}' is also used by {owner[a.lower()]}")
            owner[a.lower()] = c.slug
    return out


def text_of(root: Path, target: str) -> str:
    """The words to scan: a file, or a use case with its diagrams, criteria and rules."""
    p = root / target
    if p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    if re.fullmatch(r"UC-[A-Z]\d+", target):
        parts = [f.read_text(encoding="utf-8", errors="replace") for f in sorted((root / "docs/usecases").glob(f"{target}-*"))]
        parts += [f.read_text(encoding="utf-8", errors="replace") for f in sorted((root / "docs/usecases/diagrams").glob(f"{target}-*"))]
        return "\n".join(parts)
    return target


def mentions(text: str, card: Card) -> bool:
    for a in {card.term, *card.aliases}:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(a)}(?![A-Za-z0-9])", text, re.IGNORECASE):
            return True
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="the repo root (default: found from the current folder)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("check")
    p = sub.add_parser("show")
    p.add_argument("term")
    p = sub.add_parser("find")
    p.add_argument("targets", nargs="+")
    p.add_argument("--unseen", action="store_true", help="only the terms the learner has not met")
    p.add_argument("--limit", type=int, default=2, help="how many to print (default 2)")
    p.add_argument("--all", action="store_true", help="print every match")
    sub.add_parser("due")
    p = sub.add_parser("reviewed")
    p.add_argument("terms", nargs="+")
    p = sub.add_parser("seen")
    p.add_argument("terms", nargs="+")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else _repo_root(Path.cwd().resolve())
    all_cards = cards(root)
    met = seen(root)

    if args.cmd == "list":
        for c in all_cards:
            print(f"{'seen ' if c.slug in met else 'new  '} {c.term:<22} {c.say}")
        return 0
    if args.cmd == "check":
        bad = problems(root, all_cards)
        for b in bad:
            print(b)
        print(f"{len(all_cards)} cards: {len(bad)} problem(s)")
        return 1 if bad else 0
    if args.cmd == "show":
        c = find_card(all_cards, args.term)
        if not c:
            print(f"no card for '{args.term}'. Cards: {', '.join(x.term for x in all_cards)}", file=sys.stderr)
            return 1
        print(f"# {c.term}\n\n{c.say}\n\n{c.body}\n\nIn the code: " + "; ".join(f"{f} ({s})" if s else f for f, s in c.code))
        print(f"Study guide: {GUIDE}, section {c.guide}\nCheck yourself: {c.check}")
        return 0
    if args.cmd == "find":
        text = "\n".join(text_of(root, t) for t in args.targets)
        ranked = sorted(((score(text, c), c) for c in all_cards if mentions(text, c)), key=lambda x: (-x[0], x[1].slug))
        hits = offered(all_cards, [c for _, c in ranked], met)
        if args.unseen:
            hits = [c for c in hits if c.slug not in met]
        if not args.all:
            hits = hits[: max(args.limit, 0)]
        for c in hits:
            print(f"{'seen ' if c.slug in met else 'new  '} {c.term:<22} {c.say}")
        if not hits:
            print("no terms with a card" + (" that are new to you" if args.unseen else ""))
        return 0
    if args.cmd == "due":
        slugs = due(root, today())
        for slug in slugs:
            c = find_card(all_cards, slug)
            print(f"{c.term if c else slug:<22} {c.check if c else ''}")
        if not slugs:
            print("nothing is due")
        return 0
    if args.cmd == "reviewed":
        done = []
        for name in args.terms:
            c = find_card(all_cards, name)
            if not c:
                print(f"no card for '{name}'", file=sys.stderr)
                return 1
            if c.slug not in met:
                print(f"'{name}' has not been marked seen yet", file=sys.stderr)
                return 1
            done.append(c.slug)
        (root / SEEN).parent.mkdir(parents=True, exist_ok=True)
        with open(root / SEEN, "a", encoding="utf-8") as f:
            for slug in done:
                f.write(f"{slug} reviewed {today().isoformat()}\n")
        print("reviewed: " + ", ".join(done))
        return 0
    if args.cmd == "seen":
        (root / SEEN).parent.mkdir(parents=True, exist_ok=True)
        done = []
        for name in args.terms:
            c = find_card(all_cards, name)
            if not c:
                print(f"no card for '{name}'", file=sys.stderr)
                return 1
            if c.slug not in met:
                done.append(c.slug)
        with open(root / SEEN, "a", encoding="utf-8") as f:
            for slug in done:
                f.write(f"{slug} seen {today().isoformat()}\n")
        print("recorded: " + (", ".join(done) or "already known"))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
