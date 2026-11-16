"""`Agent` and `ChatModel` backed by OpenAI, through the official SDK.

The SDK is an optional extra (`pip install "vbench[openai]"`), imported only when an answer is asked for. The key is the
SDK's own `OPENAI_API_KEY` and never leaves this process. Like the Claude adapter, every way it can fail (no key, a
rate limit, a refusal, a cut-off answer) becomes an `AgentError` the caller can show.
"""

from __future__ import annotations

import importlib.util
import json
import os
from collections.abc import Iterator
from typing import Any

from ..domain.errors import AgentError
from ..ports import ToolCall

DEFAULT_MODEL = "gpt-4.1"
INSTALL = 'The OpenAI SDK is not installed. Install it with: pip install "vbench[openai]"'


def sdk_available() -> bool:
    return importlib.util.find_spec("openai") is not None


class OpenAIAgent:
    name = "OpenAI"

    def __init__(self, model: str | None = None, client: Any = None) -> None:
        self.model = model or os.environ.get("VBENCH_OPENAI_MODEL") or DEFAULT_MODEL
        self._client = client

    def _connect(self) -> Any:
        try:
            import openai
        except ImportError as e:
            raise AgentError(INSTALL) from e
        if not os.environ.get("OPENAI_API_KEY"):
            raise AgentError("OpenAI needs a key. Set OPENAI_API_KEY in the environment that starts `vbench serve`.")
        return openai.OpenAI(timeout=90.0, max_retries=1)

    @staticmethod
    def _explain(error: Exception) -> AgentError:
        try:
            import openai
        except ImportError:
            return AgentError(f"OpenAI could not answer: {type(error).__name__}")
        if isinstance(error, openai.AuthenticationError):
            return AgentError("OpenAI did not accept the key. Check OPENAI_API_KEY.")
        if isinstance(error, openai.RateLimitError):
            return AgentError("OpenAI is rate limiting this account; try again in a minute.")
        if isinstance(error, openai.APIConnectionError):
            return AgentError("OpenAI could not be reached; check the network.")
        if isinstance(error, openai.APIStatusError):
            return AgentError(f"OpenAI answered with an error ({error.status_code}): {error.message}")
        return AgentError(f"OpenAI could not answer: {type(error).__name__}")

    def structured(self, system: str, user: str, schema: dict) -> dict:
        client = self._client or self._connect()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "answer", "schema": schema, "strict": False},
                },
            )
        except Exception as e:
            raise self._explain(e) from e
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise AgentError("OpenAI's answer was cut off.")
        if getattr(choice.message, "refusal", None):
            raise AgentError("OpenAI declined to answer this one.")
        try:
            data = json.loads(choice.message.content or "")
        except ValueError as e:
            raise AgentError("OpenAI's answer was not valid JSON.") from e
        if not isinstance(data, dict):
            raise AgentError("OpenAI's answer was not an object.")
        return data

    @staticmethod
    def _wire(system: str, messages: list[dict]) -> list[dict]:
        out: list[dict] = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "tool":
                out.append({"role": "tool", "tool_call_id": m["id"], "content": m["content"]})
            elif m["role"] == "assistant" and m.get("calls"):
                out.append(
                    {
                        "role": "assistant",
                        "content": m.get("content") or None,
                        "tool_calls": [
                            {
                                "id": c["id"],
                                "type": "function",
                                "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])},
                            }
                            for c in m["calls"]
                        ],
                    }
                )
            else:
                out.append({"role": m["role"], "content": m["content"]})
        return out

    def turn(self, system: str, messages: list[dict], tools: list[dict]) -> Iterator[tuple[str, object]]:
        client = self._client or self._connect()
        kwargs: dict[str, Any] = {}
        if tools:
            kwargs["tools"] = [
                {"type": "function", "function": {k: t[k] for k in ("name", "description", "parameters")}}
                for t in tools
            ]
        try:
            stream = client.chat.completions.create(
                model=self.model, messages=self._wire(system, messages), stream=True, **kwargs
            )
            pending: dict[int, dict] = {}
            for chunk in stream:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                delta = choice.delta
                if delta.content:
                    yield ("token", delta.content)
                for tc in delta.tool_calls or []:
                    slot = pending.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                    slot["id"] = tc.id or slot["id"]
                    if tc.function:
                        slot["name"] = tc.function.name or slot["name"]
                        slot["args"] += tc.function.arguments or ""
                if choice.finish_reason == "length":
                    raise AgentError("OpenAI's answer was cut off.")
        except AgentError:
            raise
        except Exception as e:
            raise self._explain(e) from e
        calls = []
        for _, slot in sorted(pending.items()):
            try:
                args = json.loads(slot["args"] or "{}")
            except ValueError:
                args = {}
            calls.append(ToolCall(slot["id"], slot["name"], args if isinstance(args, dict) else {}))
        yield ("calls", calls)
