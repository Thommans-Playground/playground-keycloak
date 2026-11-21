"""Who is asking, in Projects' own words (ADR 0002, 0015). Composition translates the guard's result into it."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Caller:
    account_id: str
    is_administrator: bool
