"""Use case: scaffold `.vbench/config.toml`, docs templates, CI and the project-scope plugin settings."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..domain.config import CONFIG_PATH
from ..domain.errors import UsageError
from ..domain.stack import STACKS, display_name, dist_name, importlinter_text, package_name
from ..ports import InstallInfo, Templates, Workspace

REPO_FILES = {  # template -> (destination, the --ci choices it is written for)
    "repo/CONTRIBUTING.md": ("CONTRIBUTING.md", ("github", "gitlab", "none", "both")),
    "repo/pull_request_template.md": (".github/pull_request_template.md", ("github", "both")),
}
GITLAB_MR = ("repo/pull_request_template.md", ".gitlab/merge_request_templates/Default.md")
CI_TARGETS = {
    "github": ("ci/github.yml", ".github/workflows/vbench.yml"),
    "gitlab": ("ci/gitlab.yml", ".gitlab-ci.vbench.yml"),
}
SETTINGS = ".claude/settings.json"
# Read-only or local-only commands that need no prompt. `init`, `update` and the gate scripts are left out on
# purpose: they write files, install software or run the project's own command strings, so Claude Code asks.
ALLOW = [
    "Bash(vbench check:*)",
    "Bash(vbench status:*)",
    "Bash(vbench next:*)",
    "Bash(vbench sync:*)",
    "Bash(vbench export:*)",
    "Bash(vbench new uc:*)",
    "Bash(vbench new discovery:*)",
    "Bash(vbench --version)",
]
PLACEHOLDER_URL = "https://<host>/<org>/vbench.git"


@dataclass
class InitReport:
    written: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    plugin_enabled: bool = False
    stack: str = "none"
    package: str = ""
    skeleton: bool = False  # the stack's application skeleton was written
    skeleton_skipped: bool = False  # the folder already had a pyproject.toml, so it was left alone


def _render(text: str, subs: dict[str, str]) -> str:
    for k, v in subs.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def _quote(items: list[str]) -> str:
    return "[" + ", ".join(f'"{i}"' for i in items) + "]"


STACK_DOC_ROW = (
    "| [Technology stack](04-technology-stack.md) | What the project is built on, and why | `/vbench:v-2-design` |"
)
COMMANDS_MARK = "# Commands the /vbench:*"


def init_project(
    ws: Workspace,
    templates: Templates,
    install_info: InstallInfo,
    *,
    version: str,
    prod: list[str],
    tests: list[str],
    ci: str = "both",
    force: bool = False,
    stack: str = "python-fastapi",
    name: str = "project",
) -> InitReport:
    if stack not in STACKS:
        raise UsageError(f"unknown stack `{stack}`; choose one of: {', '.join(STACKS)}")
    origin = install_info.origin()
    url = origin.url.removeprefix("git+") if origin and origin.is_git else ""
    package = package_name(name) if stack != "none" else ""
    subs = {
        "VBENCH_VERSION": version,
        "VBENCH_SOURCE": f"git+{url or PLACEHOLDER_URL}@v{version}",
        "STACK": "" if stack == "none" else stack,
        "PACKAGE": package,
        "NAME": display_name(name),
        "DIST": dist_name(name),
    }
    report = InitReport(stack=stack, package=package)
    base = f"stacks/{stack}/"
    stack_files = [n for n in templates.names(f"stacks/{stack}")] if stack != "none" else []

    def put(rel: str, text: str) -> None:
        (report.written if ws.write(rel, text, overwrite=force) else report.skipped).append(rel)

    cfg = _render(templates.read("config.toml"), subs)
    cfg = cfg.replace('prod = ["src"]', f"prod = {_quote(prod)}").replace(
        'tests = ["tests"]', f"tests = {_quote(tests)}"
    )
    if f"{base}config.commands.toml" in stack_files:  # the stack's gate commands replace the generic ones
        cfg = cfg[: cfg.index(COMMANDS_MARK)] + templates.read(f"{base}config.commands.toml")
    put(CONFIG_PATH, cfg)

    docs = {n: templates.read(n) for n in templates.names("docs")}
    for n in stack_files:  # a stack's own docs add to the docs, or replace the generic file of the same name
        if n.startswith(f"{base}docs/"):
            docs[n.removeprefix(base)] = _render(templates.read(n), subs)
    row = STACK_DOC_ROW + "\n" if any(n == f"{base}docs/04-technology-stack.md" for n in stack_files) else ""
    for dst, text in docs.items():
        put(dst, text.replace("{{STACK_DOC_ROW}}\n", row))

    for host, (src, dst) in CI_TARGETS.items():
        if ci in (host, "both"):
            text = _render(templates.read(src), subs)
            job = f"{base}ci/{host}-app-job.yml"
            put(dst, text + (_render(templates.read(job), subs) if job in stack_files else ""))
    for src, (dst, hosts) in REPO_FILES.items():
        if ci in hosts:
            put(dst, templates.read(src))
    if ci in ("gitlab", "both"):
        put(GITLAB_MR[1], templates.read(GITLAB_MR[0]))

    skeleton = [
        n
        for n in stack_files
        if not n.startswith((f"{base}docs/", f"{base}ci/")) and not n.endswith("config.commands.toml")
    ]
    if skeleton and ws.exists("pyproject.toml") and not force:
        report.skeleton_skipped = True  # an existing project: harness, docs and CI only
    elif skeleton:
        for n in skeleton:
            put(n.removeprefix(base).replace("src/__package__", f"src/{package}"), _render(templates.read(n), subs))
        put(".importlinter", importlinter_text(package, []))
        report.skeleton = True
    data = json.loads(ws.read(SETTINGS)) if ws.exists(SETTINGS) else {}
    allow = data.setdefault("permissions", {}).setdefault("allow", [])
    allow += [rule for rule in ALLOW if rule not in allow]
    if url:
        data.setdefault("extraKnownMarketplaces", {}).setdefault("vbench", {"source": {"source": "git", "url": url}})
        data.setdefault("enabledPlugins", {}).setdefault("vbench@vbench", True)
        report.plugin_enabled = True
    ws.write(SETTINGS, json.dumps(data, indent=2) + "\n")
    report.written.append(SETTINGS)
    return report
