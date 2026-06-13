from __future__ import annotations

import re

DEFAULT_VOICE = "course-narrator-v1"
DEFAULT_MODEL = "hexgrad/Kokoro-82M"
DEFAULT_FORMAT = "mp3"
DEFAULT_PADDING_MS = 800
SCHEMA = "slide-narration/v1"
NOTES_BLOCK_START = "::: {.notes}"
BLOCK_END = ":::"
HEADING_RE = re.compile(r"^(##+)\s+(.*?)(?:\s+\{.*\}\s*)?$")

