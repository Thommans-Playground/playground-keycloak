"""Errors the core raises; the driving adapter maps them to exit codes."""


class VBenchError(Exception):
    pass


class ConfigError(VBenchError):
    pass


class UsageError(VBenchError):
    pass


class RefusedError(VBenchError):
    """The request was understood and the work is not ready (an unfinished task, tests not confirmed). Exits 1."""


class AmbiguousError(UsageError):
    """More than one answer fits, and guessing would be wrong; the message lists them. Exits 2, not 1."""


class UpdateError(VBenchError):
    pass


class AgentError(VBenchError):
    """The agent could not answer: it is not set up, it refused, it failed, or it answered something unusable."""


class StaleError(VBenchError):
    """The files changed since the change was previewed, so what was shown is no longer what would be written."""
