"""Use case: what is the one thing to do next."""

from __future__ import annotations

from ..domain.briefs import read_briefs
from ..domain.config import Config
from ..domain.model import NextStep
from ..domain.next import next_step, ready_steps
from ..domain.status import derive_status
from ..ports import Workspace


def what_next(cfg: Config, ws: Workspace) -> NextStep:
    return next_step(derive_status(cfg, ws).rows, read_briefs(cfg, ws))


def what_is_ready(cfg: Config, ws: Workspace) -> list[NextStep]:
    """All the steps that can start now, for parallel work (`vbench next --ready`)."""
    return ready_steps(derive_status(cfg, ws).rows, read_briefs(cfg, ws))
