"""Entry point: `uvicorn app.main:create_app --factory`. All wiring is in composition/."""

from app.composition.app import create_app

__all__ = ["create_app"]
