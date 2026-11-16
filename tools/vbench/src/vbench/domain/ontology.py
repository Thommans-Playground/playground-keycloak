"""The project's ontology, derived from what is already written: never authored, never stored by hand.

Two layers. The *method* layer is fixed: the classes vbench knows (Problem, Request, Requirement, UseCase, Criterion,
Task, Step, Test, ...) and the relations between them. The *project* layer is this repository's individuals: its ids,
the edges the trace derives from the documents and tags, its bounded contexts and the terms of its vocabulary.

Rendering is plain text in four formats, all from one model: Turtle (OWL 2 written as RDF), RDF/XML (OWL, what Protege
opens), JSON-LD and YAML. No library is involved and no reasoner is implied: the file states facts, it infers nothing.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from urllib.parse import quote
from xml.sax.saxutils import escape, quoteattr

from ..ports import Workspace
from .checks import collect_realised, collect_step_rows, collect_tasks, collect_verified, spec_files
from .config import Config
from .graph import read_links
from .model import natural_key
from .specs import read_specs, slug
from .trace import build_trace
from .vocabulary import read_terms, slug_of

METHOD = "urn:vbench:method:"
FORMATS = ("ttl", "owl", "jsonld", "yaml")
EXTENSION = {"ttl": "ttl", "owl": "owl", "jsonld": "jsonld", "yaml": "yaml"}

# class -> what it is
CLASSES: dict[str, str] = {
    "Problem": "Something a stakeholder suffers from.",
    "Request": "A stakeholder's raw ask, in their words.",
    "Requirement": "A functional or quality requirement a request leads to.",
    "UseCase": "What an actor achieves; the unit of delivery.",
    "Criterion": "A testable acceptance criterion of a use case.",
    "Task": "A commit-sized piece of a use case that ends with a passing test.",
    "Step": "One numbered message of a use case's sequence diagram.",
    "Test": "A test that proves criteria.",
    "CodeFile": "A production file that realises a use case or a step.",
    "TestFile": "A test file that verifies a use case or a step.",
    "BoundedContext": "A part of the system with its own model and vocabulary.",
    "Term": "A word of the project's ubiquitous language.",
}

# property -> (domain, range, comment)
RELATIONS: dict[str, tuple[str, str, str]] = {
    "concernsProblem": ("Request", "Problem", "The problem a request is about."),
    "satisfiesRequest": ("Requirement", "Request", "The request a requirement answers."),
    "realisesRequirement": ("UseCase", "Requirement", "A requirement a use case realises."),
    "dependsOn": ("UseCase", "UseCase", "A use case that must be built first."),
    "criterionOf": ("Criterion", "UseCase", "The use case a criterion belongs to."),
    "satisfiesRequirement": ("Criterion", "Requirement", "A requirement a criterion makes testable."),
    "verifiesCriterion": ("Test", "Criterion", "A criterion a test proves."),
    "taskOf": ("Task", "UseCase", "The use case a task belongs to."),
    "closesCriterion": ("Task", "Criterion", "A criterion a task closes."),
    "buildsStep": ("Task", "Step", "A sequence step a task builds."),
    "stepOf": ("Step", "UseCase", "The use case whose sequence diagram holds a step."),
    "stepRealisedIn": ("Step", "CodeFile", "Code that carries `Realises UC-… · STP-…` for the step."),
    "stepDrivenBy": ("Step", "TestFile", "A test file with a real test that says it drives the step."),
    "realisedIn": ("UseCase", "CodeFile", "Code tagged `Realises` for the use case."),
    "verifiedBy": ("UseCase", "TestFile", "A test file tagged `Verifies` for the use case."),
    "inContext": ("UseCase", "BoundedContext", "The bounded context a use case lives in."),
    "termInContext": ("Term", "BoundedContext", "The bounded context a term belongs to."),
    "notToBeConfusedWith": ("Term", "Term", "A defined term this one is not."),
}
DATA = {
    "planned": "True when the step is marked (planned) in the diagram: not built yet.",
    "confusedWith": "A word the vocabulary says this term is not (it is not itself a defined term).",
}

KIND_CLASS = {
    "problem": "Problem",
    "request": "Request",
    "requirement": "Requirement",
    "usecase": "UseCase",
    "criterion": "Criterion",
    "test": "Test",
}
TRACE_EDGE = {
    ("request", "problem"): "concernsProblem",
    ("requirement", "request"): "satisfiesRequest",
    ("usecase", "requirement"): "realisesRequirement",
    ("criterion", "usecase"): "criterionOf",
    ("criterion", "requirement"): "satisfiesRequirement",
    ("test", "criterion"): "verifiesCriterion",
}


@dataclass
class Individual:
    local: str
    cls: str
    label: str
    comment: str = ""
    edges: list[tuple[str, str]] = field(default_factory=list)  # (relation, target local name)
    data: list[tuple[str, str | bool]] = field(default_factory=list)  # (data property, literal)


@dataclass
class Ontology:
    iri: str  # the project namespace
    individuals: dict[str, Individual]


def _n(local: str) -> str:
    """A local name safe in an IRI and in a Turtle prefixed name (a test id has `/`, `:` and `.` in it)."""
    return quote(local, safe="-_")


def _file(path: str) -> str:
    return "file-" + slug_of(path)


def build_ontology(cfg: Config, ws: Workspace) -> Ontology:
    people: dict[str, Individual] = {}

    def add(local: str, cls: str, label: str, comment: str = "") -> Individual:
        return people.setdefault(local, Individual(local, cls, " ".join(label.split()), comment))

    def edge(src: str, rel: str, dst: str) -> None:
        if src in people and dst in people and (rel, dst) not in people[src].edges:
            people[src].edges.append((rel, dst))

    trace = build_trace(cfg, ws)
    for id_, kind in trace.kinds.items():
        add(id_, KIND_CLASS[kind], trace.labels.get(id_, id_))
    for child, parents in trace.parents.items():
        for parent in parents:
            rel = TRACE_EDGE.get((trace.kinds.get(child, ""), trace.kinds.get(parent, "")))
            if rel:
                edge(child, rel, parent)

    specs = read_specs(cfg, ws)
    for s in specs:
        add(s.uc, "UseCase", s.title)
        if s.context:
            ctx = add("ctx-" + slug(s.context), "BoundedContext", s.context)
            edge(s.uc, "inContext", ctx.local)
    for uc, deps in read_links(cfg, ws).items():
        for dep in deps:
            edge(uc, "dependsOn", dep)

    owner = {p: uc for uc, p in spec_files(cfg, ws).items()}
    for tsk, (path, acs) in collect_tasks(cfg, ws).items():
        t = add(tsk, "Task", tsk)
        if path in owner:
            edge(tsk, "taskOf", owner[path])
        for ac in acs:
            edge(t.local, "closesCriterion", ac)
    for r in collect_step_rows(cfg, ws)[0]:
        s = r.step
        step = add(s.id, "Step", s.label or s.id)
        step.data.append(("planned", s.planned))
        edge(s.id, "stepOf", s.uc)
        for tsk in r.tasks:
            edge(tsk, "buildsStep", s.id)
        for path, _ in r.code:
            add(_file(path), "CodeFile", path)
            edge(s.id, "stepRealisedIn", _file(path))
        for path in r.tests:
            add(_file(path), "TestFile", path)
            edge(s.id, "stepDrivenBy", _file(path))
    for uc, paths in collect_realised(cfg, ws).items():
        for path in sorted(paths):
            add(_file(path), "CodeFile", path)
            edge(uc, "realisedIn", _file(path))
    for uc, pairs in collect_verified(cfg, ws).items():
        for path, _ in sorted(pairs):
            add(_file(path), "TestFile", path)
            edge(uc, "verifiedBy", _file(path))

    terms = read_terms(cfg, ws)
    for t in terms:
        term = add("term-" + slug_of(t.name), "Term", t.name, t.definition)
        if t.context:
            ctx = add("ctx-" + slug(t.context), "BoundedContext", t.context)
            edge(term.local, "termInContext", ctx.local)
    defined = {slug_of(t.name): "term-" + slug_of(t.name) for t in terms}
    for t in terms:
        me = "term-" + slug_of(t.name)
        for word in t.confusable:
            if slug_of(word) in defined:
                edge(me, "notToBeConfusedWith", defined[slug_of(word)])
            else:
                people[me].data.append(("confusedWith", word))
    return Ontology(cfg.ontology_iri, people)


# ------------------------------------------------------------------------------------------------ rendering
def _sorted(o: Ontology) -> list[Individual]:
    return sorted(o.individuals.values(), key=lambda i: (i.cls, natural_key(i.local)))


def _lit(text: str) -> str:
    """A double-quoted string that is valid JSON, Turtle and YAML alike."""
    esc = {'"': '\\"', "\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t"}
    body = "".join(esc.get(c) or (f"\\u{ord(c):04x}" if ord(c) < 0x20 else c) for c in text)
    return f'"{body}"'


def _json(value, level: int = 0) -> str:
    """A small JSON writer (two-space indent, insertion order), because the core imports no I/O or serialiser."""
    pad, inner = "  " * level, "  " * (level + 1)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _lit(value)
    if isinstance(value, dict):
        rows = [f"{inner}{_lit(k)}: {_json(v, level + 1)}" for k, v in value.items()]
        return "{\n" + ",\n".join(rows) + f"\n{pad}}}" if rows else "{}"
    rows = [f"{inner}{_json(v, level + 1)}" for v in value]
    return "[\n" + ",\n".join(rows) + f"\n{pad}]" if rows else "[]"


def _ttl_value(v: str | bool) -> str:
    return ("true" if v else "false") if isinstance(v, bool) else _lit(v)


def to_turtle(o: Ontology) -> str:
    out = [
        "# Generated by `vbench ontology`. Do not edit: it is derived from the specs, tags and vocabulary.",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        f"@prefix vb: <{METHOD}> .",
        f"@prefix p: <{o.iri}> .",
        "",
        f'<{o.iri}ontology> a owl:Ontology ; rdfs:label "vbench project ontology" .',
        "",
    ]
    for name, comment in CLASSES.items():
        out.append(f"vb:{name} a owl:Class ; rdfs:label {_lit(name)} ; rdfs:comment {_lit(comment)} .")
    out.append("")
    for name, (dom, rng, comment) in RELATIONS.items():
        kind = "owl:ObjectProperty, owl:SymmetricProperty" if name == "notToBeConfusedWith" else "owl:ObjectProperty"
        out.append(f"vb:{name} a {kind} ; rdfs:domain vb:{dom} ; rdfs:range vb:{rng} ; rdfs:comment {_lit(comment)} .")
    for name, comment in DATA.items():
        rng = "xsd:boolean" if name == "planned" else "xsd:string"
        out.append(f"vb:{name} a owl:DatatypeProperty ; rdfs:range {rng} ; rdfs:comment {_lit(comment)} .")
    out.append("")
    for i in _sorted(o):
        parts = [f"a vb:{i.cls}", f"rdfs:label {_lit(i.label)}"]
        if i.comment:
            parts.append(f"rdfs:comment {_lit(i.comment)}")
        parts += [f"vb:{rel} p:{_n(dst)}" for rel, dst in sorted(i.edges, key=lambda e: (e[0], natural_key(e[1])))]
        parts += [f"vb:{k} {_ttl_value(v)}" for k, v in i.data]
        out.append(f"p:{_n(i.local)} " + " ;\n    ".join(parts) + " .")
    return "\n".join(out) + "\n"


def to_rdfxml(o: Ontology) -> str:
    q = quoteattr
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!-- Generated by `vbench ontology`. Do not edit: it is derived from the specs, tags and vocabulary. -->",
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"',
        '         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"',
        '         xmlns:owl="http://www.w3.org/2002/07/owl#"',
        '         xmlns:xsd="http://www.w3.org/2001/XMLSchema#"',
        f"         xmlns:vb={q(METHOD)}",
        f"         xmlns:p={q(o.iri)}>",
        f"  <owl:Ontology rdf:about={q(o.iri + 'ontology')}>",
        "    <rdfs:label>vbench project ontology</rdfs:label></owl:Ontology>",
    ]
    for name, comment in CLASSES.items():
        out.append(
            f"  <owl:Class rdf:about={q(METHOD + name)}><rdfs:label>{escape(name)}</rdfs:label>"
            f"<rdfs:comment>{escape(comment)}</rdfs:comment></owl:Class>"
        )
    for name, (dom, rng, comment) in RELATIONS.items():
        extra = (
            '<rdf:type rdf:resource="http://www.w3.org/2002/07/owl#SymmetricProperty"/>'
            if name == "notToBeConfusedWith"
            else ""
        )
        out.append(
            f"  <owl:ObjectProperty rdf:about={q(METHOD + name)}>{extra}<rdfs:domain rdf:resource={q(METHOD + dom)}/>"
            f"<rdfs:range rdf:resource={q(METHOD + rng)}/><rdfs:comment>{escape(comment)}</rdfs:comment>"
            "</owl:ObjectProperty>"
        )
    for name, comment in DATA.items():
        rng = "http://www.w3.org/2001/XMLSchema#" + ("boolean" if name == "planned" else "string")
        out.append(
            f"  <owl:DatatypeProperty rdf:about={q(METHOD + name)}><rdfs:range rdf:resource={q(rng)}/>"
            f"<rdfs:comment>{escape(comment)}</rdfs:comment></owl:DatatypeProperty>"
        )
    for i in _sorted(o):
        body = [f"<rdf:type rdf:resource={q(METHOD + i.cls)}/>", f"<rdfs:label>{escape(i.label)}</rdfs:label>"]
        if i.comment:
            body.append(f"<rdfs:comment>{escape(i.comment)}</rdfs:comment>")
        body += [
            f"<vb:{rel} rdf:resource={q(o.iri + _n(dst))}/>"
            for rel, dst in sorted(i.edges, key=lambda e: (e[0], natural_key(e[1])))
        ]
        for k, v in i.data:
            if isinstance(v, bool):
                body.append(
                    f'<vb:{k} rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">{str(v).lower()}</vb:{k}>'
                )
            else:
                body.append(f"<vb:{k}>{escape(v)}</vb:{k}>")
        out.append(f"  <rdf:Description rdf:about={q(o.iri + _n(i.local))}>" + "".join(body) + "</rdf:Description>")
    out.append("</rdf:RDF>")
    return "\n".join(out) + "\n"


def to_jsonld(o: Ontology) -> str:
    graph: list[dict] = [{"@id": f"{o.iri}ontology", "@type": "owl:Ontology", "rdfs:label": "vbench project ontology"}]
    for name, comment in CLASSES.items():
        graph.append({"@id": f"vb:{name}", "@type": "owl:Class", "rdfs:label": name, "rdfs:comment": comment})
    for name, (dom, rng, comment) in RELATIONS.items():
        graph.append(
            {
                "@id": f"vb:{name}",
                "@type": ["owl:ObjectProperty", "owl:SymmetricProperty"]
                if name == "notToBeConfusedWith"
                else "owl:ObjectProperty",
                "rdfs:domain": {"@id": f"vb:{dom}"},
                "rdfs:range": {"@id": f"vb:{rng}"},
                "rdfs:comment": comment,
            }
        )
    for name, comment in DATA.items():
        rng = "xsd:boolean" if name == "planned" else "xsd:string"
        graph.append(
            {"@id": f"vb:{name}", "@type": "owl:DatatypeProperty", "rdfs:range": {"@id": rng}, "rdfs:comment": comment}
        )
    for i in _sorted(o):
        node: dict = {"@id": f"p:{_n(i.local)}", "@type": f"vb:{i.cls}", "rdfs:label": i.label}
        if i.comment:
            node["rdfs:comment"] = i.comment
        grouped: dict[str, list] = defaultdict(list)
        for rel, dst in sorted(i.edges, key=lambda e: (e[0], natural_key(e[1]))):
            grouped[f"vb:{rel}"].append({"@id": f"p:{_n(dst)}"})
        for k, v in i.data:
            grouped[f"vb:{k}"].append(v)
        node.update({k: v[0] if len(v) == 1 else v for k, v in grouped.items()})
        graph.append(node)
    context = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "vb": METHOD,
        "p": o.iri,
    }
    return _json({"@context": context, "@graph": graph}) + "\n"


def to_yaml(o: Ontology) -> str:
    out = [
        "# Generated by `vbench ontology`. Do not edit: it is derived from the specs, tags and vocabulary.",
        f"ontology: {_lit(o.iri)}",
        f"method: {_lit(METHOD)}",
        "classes:",
    ]
    out += [f"  {name}: {_lit(comment)}" for name, comment in CLASSES.items()]
    out.append("relations:")
    for name, (dom, rng, comment) in RELATIONS.items():
        out.append(f"  {name}: {{domain: {dom}, range: {rng}, comment: {_lit(comment)}}}")
    out.append("individuals:")
    for i in _sorted(o):
        out.append(f"  {_lit(i.local)}:")
        out.append(f"    class: {i.cls}")
        out.append(f"    label: {_lit(i.label)}")
        if i.comment:
            out.append(f"    comment: {_lit(i.comment)}")
        by_rel: dict[str, list[str]] = defaultdict(list)
        for rel, dst in sorted(i.edges, key=lambda e: (e[0], natural_key(e[1]))):
            by_rel[rel].append(dst)
        for rel, targets in by_rel.items():
            out.append(f"    {rel}: [{', '.join(_lit(t) for t in targets)}]")
        for k, v in i.data:
            out.append(f"    {k}: {_ttl_value(v)}")
    return "\n".join(out) + "\n"


RENDER = {"ttl": to_turtle, "owl": to_rdfxml, "jsonld": to_jsonld, "yaml": to_yaml}


def render(o: Ontology, fmt: str) -> str:
    return RENDER[fmt](o)


def file_name(fmt: str) -> str:
    return f"project.{EXTENSION[fmt]}"
