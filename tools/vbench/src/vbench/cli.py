"""`vbench` command line: the driving adapter and composition root.

Parses arguments, wires the adapters into the use cases in `app/`, prints results and maps errors to exit
codes. No rules live here.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import __version__
from .adapters import http_server
from .adapters.fs import FsWorkspace
from .adapters.git import GitReleases, GitRepo
from .adapters.install_record import DirectUrlInstallInfo
from .adapters.package_bundle import PackageBundle
from .adapters.package_templates import PackageTemplates
from .adapters.shell import ShellRunner
from .adapters.term import MODES, Style, wants_color
from .adapters.toml_config import find_playground_root, find_root, load_config
from .adapters.uv import UvInstaller
from .app import update as update_uc
from .app.check import links_mermaid, run_checks, run_commit_check
from .app.commit import make_commit, plan_commit
from .app.doctor import diagnose
from .app.export import export_state
from .app.export_playground import export_playground_state
from .app.init import init_project
from .app.new import new_context, new_context_map, new_discovery, new_use_case, next_free_ids
from .app.next import what_is_ready, what_next
from .app.ontology import render_ontology, write_ontology
from .app.status import project_status, results_json, status_json
from .app.sync import sync as sync_uc
from .app.trace import trace_json, trace_text
from .domain.checks import CHECKS
from .domain.config import Config
from .domain.errors import ConfigError, UpdateError, UsageError, VBenchError
from .domain.model import NextStep
from .domain.ontology import FORMATS
from .domain.stack import STACKS
from .domain.vcard import render_card
from .ports import Bundle, Committer, Installer, InstallInfo, Releases, Repo, Runner, Templates, Workspace

# What the dashboard needs of a project written in the playground's own format: where its docs are.
PLAYGROUND_CONFIG = Config.from_raw({"vbench": {"docs": "docs"}})


@dataclass
class Adapters:
    """The driven adapters the commands use. Tests pass fakes for the ones that touch the outside world."""

    templates: Templates = field(default_factory=PackageTemplates)
    install_info: InstallInfo = field(default_factory=DirectUrlInstallInfo)
    releases: Releases = field(default_factory=GitReleases)
    installer: Installer = field(default_factory=UvInstaller)
    repo_for: Callable[[Path], Repo] = GitRepo
    bundle: Bundle = field(default_factory=PackageBundle)
    committer_for: Callable[[Path], Committer] = GitRepo
    runner_for: Callable[[Path], Runner] = ShellRunner


# ---------------------------------------------------------------------------- commands
def cmd_init(args: argparse.Namespace, ad: Adapters) -> int:
    ws = FsWorkspace(Path(args.path))
    r = init_project(
        ws,
        ad.templates,
        ad.install_info,
        version=__version__,
        prod=args.prod,
        tests=args.tests,
        ci=args.ci,
        force=args.force,
        stack=args.stack,
        name=args.name or ws.root.name,
    )
    if (Path(args.path) / ".vbench/config.toml").is_file():  # the id registry lists what the scaffold already holds
        sync_uc(load_config(Path(args.path)), ws)
    for w in r.written:
        print(f"  created  {w}")
    for s in r.skipped:
        print(f"  kept     {s} (exists; use --force to overwrite)")
    plugin = (
        "  Teammates are prompted to install the Claude Code plugin when they open this repo\n"
        "  (commit .claude/settings.json)."
        if r.plugin_enabled
        else "  In Claude Code: /plugin marketplace add <repo-url>, then /plugin install vbench\n"
        "  (and replace the <host>/<org> placeholder in the CI files with your vbench repo URL)."
    )
    if r.skeleton:
        print(
            f"\nStack: python-fastapi, package `{r.package}` "
            "(FastAPI, PostgreSQL, ports and adapters, uv, Ruff, mypy).\n"
            "  uv sync                    install, and write uv.lock (commit it)\n"
            "  uv run pytest              the first test\n"
            "  docker compose up --build  the API and PostgreSQL on http://localhost:8000/docs\n"
            "  Read docs/04-technology-stack.md; the stack is recorded as decisions in the ADRs."
        )
    elif r.skeleton_skipped:
        print(
            "\nThis folder already has a pyproject.toml, so the application skeleton was left alone. The docs, the\n"
            "stack decision records, the configuration and the CI jobs were written; check they match your project."
        )
    print(
        "\nNext, in Claude Code:\n"
        "  /vbench:next        does the one next step and stops for your approval\n"
        "  vbench status       shows where each use case is on the V\n"
        "\n"
        "New to this? Read docs/00-getting-started.md (15 minutes), and docs/00-glossary.md for any word you\n"
        "do not know. In a terminal, `vbench next` says what is due and `vbench status` shows where you are.\n" + plugin
    )
    return 0


def cmd_check(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    missing = [d for d in (*cfg.prod, *cfg.tests) if not ws.exists(d)]
    if missing and args.which != "commits":  # a wrong folder makes every gate pass for the wrong reason
        print(
            f"vbench: configured folder(s) not found: {', '.join(missing)}. Set `prod` and `tests` in "
            ".vbench/config.toml, or the gates will find no code or tests to check.",
            file=sys.stderr,
        )
    if args.which == "commits":
        if args.matrix:
            raise UsageError("--matrix applies to rungs, acs, links and diagrams only.")
        res = run_commit_check(cfg, ws, ad.repo_for(root), args.base, args.branch)
        if args.json:
            print(json.dumps(results_json([res]), indent=2))
            return 0 if res.ok else 1
        print("\n".join(args.style.result(res.ok, res.lines)))
        return 0 if res.ok else 1
    if args.mermaid:
        if args.which != "links":
            raise UsageError("--mermaid applies to `check links` only.")
        print(links_mermaid(cfg, ws))
        return 0
    results = run_checks(cfg, ws, args.which, args.matrix)
    if args.json:
        print(json.dumps(results_json(results), indent=2))
        return 0 if args.matrix or all(r.ok for r in results) else 1
    if args.matrix:
        for r in results:
            print("\n".join(args.style.result(r.ok, r.lines)))
            print()
        return 0
    failed = 0
    for r in results:
        print("\n".join(args.style.result(r.ok, r.lines)))
        if not r.ok:
            failed += 1
            print()
    if failed and ws.exists(f"{cfg.docs.rstrip('/')}/00-glossary.md"):
        print(args.style("muted", f"Unsure what a term means? See {cfg.docs.rstrip('/')}/00-glossary.md."))
    return 1 if failed else 0


def cmd_new(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    if args.kind == "discovery":
        print(
            f"created {new_discovery(cfg, ws, ad.templates, args.title)}\n"
            "The interview fills it in; set Status to approved when you agree it."
        )
        return 0
    if args.kind == "context":
        made = new_context(cfg, ws, ad.templates, args.name)
        print(
            "\n".join(f"created {p}" for p in made)
            + "\nDraw the aggregates, then name the context in the specs' Bounded context row."
            + (
                "\nThe architecture contract (.importlinter) now covers this context: `uv run lint-imports`."
                if ".importlinter" in made
                else ""
            )
        )
        return 0
    if args.kind == "context-map":
        print(
            f"created {new_context_map(cfg, ws, ad.templates)}\n"
            "Classify each context and add one line per cross-context edge."
        )
        return 0
    if args.kind == "id":
        print("\n".join(next_free_ids(cfg, ws, args.id_kind, args.area, args.count)))
        return 0
    n = new_use_case(cfg, ws, ad.templates, args.area, args.title, args.slug)
    print(f"created {n.path}  ({n.uc}, rigor: {n.rigor})")
    print(f"Fill in the ACs, then tag code `Realises {n.uc}` and tests `Verifies {n.uc} · <rung> rung.`")
    return 0


def cmd_commit(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    repo = ad.repo_for(root)
    plan = plan_commit(
        cfg,
        ws,
        repo,
        summary=args.summary,
        type_=args.type,
        uc=args.uc,
        task=args.task,
        body=args.body or "",
        breaking=args.breaking,
    )
    for w in plan.warnings:
        print(f"vbench: {w}", file=sys.stderr)
    if args.message_only:
        print(plan.message)
        return 0
    sha = None
    if not args.dry_run and not plan.blockers:
        sha = make_commit(
            cfg,
            repo,
            ad.committer_for(root),
            plan,
            green=args.green,
            allow_default_branch=args.allow_default_branch,
            runner=ad.runner_for(root),
        )
    if args.json:
        print(json.dumps({**asdict(plan), "committed": sha}, indent=2))
    else:
        print(plan.message)
        print(f"\n{plan.type}  files: {', '.join(plan.paths)}")
        for b in plan.blockers:
            print(f"cannot commit yet: {b}")
        if sha:
            print(f"committed {sha}")
        elif args.dry_run and not plan.blockers:
            print("dry run: nothing committed.")
    if plan.blockers:
        return 1
    return 0


def cmd_id(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    print("\n".join(next_free_ids(cfg, ws, args.id_kind, args.area, args.count)))
    return 0


def _yes_no(sty: Style, value: bool) -> str:
    return sty("ok", "yes") if value else sty("muted", "no")


def cmd_status(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    st = project_status(cfg, ws, ad.repo_for(root), args.uc)
    if args.uc and not st.report.rows:
        known = ", ".join(r.uc for r in project_status(cfg, ws, ad.repo_for(root)).report.rows) or "none yet"
        raise UsageError(f"no use case or area matches `{args.uc}`. Use cases: {known}.")
    if args.json:
        print(json.dumps(status_json(cfg, ws, ad.repo_for(root), args.uc), indent=2))
        return 0
    sty = args.style
    if args.card:
        print(f"{sty('muted', 'branch:')} {st.branch or '(unknown)'}\n")
        for r in st.report.rows:
            print("\n".join(render_card(r, paint=sty)) + "\n")
        print(
            sty("muted", "gates:")
            + " "
            + "  ".join(f"{g.name}={sty('ok', 'ok') if g.ok else sty('fail', 'FAIL')}" for g in st.report.gates)
        )
        return 0
    print(f"{sty('muted', 'branch:')} {st.branch or '(unknown)'}   {sty('muted', 'specs:')} {len(st.report.rows)}\n")
    print("| UC | wave | ACs | covered | tasks | code | tested | blocked by | next |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in st.report.rows:
        blocked = sty("warn", ", ".join(r.blocked_by)) if r.blocked_by else sty("muted", "-")
        print(
            f"| {sty('id', r.uc)} | {r.wave} | {r.acs} | {r.covered}/{r.enforced} | {r.tasks_closed}/{r.tasks} "
            f"| {_yes_no(sty, r.code)} | {_yes_no(sty, r.tested)} | {blocked} | {r.next} |"
        )
    if st.report.orphans:
        print(f"\ncode tags with no spec: {', '.join(st.report.orphans)}")
    print(
        "\n"
        + sty("muted", "gates:")
        + " "
        + "  ".join(f"{g.name}={sty('ok', 'ok') if g.ok else sty('fail', 'FAIL')}" for g in st.report.gates)
    )
    return 0


def cmd_doctor(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    found = diagnose(cfg, ws, ad.repo_for(root))
    if args.json:
        print(json.dumps([asdict(f) for f in found], indent=2))
    elif not found:
        print("vbench doctor: nothing has drifted.")
    for f in found if not args.json else []:
        tone = "fail" if f.level == "problem" else "warn"
        sty = args.style
        print(f"{sty(tone, f'{f.level.upper():8}')} {f.text}\n         {sty('muted', 'fix:')} {sty('reason', f.fix)}")
    return 1 if any(f.level == "problem" for f in found) else 0


def _next_json(n: NextStep) -> dict:
    return {
        "command": n.command,
        "uc": n.uc,
        "why": n.why,
        "purpose": n.purpose,
        "blocked": {uc: list(waits) for uc, waits in n.blocked},
    }


def cmd_ontology(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    if args.write:
        formats = (args.format,) if args.format else FORMATS
        changed = write_ontology(cfg, ws, formats)
        print("\n".join(f"wrote {p}" for p in changed) or "The ontology files are already up to date.")
        return 0
    print(render_ontology(cfg, ws, args.format or "ttl"), end="")
    return 0


def cmd_trace(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    if args.json:
        print(json.dumps(trace_json(cfg, ws, args.uc), indent=2))
    else:
        print("\n".join(args.style.trace(trace_text(cfg, ws, args.uc))))
    return 0


def _print_next(sty: Style, n: NextStep) -> None:
    """The plain words stay `next:`, `why:` and `for:`; style only picks out the command and softens the reason."""
    command = sty("command", n.command) if n.command else sty("fail", "(nothing can proceed)")
    print(f"{sty('muted', 'next:')} {command}\n{sty('muted', 'why: ')} {n.why}")
    if n.purpose:
        print(f"{sty('muted', 'for: ')} {sty('reason', n.purpose)}")


def cmd_next(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    if args.ready:
        steps = what_is_ready(cfg, ws)
        if args.json:
            print(json.dumps({"ready": [_next_json(n) for n in steps]}, indent=2))
        else:
            for n in steps:
                _print_next(args.style, n)
                print()
        return 0 if any(n.command for n in steps) else 1
    n = what_next(cfg, ws)
    if args.json:
        print(json.dumps(_next_json(n), indent=2))
        return 0 if n.command else 1
    _print_next(args.style, n)
    for uc, waits in n.blocked:
        print(
            f"{args.style('warn', 'wait:')} {args.style('id', uc)} is blocked by {args.style('id', ', '.join(waits))}"
        )
    return 0 if n.command else 1


def cmd_sync(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    changed = sync_uc(cfg, ws)
    print("\n".join(f"updated {p}" for p in changed) or "Everything derived is already up to date.")
    return 0


def _state_for(
    args: argparse.Namespace, ad: Adapters, root: Path
) -> Callable[[], tuple[Config, Workspace, Callable[[], dict]]]:
    """Load the project afresh: its config, its files and the state function for the format it is written in."""
    if args.format == "playground":

        def load_playground():
            w = FsWorkspace(root)
            return PLAYGROUND_CONFIG, w, lambda: export_playground_state(w, ad.repo_for(root))

        return load_playground

    def load_vbench():
        c, w = load_config(root), FsWorkspace(root)
        return c, w, lambda: export_state(c, w, ad.repo_for(root))

    return load_vbench


def cmd_export(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    print(json.dumps(_state_for(args, ad, root)()[2](), indent=2))
    return 0


def cmd_serve(args: argparse.Namespace, cfg: Config, ws: Workspace, ad: Adapters, root: Path) -> int:
    static = (
        Path(args.static or os.environ.get("VBENCH_UI_DIST", ""))
        if (args.static or os.environ.get("VBENCH_UI_DIST"))
        else None
    )

    # the project is re-read on every request, so the page always shows the files as they are now
    server = http_server.serve(_state_for(args, ad, root), args.host, args.port, static)
    print(f"vbench UI on http://{args.host}:{server.server_address[1]}/  (read-only; Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def cmd_update(args: argparse.Namespace, ad: Adapters) -> int:
    plan = update_uc.plan_update(__version__, ad.install_info, ad.releases, args.to)
    if not plan.newer:
        print(f"vbench {plan.current} is up to date.")
        return 0
    print(f"vbench {plan.current} -> {plan.target}")
    if args.check:
        print("run `vbench update` to install it.")
        return 0
    update_uc.apply_update(plan, ad.installer)
    print("\nNext: update the Claude Code plugin with `/plugin marketplace update` then `/plugin update vbench`,")
    print("and compare your project's docs/CI with the new templates (`vbench init --force` overwrites them).")
    return 0


# ---------------------------------------------------------------------------- main
ALIASES = {"c": "check", "st": "status", "n": "next"}  # short forms; --help shows the long names only


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="vbench", description="Keep AI-assisted work on the V-cycle.")
    ap.add_argument("--version", action="version", version=f"vbench {__version__}")
    ap.add_argument(
        "--color",
        choices=MODES,
        default="auto",
        help="colour and text styles in human-readable output (auto: only on a terminal; NO_COLOR turns it off)",
    )
    sub = ap.add_subparsers(
        dest="cmd",
        required=True,
        # export and serve still work; they are for the dashboard and agents, so --help leaves them out
        metavar="{init,check,new,id,commit,status,next,trace,ontology,doctor,sync,update}",
    )

    p = sub.add_parser("init", help="scaffold .vbench/config.toml, docs/ templates and CI")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ci", choices=["github", "gitlab", "both", "none"], default="both")
    p.add_argument("--prod", nargs="+", default=["src"], help="production code dirs")
    p.add_argument("--tests", nargs="+", default=["tests"], help="test dirs")
    p.add_argument(
        "--stack",
        choices=STACKS,
        default="python-fastapi",
        help="what to scaffold besides the harness: the python-fastapi application skeleton, or none",
    )
    p.add_argument("--name", help="the project name (default: the folder name); the Python package is derived from it")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("check", aliases=["c"], help="run the gates (exit 1 on failure)")
    p.add_argument(
        "which",
        nargs="?",
        choices=[*CHECKS, "commits", "all"],
        default="all",
        help="`all` (the default) runs refs, rungs, acs, links, diagrams and docs; `commits` (git history) is explicit",
    )
    p.add_argument("--matrix", action="store_true", help="print the trace matrix instead of gating")
    p.add_argument(
        "--json", action="store_true", help="machine-readable: [{name, passing, lines}] (exit code as usual)"
    )
    p.add_argument("--mermaid", action="store_true", help="links: print the build order as a Mermaid flowchart")
    p.add_argument("--base", help="commits: the base ref to compare against (default: base_branch in config)")
    p.add_argument("--branch", help="commits: the branch name to check (default: the current branch)")

    p = sub.add_parser("new", help="allocate the next id and scaffold an artifact")
    nsub = p.add_subparsers(dest="kind", required=True)
    q = nsub.add_parser("uc", help="new use-case spec")
    q.add_argument("--area", required=True, help="area letter, e.g. A")
    q.add_argument("--title", required=True)
    q.add_argument("--slug")
    q = nsub.add_parser("discovery", help="new discovery brief (the analysis, before any requirement)")
    q.add_argument("--title", required=True, help="the idea, in a few words")
    q = nsub.add_parser("context", help="new bounded-context domain model (NN-<context>-ddd.puml)")
    q.add_argument("--name", required=True, help="the context's name, as written in the specs' Bounded context row")
    q = nsub.add_parser("id", help=argparse.SUPPRESS)  # the old spelling of `vbench id`
    q.add_argument("id_kind", metavar="kind")
    q.add_argument("--area")
    q.add_argument("--count", type=int, default=1)
    nsub.add_parser("context-map", help="new context map (09-context-ddd.puml) over the existing context models")

    p = sub.add_parser(
        "commit",
        help="write the commit message for a finished task, as the convention requires, and commit what is staged",
        description=(
            "Commit one finished piece of work. The message is built from the branch, the staged files and your "
            "summary, and always satisfies `vbench check commits`. Code commits (feat, fix, refactor, perf) are only "
            "made when the task's criteria all have tests (real ones: they must assert something) and the gates pass "
            "for this work. vbench then runs the project's test command ([commands] test in .vbench/config.toml) and "
            "commits only if it passes; with no command set you must say --green yourself. Only staged files are "
            "committed."
        ),
    )
    p.add_argument("-m", "--summary", required=True, help="what the change does, in the imperative (add login)")
    p.add_argument(
        "-t",
        "--type",
        help="feat | fix | docs | refactor | perf | test | build | ci | chore (default: from branch and files)",
    )
    p.add_argument(
        "--breaking",
        action="store_true",
        help="a breaking change: adds `!` and a BREAKING CHANGE footer (a major version)",
    )
    p.add_argument("--uc", help="the use case (default: from the branch or the staged files)")
    p.add_argument("--task", help="the task (default: from the branch or the criteria the staged tests mark)")
    p.add_argument("--body", help="extra lines for the commit body")
    p.add_argument("--dry-run", action="store_true", help="show the message and what blocks it; commit nothing")
    p.add_argument("--message-only", action="store_true", help="print just the message; commit nothing")
    p.add_argument("--json", action="store_true", help="machine-readable result")
    p.add_argument(
        "--green",
        action="store_true",
        help="code commits: I ran the tests and they pass (only when no [commands] test is set)",
    )
    p.add_argument("--allow-default-branch", action="store_true", help="allow committing on the default branch")

    p = sub.add_parser(
        "id", help="print the next free id of a kind (writes nothing): fr, nfr, request, ac, task, step, ..."
    )
    p.add_argument("id_kind", metavar="kind", help="request | stakeholder | fr | nfr | ac | task | step")
    p.add_argument("--area", help="area letter (needed for ac, task and step)")
    p.add_argument("--count", type=int, default=1, help="how many consecutive ids to print")

    p = sub.add_parser("status", aliases=["st"], help="progress derived from specs, tags and gates (read-only)")
    p.add_argument("uc", nargs="?", help="UC id or area letter to narrow")
    p.add_argument(
        "--json", action="store_true", help="machine-readable, with where each use case is realised and tested"
    )
    p.add_argument("--card", action="store_true", help="each use case as a table of the V, instead of the status table")

    p = sub.add_parser(
        "next", aliases=["n"], help="the one next step: which command to run, for which use case, and why"
    )
    p.add_argument("--json", action="store_true", help="machine-readable (for the /vbench:next skill)")
    p.add_argument(
        "--ready",
        action="store_true",
        help="every step that can start now (use cases whose dependencies are built), for parallel work",
    )

    p = sub.add_parser(
        "ontology",
        help="the project's ontology (artifacts, ids, vocabulary) as OWL/Turtle, RDF-XML, JSON-LD or YAML",
        description="Derive the ontology from the specs, tags and vocabulary. Prints one format, or with --write "
        "puts all four under the `ontology` folder of the config.",
    )
    p.add_argument("--format", choices=FORMATS, help="ttl (default), owl (RDF/XML), jsonld, yaml")
    p.add_argument("--write", action="store_true", help="write the files instead of printing")

    p = sub.add_parser("trace", help="a use case's sequence-diagram steps with their task, code and test")
    p.add_argument("uc", help="the use case id, e.g. UC-N-001")
    p.add_argument("--json", action="store_true", help="machine-readable")

    p = sub.add_parser("sync", help="regenerate what is derived from the specs (the overall use-case diagram)")

    p = sub.add_parser(
        "export",
        help=argparse.SUPPRESS,
        description="Print the whole project state as JSON (what the dashboard reads).",
    )
    p.add_argument(
        "--format",
        choices=["vbench", "playground"],
        default=os.environ.get("VBENCH_FORMAT", "vbench"),
        help="the project's format: vbench (default, or $VBENCH_FORMAT) or playground, the auth app's own",
    )

    p = sub.add_parser(
        "serve",
        help=argparse.SUPPRESS,
        description="Serve the project to the optional dashboard on localhost (read-only).",
    )
    p.add_argument(
        "--format",
        choices=["vbench", "playground"],
        default=os.environ.get("VBENCH_FORMAT", "vbench"),
        help="the project's format: vbench (default, or $VBENCH_FORMAT) or playground, the auth app's own",
    )
    p.add_argument("--host", default="127.0.0.1", help="bind address (default: loopback only)")
    p.add_argument("--port", type=int, default=3100)
    p.add_argument("--static", help="folder with the built UI (default: $VBENCH_UI_DIST)")

    p = sub.add_parser("doctor", help="find drift in the working copy: stale branch, dead worktrees, failing gates")
    p.add_argument("--json", action="store_true", help="machine-readable findings")

    p = sub.add_parser("update", help="reinstall the CLI at the newest release tag (needs uv)")
    p.add_argument("--check", action="store_true", help="only report whether a newer release exists")
    p.add_argument("--to", metavar="TAG", help="install this tag instead of the newest")
    for group in (sub, nsub):
        # argparse prints a subcommand whose help is SUPPRESS as "==SUPPRESS=="; drop those entries from the listing
        group._choices_actions = [a for a in group._choices_actions if a.help != argparse.SUPPRESS]
    return ap


def main(argv: list[str] | None = None, adapters: Adapters | None = None) -> int:
    ad = adapters or Adapters()
    args = _parser().parse_args(argv)
    args.cmd = ALIASES.get(args.cmd, args.cmd)
    args.style = Style(wants_color(args.color, sys.stdout))
    try:
        if args.cmd == "init":
            return cmd_init(args, ad)
        if args.cmd == "update":
            return cmd_update(args, ad)
        if args.cmd in ("export", "serve") and args.format == "playground":
            root = find_playground_root()
            return {"export": cmd_export, "serve": cmd_serve}[args.cmd](
                args, PLAYGROUND_CONFIG, FsWorkspace(root), ad, root
            )
        root = find_root()
        cfg, ws = load_config(root), FsWorkspace(root)
        if cfg.vbench_version and cfg.vbench_version != __version__:
            print(
                f"vbench: this project is pinned to {cfg.vbench_version} but {__version__} is installed. "
                f"Run `vbench update --to v{cfg.vbench_version}`, or bump vbench_version after validating.",
                file=sys.stderr,
            )
        return {
            "check": cmd_check,
            "new": cmd_new,
            "id": cmd_id,
            "trace": cmd_trace,
            "ontology": cmd_ontology,
            "commit": cmd_commit,
            "status": cmd_status,
            "next": cmd_next,
            "doctor": cmd_doctor,
            "sync": cmd_sync,
            "export": cmd_export,
            "serve": cmd_serve,
        }[args.cmd](args, cfg, ws, ad, root)
    except (ConfigError, UsageError, UpdateError) as e:
        print(f"vbench: {e}", file=sys.stderr)
        return 2
    except VBenchError as e:
        print(f"vbench: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
