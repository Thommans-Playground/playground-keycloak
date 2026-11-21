"""The rule of a project's name (AC-12, AC-91): plain text, trimmed, 1 to 100 characters. Pure."""

import unicodedata

from app.projects.domain.errors import InvalidProjectName

MAX_NAME_LENGTH = 100
# Bidirectional marks, embeddings, overrides and isolates: they can make a name read as another one.
BIDIRECTIONAL = frozenset("‎‏؜" + "".join(map(chr, [*range(0x202A, 0x202F), *range(0x2066, 0x206A)])))


def clean_name(name: str) -> str:
    """The trimmed name, or InvalidProjectName. The length is counted in Unicode characters after trimming. The
    message never repeats the name: it would carry the hidden characters to the log and the screen."""
    text = name.strip()
    if not 1 <= len(text) <= MAX_NAME_LENGTH:
        raise InvalidProjectName(f"A project name has 1 to {MAX_NAME_LENGTH} characters.")
    if any(c in BIDIRECTIONAL or unicodedata.category(c) == "Cc" for c in text):
        raise InvalidProjectName("A project name is plain text, with no control or direction characters.")
    return text
