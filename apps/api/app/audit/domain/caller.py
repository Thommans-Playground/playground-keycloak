"""Who is asking, in Audit's own words (decision 14, ADR 0011). Composition translates the guard's result into it."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Caller:
    account_id: str
    is_administrator: bool
