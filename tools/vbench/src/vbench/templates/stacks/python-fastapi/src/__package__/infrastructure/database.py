"""PostgreSQL access through SQLAlchemy 2.

Contexts keep their own models and repositories in their outbound adapters.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """The declarative base for the SQLAlchemy models in the contexts' outbound adapters."""


def make_session_factory(url: str) -> sessionmaker[Session]:
    return sessionmaker(create_engine(url, pool_pre_ping=True), expire_on_commit=False)
