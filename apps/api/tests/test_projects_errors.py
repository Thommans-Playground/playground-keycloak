"""How HTTP answers a Projects rule refusal: the body the web reads (detail.code). No rule refuses yet; later slices
add the statuses."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.projects.adapters.inbound.errors import register_error_handlers
from app.projects.domain.errors import ProjectsError


def test_a_projects_refusal_is_answered_with_its_code_and_message():
    class Odd(ProjectsError):
        code = "odd"

    app = FastAPI()
    register_error_handlers(app)

    @app.get("/x")
    def x():
        raise Odd("No.")

    r = TestClient(app).get("/x")
    assert (r.status_code, r.json()) == (400, {"detail": {"code": "odd", "message": "No."}})
