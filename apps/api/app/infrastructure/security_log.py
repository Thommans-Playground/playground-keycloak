"""The security log as one JSON object per line on stdout (ADR 0013).

On AWS the ECS awslogs driver ships stdout to CloudWatch. Only the keys below can be written, and every value is
checked: a value that does not look like a short code or id is dropped, so a token can not get in.
It imports no context: each context's SecurityLog port is satisfied structurally.
"""

import hashlib
import json
import re
import sys
from datetime import UTC, datetime

_CODE = re.compile(r"[a-z_]{1,40}")
_ID = re.compile(r"[A-Za-z0-9-]{1,64}")


class JsonStdoutSecurityLog:
    def __init__(self, stream=None):
        self._stream = stream

    def event(self, name, result, person_id=None, session_id=None, reason=None):
        line = {
            "ts": datetime.now(UTC).isoformat(),
            "event": name if _CODE.fullmatch(name or "") else "invalid_event",
            "result": result if _CODE.fullmatch(result or "") else "invalid_result",
        }
        if person_id is not None and _ID.fullmatch(person_id):
            line["person_id"] = person_id
        if session_id:
            line["session"] = hashlib.sha256(session_id.encode()).hexdigest()[:16]
        if reason is not None and _CODE.fullmatch(reason):
            line["reason"] = reason
        stream = self._stream or sys.stdout
        stream.write(json.dumps(line) + "\n")
        stream.flush()
