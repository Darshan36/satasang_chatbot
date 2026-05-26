"""Shared content cleaning for prasang stories.

Strips the boilerplate Sabha metadata (Date / Day / Place / Time / Topic /
Prasad headers) so it is never embedded, tagged, or shown to users — this both
improves search quality and honours the "keep metadata hidden" preference.

Extends the patterns originally in refine_prasangs_v2.py.
"""
import hashlib
import re

# A line is dropped if it matches any of these (case-insensitive, anywhere).
_METADATA_PATTERNS = [
    r"Akshar Sarjan Sabha",
    r"Date\s*[-–:ઃ]",
    r"Day\s*[-–:ઃ]",
    r"Place\s*[-–:ઃ]",
    r"Time\s*[-–:ઃ]",
    r"Topic\s*[-–:ઃ�]",   # includes the corrupted separator seen in the data
    r"ટોપિક\s*[-–:ઃ]",
    r"Prasad\s*[-–:ઃ]",
]
_METADATA_RE = re.compile("|".join(_METADATA_PATTERNS), re.IGNORECASE)


def clean_content(content: str) -> str:
    """Remove metadata header lines and collapse excess blank lines."""
    if not content:
        return ""
    kept = []
    for line in content.split("\n"):
        stripped = line.strip().strip("*").strip()
        if not stripped:
            kept.append(line)
            continue
        if _METADATA_RE.search(line):
            continue
        kept.append(line)
    result = "\n".join(kept).strip()
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


def content_hash(text: str) -> str:
    """Stable SHA-256 hash of cleaned content, used to detect changes / resume."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
