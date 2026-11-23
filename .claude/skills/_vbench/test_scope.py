"""The skills and agents keep one job each, and nothing is lost quietly (ADR 0017).

Run: python3 -m unittest discover -s .claude/skills/_vbench -p "test_*.py"

Reads docs/standards/skills-and-agents.md (the map) and skills-and-agents-ledger.md (what must stay), and checks them
against the files. It judges nothing about quality: it checks that things exist."""

import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILLS = REPO / ".claude" / "skills"
sys.path.insert(0, str(SKILLS / "_vbench"))
AGENTS = REPO / ".claude" / "agents"
MAP = (REPO / "docs/standards/skills-and-agents.md").read_text(encoding="utf-8")
LEDGER = (REPO / "docs/standards/skills-and-agents-ledger.md").read_text(encoding="utf-8")


def names():
    skills = {p.name for p in SKILLS.glob("vbench-*") if (p / "SKILL.md").is_file()}
    agents = {p.stem for p in AGENTS.glob("*.md")}
    return skills, agents


def rows(text, header):
    """The body rows of the table whose header row starts with `header`, as lists of cells."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(header):
            out = []
            for row in lines[i + 2 :]:
                if not row.startswith("|"):
                    break
                out.append([c.strip() for c in row.strip().strip("|").split("|")])
            return out
    raise AssertionError(f"no table starting {header!r}")


class Tests(unittest.TestCase):
    def test_every_skill_and_agent_has_a_row_in_the_map(self):
        skills, agents = names()
        listed = {c[0].strip("`") for c in rows(MAP, "| Role |")}
        self.assertEqual(sorted((skills | agents) - listed), [], "in the repo, but not in the map")
        self.assertEqual(sorted(listed - (skills | agents)), [], "in the map, but not in the repo")

    def test_every_role_belongs_to_one_known_pack_and_the_config_knows_the_same_packs(self):
        import config

        packs = {c[0].strip("`"): c[-1] for c in rows(MAP, "| Role |")}
        self.assertTrue(packs, "the Roles table has no Pack column")
        self.assertEqual(sorted(set(packs.values()) - set(config.PACKS)), [], "a role names a pack the config does not know")
        self.assertEqual(sorted(set(config.PACKS) - set(packs.values())), [], "a pack in the config has no role")
        # the trace rows each belong to a pack too: a pack that is off must have rows to switch off
        sys.path.insert(0, str(SKILLS / "vbench-vcycle" / "scripts"))
        import vcycle

        self.assertTrue(set(vcycle.PACK_OF.values()) <= set(config.PACKS))

    def test_every_hand_off_and_mention_names_something_that_exists(self):
        skills, agents = names()
        known = skills | agents
        mentioned = {m.removesuffix(".md") for m in re.findall(r"`(vbench-[a-z-]+(?:\.md)?)`", MAP)}
        self.assertEqual(sorted(mentioned - known), [], "the map names a skill or agent that does not exist")

    def test_every_script_command_in_the_ledger_is_still_offered(self):
        cache = {}
        for skill, script, command in rows(LEDGER, "| Skill | Script |"):
            path = SKILLS / skill / "scripts" / script
            self.assertTrue(path.is_file(), f"{skill}: {script} is gone")
            if path not in cache:
                out = subprocess.run([sys.executable, str(path), "--help"], capture_output=True, text=True, timeout=30)
                cache[path] = out.stdout + out.stderr
            self.assertIn(command, cache[path], f"{script} no longer offers {command}")

    def test_every_guard_in_the_ledger_is_still_in_its_file(self):
        for file, phrase, _why in rows(LEDGER, "| File | Phrase |"):
            path = REPO / file
            self.assertTrue(path.is_file(), f"{file} is gone")
            self.assertIn(phrase.lower(), path.read_text(encoding="utf-8").lower(), f"{file} lost: {phrase}")


if __name__ == "__main__":
    unittest.main()
