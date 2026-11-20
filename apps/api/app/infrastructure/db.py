"""The declarative base every context's tables register on. It belongs to no context (ADR 0004, decision 14)."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
