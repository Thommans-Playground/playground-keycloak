"""Projects' own error base. No shared kernel (ADR 0010, 0015)."""


class ProjectsError(Exception):
    code = "projects_error"

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message


class NotAnAdministrator(ProjectsError):
    code = "forbidden"
