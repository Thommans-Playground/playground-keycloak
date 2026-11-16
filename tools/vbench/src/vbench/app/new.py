"""Use case: allocate the next use-case id and scaffold its spec."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.config import Config
from ..domain.contexts import CONTEXT_MAP, at, context_files, next_context_number
from ..domain.errors import UsageError
from ..domain.ids import ALLOCATABLE, collect_id_texts, next_ids, next_uc_id
from ..domain.scaffold import TEMPLATE, spec_text
from ..domain.specs import slug
from ..domain.stack import LAYERS, code_contexts, context_package, importlinter_text
from ..ports import Templates, Workspace
from .sync import sync

SLUG = re.compile(r"[^a-z0-9]+")


def spec_template(cfg: Config, ws: Workspace, templates: Templates) -> str:
    """The project's own spec template when it has one, otherwise the one vbench ships."""
    local = f"{cfg.specs.rstrip('/')}/_TEMPLATE.md"
    return ws.read(local) if ws.exists(local) else templates.read(TEMPLATE)


@dataclass
class NewUseCase:
    uc: str
    path: str
    rigor: str


def new_use_case(
    cfg: Config, ws: Workspace, templates: Templates, area: str, title: str, slug: str | None = None
) -> NewUseCase:
    area = area.upper()
    if not re.fullmatch(r"[A-Z]", area):
        raise UsageError("--area must be a single letter (the area code, e.g. A for Authentication).")
    slug = SLUG.sub("-", (slug or title).lower()).strip("-")
    if not slug:
        raise UsageError("Could not derive a slug; pass --slug.")

    specs = cfg.specs.rstrip("/")
    spec_names = [p.rsplit("/", 1)[-1] for p in ws.files([specs], [".md"])]
    texts = (ws.read(p) for p in [*ws.files(cfg.prod, cfg.prod_ext), *ws.files(cfg.tests, cfg.test_ext)])
    uc = next_uc_id(area, spec_names, texts)
    ac, task = next_ids("ac", area, collect_id_texts(cfg, ws))[0], next_ids("task", area, collect_id_texts(cfg, ws))[0]

    body = spec_text(cfg, spec_template(cfg, ws, templates), uc, title, ac, task)
    path = f"{specs}/{uc}-{slug}.md"
    ws.write(path, body)
    sync(cfg, ws)  # the overall use-case diagram follows the specs
    return NewUseCase(uc, path, cfg.rigor_default)


def next_free_ids(cfg: Config, ws: Workspace, kind: str, area: str | None, count: int) -> list[str]:
    """The next `count` unused ids of a kind (`vbench id fr`), without writing anything."""
    if kind not in ALLOCATABLE:
        raise UsageError(f"unknown id kind `{kind}`; choose one of {', '.join(ALLOCATABLE)}.")
    if ALLOCATABLE[kind][1]:
        area = (area or "").upper()
        if not re.fullmatch(r"[A-Z]", area):
            raise UsageError(f"--area is a single letter (the area code) for `{kind}` ids.")
    return next_ids(kind, area or "", collect_id_texts(cfg, ws), max(1, count))


def _ident(name: str) -> str:
    return "".join(w.capitalize() for w in slug(name).split("-")) or "Context"


def new_context(cfg: Config, ws: Workspace, templates: Templates, name: str) -> list[str]:
    """Create `<NN>-<context>-ddd.puml` from the skeleton; NN is the next free tier (10, 20, ...). With the
    python-fastapi stack it also creates the context's code package and rewrites the architecture contract.
    Returns the paths created, the diagram first."""
    s = slug(name)
    if not s:
        raise UsageError("Could not derive a file name from --name.")
    if s in context_files(cfg, ws):
        raise UsageError(f"context `{name}` already has {context_files(cfg, ws)[s]}")
    path = at(cfg, f"{next_context_number(cfg, ws):02d}-{s}-ddd.puml")
    body = templates.read("diagrams/context-ddd.puml").replace("{{ID}}", _ident(name)).replace("{{NAME}}", name.strip())
    ws.write(path, body)
    created = [path]
    if cfg.stack == "python-fastapi" and cfg.package and cfg.prod:
        root = f"{cfg.prod[0].rstrip('/')}/{cfg.package}/{context_package(s)}"
        for sub, doc in LAYERS.items():
            rel = f"{root}/{sub}/__init__.py" if sub else f"{root}/__init__.py"
            if ws.write(rel, f'"""{doc.format(name=name.strip())}"""\n', overwrite=False):
                created.append(rel)
        contract = ".importlinter"
        ws.write(contract, importlinter_text(cfg.package, code_contexts(cfg, ws)))
        created.append(contract)
    return created


def new_context_map(cfg: Config, ws: Workspace, templates: Templates) -> str:
    """Create the context map with one package per existing context model. Needs two or more."""
    files = context_files(cfg, ws)
    if len(files) < 2:
        raise UsageError("A context map relates contexts: create two or more first (`vbench new context --name ...`).")
    path = at(cfg, CONTEXT_MAP)
    if ws.exists(path):
        raise UsageError(f"{path} already exists; edit it (it is authored, not generated).")
    packages = "\n".join(
        f'package "{" ".join(w.capitalize() for w in sl.split("-"))}\\n«Supporting»" as {_ident(sl)} #F0F0F0'
        for sl in sorted(files)
    )
    ws.write(path, templates.read("diagrams/context-map.puml").replace("{{PACKAGES}}", packages))
    return path


def new_discovery(cfg: Config, ws: Workspace, templates: Templates, title: str) -> str:
    """Create `<discovery folder>/<slug>.md` from the brief template, as a draft. The interview fills it in."""
    s = slug(title)
    if not s:
        raise UsageError("Could not derive a file name from --title.")
    path = f"{cfg.discovery.rstrip('/')}/{s}.md"
    if ws.exists(path):
        raise UsageError(f"{path} already exists; continue that brief or choose another title.")
    local = f"{cfg.discovery.rstrip('/')}/_TEMPLATE.md"
    body = ws.read(local) if ws.exists(local) else templates.read("docs/discovery/_TEMPLATE.md")
    ws.write(path, body.replace("# Discovery: <idea>", f"# Discovery: {title.strip()}", 1))
    return path
