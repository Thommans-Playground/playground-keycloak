"""Audit's own error base. No shared kernel (ADR 0010, 0011)."""


class AuditError(Exception):
    code = "audit_error"

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message


class NotAnAdministrator(AuditError):
    code = "forbidden"
