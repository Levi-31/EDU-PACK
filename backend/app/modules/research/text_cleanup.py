import re

# The model occasionally returns typographic characters as raw control bytes
_LOW_BYTE_PUNCTUATION = str.maketrans({
    "\x14": "—",
    "\x18": "‘",
    "\x19": "’",
    "\x1c": "“",
    "\x1d": "”",
    "\x13": "–",
    "\x00": "—",
    "\x01": "—",
    "\x1f": "—",
})


def repair_control_chars(text: str) -> str:
    """Restores punctuation the model emitted as control bytes and removes any other control characters."""
    text = re.sub(r"(?<=\w)\x1f(?=(?:s|t|d|m|re|ve|ll)\b)", "’", text)
    text = re.sub(r"\x13\d(?=\s)", "—", text)
    text = re.sub(r"\x13\d", "-", text)
    text = text.translate(_LOW_BYTE_PUNCTUATION)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)


_REFERENCE_NOTE = re.compile(r"^[ \t]*[*_]*\s*references?\b[^\n]*\n?", re.IGNORECASE | re.MULTILINE)
_REFERENCE_SECTION = re.compile(
    r"^#{1,6}[ \t]+[*_]*(?:references?|bibliography|works cited)[*_:]*[ \t]*\n.*?(?=^#{1,6}[ \t]|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)


def strip_reference_notes(text: str) -> str:
    """Removes reference sections and "References: ..." footnote lines that writers add despite instructions."""
    parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
    for idx in range(0, len(parts), 2):
        parts[idx] = _REFERENCE_NOTE.sub("", _REFERENCE_SECTION.sub("", parts[idx]))
    return "".join(parts)
