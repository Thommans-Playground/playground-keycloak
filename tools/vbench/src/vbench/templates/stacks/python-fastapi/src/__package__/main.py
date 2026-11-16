"""The FastAPI application: a driving adapter.

Routes translate HTTP into use-case calls and hold no rules. Each bounded context adds its own
router under `{{PACKAGE}}.<context>.adapters.inbound`; wire them in here.
"""

from fastapi import FastAPI

from {{PACKAGE}}.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title=get_settings().app_name)

    @app.get("/health", tags=["ops"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
