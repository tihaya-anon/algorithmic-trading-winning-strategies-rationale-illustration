from __future__ import annotations

import hashlib
import re


def normalize_notes(note_lines: list[str]) -> str:
    stripped_lines = [line.strip() for line in note_lines]
    text = "\n".join(stripped_lines).strip()
    return re.sub(r"\n{3,}", "\n\n", text)


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^\w\s-]", "", lowered)
    lowered = re.sub(r"[\s_]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered)
    return lowered.strip("-")


def sha256_text(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"

