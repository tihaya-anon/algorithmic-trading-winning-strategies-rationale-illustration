from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlideNotes:
    index: int
    heading: str
    slide_id: str
    text: str
    notes_hash: str


@dataclass(frozen=True)
class RenderedSlideTiming:
    index: int
    heading_line: str
    autoslide_ms: int

