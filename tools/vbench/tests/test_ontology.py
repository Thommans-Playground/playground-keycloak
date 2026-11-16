"""Verifies the vocabulary and ontology: terms read as data, the confusion check, and the four generated formats."""

from __future__ import annotations

import json
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from vbench import cli
from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.domain.checks import check_ontology, check_vocabulary
from vbench.domain.ontology import FORMATS, build_ontology, render
from vbench.domain.vocabulary import Term, confusions, names_in_diagram, read_terms

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "notes-app"
VOCAB = """
## 2. Vocabulary (ubiquitous language)

| Term | Definition | Context | Not to be confused with |
|------|------------|---------|-------------------------|
| Note | A piece of text the author keeps. | Notes | Document, memo |
| Body | The text of a note. | Notes | Content |
"""


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text), encoding="utf-8")


def ctx(proj: Path):
    return load_config(proj), FsWorkspace(proj)


def with_vocabulary(proj: Path) -> None:
    path = proj / "docs/00-requirements-engineering.md"
    path.write_text(path.read_text() + VOCAB, encoding="utf-8")


def test_terms_are_read_from_the_vocabulary_table_and_a_placeholder_row_is_skipped(proj: Path):
    assert read_terms(*ctx(proj)) == []  # the template ships one placeholder row
    with_vocabulary(proj)
    terms = read_terms(*ctx(proj))
    assert [t.name for t in terms] == ["Note", "Body"]
    assert terms[0].confusable == ("Document", "memo") and terms[0].context == "Notes"


def test_a_diagram_name_is_flagged_when_it_uses_a_word_the_vocabulary_rules_out():
    terms = [Term("Note", "", "Notes", ("Document", "memo")), Term("Body", "", "Notes", ("Content",))]
    puml = 'participant "«service»\\nCreateNote" as S\nclass DocumentStore\nactor "Author" as U\nclass MemoryCache\n'
    assert names_in_diagram(puml) == ["CreateNote", "DocumentStore", "Author", "MemoryCache"]
    assert confusions(terms, names_in_diagram(puml)) == [("DocumentStore", "Document", "Note")]
    # a confusable word that is itself a defined term is a different concept, not a mistake
    assert confusions([*terms, Term("Document", "", "Docs", ())], ["DocumentStore"]) == []


def test_the_vocabulary_gate_fails_on_a_wrong_word_in_a_diagram_and_passes_without_terms(proj: Path):
    write(proj / "docs/usecase-diagrams/UC-A-001-thing-sequence.puml", "@startuml\nclass DocumentStore\n@enduml\n")
    assert check_vocabulary(*ctx(proj)).ok  # no vocabulary yet, so nothing is ruled out
    with_vocabulary(proj)
    res = check_vocabulary(*ctx(proj))
    assert not res.ok and '"DocumentStore" uses "Document", which the vocabulary says is not "Note"' in res.render()


@pytest.fixture
def example(tmp_path: Path) -> Path:
    import shutil

    root = tmp_path / "notes"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns(".vbench/ui", "node_modules", ".git", "__pycache__"))
    shutil.rmtree(root / "docs/ontology")  # the example ships the generated files; start from none
    return root


def test_the_examples_committed_ontology_matches_the_project():
    assert check_ontology(load_config(EXAMPLE), FsWorkspace(EXAMPLE)).ok


def test_the_ontology_holds_the_method_the_individuals_and_the_edges_between_them(example: Path):
    onto = build_ontology(*ctx(example))
    people = onto.individuals
    assert people["UC-N-001"].cls == "UseCase" and ("inContext", "ctx-notes") in people["UC-N-001"].edges
    assert ("realisesRequirement", "REQ-FR-001") in people["UC-N-001"].edges
    assert ("stepOf", "UC-N-001") in people["STP-N-002"].edges and ("planned", False) in people["STP-N-002"].data
    assert ("buildsStep", "STP-N-002") in people["TSK-N-002"].edges
    assert people["term-note"].cls == "Term" and people["term-note"].comment.startswith("A piece of text")
    assert ("confusedWith", "Document") in people["term-note"].data


@pytest.mark.parametrize("fmt", FORMATS)
def test_every_format_renders_the_same_ids_and_is_well_formed(example: Path, fmt: str):
    text = render(build_ontology(*ctx(example)), fmt)
    for needle in ("UC-N-001", "STP-N-003", "REQ-FR-001", "realisesRequirement", "BoundedContext"):
        assert needle in text
    if fmt == "owl":
        ET.fromstring(text)  # RDF/XML must parse
    if fmt == "jsonld":
        graph = json.loads(text)["@graph"]
        assert any(n["@id"] == "p:UC-N-001" and n["@type"] == "vb:UseCase" for n in graph)
    if fmt == "ttl":
        assert "a owl:Class" in text and "owl:SymmetricProperty" in text and text.count("@prefix") == 6
    assert render(build_ontology(*ctx(example)), fmt) == text  # deterministic


def test_a_test_id_with_path_characters_stays_a_valid_name(example: Path):
    ttl = render(build_ontology(*ctx(example)), "ttl")
    assert (
        "p:tests%2Ftest_create_note%2Epy%3A%3A" in ttl or "p:TST-" in ttl or "p:file-tests-test-create-note-py" in ttl
    )
    assert "p:tests/" not in ttl  # a bare `/` or `:` would not parse as a Turtle name


def test_write_creates_the_files_check_goes_stale_and_sync_refreshes_them(example: Path, capsys, monkeypatch):
    monkeypatch.chdir(example)
    assert check_ontology(*ctx(example)).lines[0].startswith("ontology: not generated")
    assert cli.main(["ontology", "--write"]) == 0
    for ext in ("ttl", "owl", "jsonld", "yaml"):
        assert (example / f"docs/ontology/project.{ext}").is_file()
    assert check_ontology(*ctx(example)).ok
    spec = example / "docs/usecase-diagrams/UC-N-001-create-note.md"
    spec.write_text(spec.read_text().replace("# UC-N-001 - Create note", "# UC-N-001 - Create a note"))
    assert not check_ontology(*ctx(example)).ok  # a committed copy that no longer matches fails
    assert cli.main(["sync"]) == 0
    assert check_ontology(*ctx(example)).ok  # sync refreshed the files that exist
    capsys.readouterr()
    assert cli.main(["ontology", "--format", "yaml"]) == 0
    assert "Create a note" in capsys.readouterr().out
