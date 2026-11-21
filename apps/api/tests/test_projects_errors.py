"""How HTTP answers a Projects rule refusal: the body the web reads (detail.code). No rule refuses yet; later slices
add the statuses."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.projects.adapters.inbound.errors import register_error_handlers
from app.projects.domain.errors import NotAnAdministrator, ProjectsError
from tests.fakes import FakeSecurityLog


def test_a_projects_refusal_is_answered_with_its_code_and_message():
    class Odd(ProjectsError):
        code = "odd"

    app = FastAPI()
    register_error_handlers(app, FakeSecurityLog())

    @app.get("/x")
    def x():
        raise Odd("No.")

    r = TestClient(app).get("/x")
    assert (r.status_code, r.json()) == (400, {"detail": {"code": "odd", "message": "No."}})


def test_not_an_administrator_is_answered_with_a_403_and_the_forbidden_body():
    app = FastAPI()
    register_error_handlers(app, FakeSecurityLog())

    @app.get("/x")
    def x():
        raise NotAnAdministrator("Administrators only.")

    r = TestClient(app).get("/x")
    assert (r.status_code, r.json()) == (
        403,
        {"detail": {"code": "forbidden", "message": "Administrators only."}},
    )


def test_project_not_found_is_answered_with_a_404_and_one_fixed_body():
    from app.projects.domain.errors import ProjectNotFound

    app = FastAPI()
    log = FakeSecurityLog()
    register_error_handlers(app, log)

    @app.get("/x")
    def x():
        raise ProjectNotFound()

    r = TestClient(app).get("/x")
    assert (r.status_code, r.json()) == (
        404,
        {"detail": {"code": "project_not_found", "message": "Project not found."}},
    )
    assert [(e["event"], e["result"], e["reason"]) for e in log.events] == [
        ("request_refused", "refused", "project_not_found")
    ]
