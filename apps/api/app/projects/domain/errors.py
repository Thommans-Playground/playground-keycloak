"""Projects' own error base. No shared kernel (ADR 0010, 0015)."""


class ProjectsError(Exception):
    code = "projects_error"

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message


class NotAnAdministrator(ProjectsError):
    code = "forbidden"


class InvalidProjectName(ProjectsError):
    code = "invalid_project_name"


class InvalidRequest(ProjectsError):
    code = "invalid_request"


class MemberNotEligible(ProjectsError):
    """One answer for a first member who is pending, deactivated or unknown: it names no id and no status (AC-13)."""

    code = "member_not_eligible"

    def __init__(self):
        super().__init__("That person cannot be added to or removed from this project.")


class ProjectNotFound(ProjectsError):
    """One answer for a project that is hidden, one that does not exist and an id that is not well formed (AC-27)."""

    code = "project_not_found"

    def __init__(self):
        super().__init__("Project not found.")
