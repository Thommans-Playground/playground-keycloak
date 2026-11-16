"""`Agent` backed by Claude, through the official Anthropic SDK.

The SDK is an optional extra (`pip install "vbench[agent]"`) and is imported only when an answer is asked for, so the
rest of vbench stays free of dependencies. Credentials are the SDK's own: `ANTHROPIC_API_KEY`, or a profile from
`ant auth login`. The model answers in a JSON shape it is held to (structured output), at a stated effort, and every
way it can fail (no key, rate limit, refusal, cut off, not JSON) becomes an `AgentError` the caller can show.
"""

from __future__ import annotations

import importlib.util
import json
from typing import Any

from ..domain.errors import AgentError
from ..ports import Agent

DEFAULT_MODEL = "claude-opus-5-5"
INSTALL = 'The Anthropic SDK is not installed. Install it with: pip install "vbench[agent]"'


def sdk_available() -> bool:
    return importlib.util.find_spec("anthropic") is not None


class ClaudeAgent:
    name = "Claude"

    def __init__(self, model: str | None = None, client: Any = None) -> None:
        self.model = model or DEFAULT_MODEL
        self._client = client

    def _connect(self) -> Any:
        try:
            import anthropic
        except ImportError as e:
            raise AgentError(INSTALL) from e
        return anthropic.Anthropic(timeout=90.0, max_retries=1)

    @staticmethod
    def _explain(error: Exception) -> AgentError:
        """What went wrong, in words a person can act on. The SDK's typed errors, most specific first."""
        try:
            import anthropic
        except ImportError:
            return AgentError(f"Claude could not answer: {type(error).__name__}")
        if isinstance(error, anthropic.AuthenticationError):
            return AgentError("Claude did not accept the credentials. Set ANTHROPIC_API_KEY, or run `ant auth login`.")
        if isinstance(error, anthropic.RateLimitError):
            return AgentError("Claude is rate limiting this account; try again in a minute.")
        if isinstance(error, anthropic.APIConnectionError):
            return AgentError("Claude could not be reached; check the network.")
        if isinstance(error, anthropic.APIStatusError):
            return AgentError(f"Claude answered with an error ({error.status_code}): {error.message}")
        return AgentError(f"Claude could not answer: {type(error).__name__}")

    def structured(self, system: str, user: str, schema: dict) -> dict:
        client = self._client or self._connect()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
            )
        except Exception as e:
            raise self._explain(e) from e

        if response.stop_reason == "refusal":
            raise AgentError("Claude declined to answer this one.")
        if response.stop_reason == "max_tokens":
            raise AgentError("Claude's answer was cut off.")
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            data = json.loads(text)
        except ValueError as e:
            raise AgentError("Claude's answer was not valid JSON.") from e
        if not isinstance(data, dict):
            raise AgentError("Claude's answer was not an object.")
        return data


def make_agent(kind: str, model: str | None = None) -> Agent | None:
    """The agent a command line asked for, or None for none. Raises `AgentError` when it cannot be set up."""
    if kind == "none":
        return None
    if kind == "claude":
        if not sdk_available():
            raise AgentError(INSTALL)
        return ClaudeAgent(model)
    if kind == "openai":
        from .openai_agent import INSTALL as OPENAI_INSTALL
        from .openai_agent import OpenAIAgent
        from .openai_agent import sdk_available as openai_available

        if not openai_available():
            raise AgentError(OPENAI_INSTALL)
        return OpenAIAgent(model)
    raise AgentError(f"unknown agent `{kind}`; choose none, claude or openai")
