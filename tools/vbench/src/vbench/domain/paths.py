"""Which files a person or an agent may read or commit from outside the repo's own tooling: documentation only.

One rule for the dashboard's file endpoint and for `commit_changes`, so they cannot drift apart.
"""

from __future__ import annotations

import posixpath

from .config import Config

DOC_EXTENSIONS = (".md", ".puml")


def docs_path(cfg: Config, rel: str) -> str | None:
    """The normalised project-relative path if it is a .md/.puml file inside the docs or specs folder, else None."""
    if not rel or rel.startswith(("/", "\\")) or "\\" in rel or "\x00" in rel:
        return None
    norm = posixpath.normpath(rel)
    if norm.startswith("..") or ".." in norm.split("/") or not norm.endswith(DOC_EXTENSIONS):
        return None
    roots = [cfg.docs.rstrip("/"), cfg.specs.rstrip("/")]
    return norm if any(norm == r or norm.startswith(r + "/") for r in roots) else None


def branch_block(branch: str, base: str, allow_default: bool) -> str:
    """Why writing is refused on this branch (empty when it is allowed).

    A detached HEAD (no branch name) counts as unsafe, as does the default branch: a change there lands on the line
    everyone else builds on.
    """
    if allow_default:
        return ""
    if not branch:
        return (
            "HEAD is not on a branch (detached, or this is not a git repository). "
            "Switch to a branch, or start with --allow-default-branch."
        )
    if branch == base:
        return f"You are on `{base}`, the default branch. Switch branch, or start with --allow-default-branch."
    return ""
