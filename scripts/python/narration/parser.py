from __future__ import annotations

from pathlib import Path

from .constants import BLOCK_END, HEADING_RE, NOTES_BLOCK_START
from .text import normalize_notes, sha256_text, slugify
from .types import SlideNotes


def extract_slides(section_file: Path) -> list[SlideNotes]:
    lines = section_file.read_text(encoding="utf-8").splitlines()
    slides: list[SlideNotes] = []
    current_heading: str | None = None
    current_notes: list[str] = []
    inside_notes = False

    for line in lines:
        heading_match = HEADING_RE.match(line)
        if heading_match and heading_match.group(1) == "##":
            finalize_slide(slides, current_heading, current_notes)
            current_heading = heading_match.group(2).strip()
            current_notes = []
            inside_notes = False
            continue

        stripped = line.strip()
        if stripped == NOTES_BLOCK_START:
            if current_heading is None:
                raise ValueError("found notes block before first level-2 slide heading")
            if inside_notes:
                raise ValueError(f"nested notes block under slide {current_heading!r}")
            inside_notes = True
            current_notes = []
            continue

        if inside_notes and stripped == BLOCK_END:
            inside_notes = False
            continue

        if inside_notes:
            current_notes.append(line.rstrip())

    finalize_slide(slides, current_heading, current_notes)
    if not slides:
        raise ValueError("no level-2 slides found")
    return slides


def finalize_slide(slides: list[SlideNotes], heading: str | None, note_lines: list[str]) -> None:
    if heading is None:
        return
    text = normalize_notes(note_lines)
    if not text:
        return
    index = len(slides) + 1
    slides.append(
        SlideNotes(
            index=index,
            heading=heading,
            slide_id=slugify(heading),
            text=text,
            notes_hash=sha256_text(text),
        )
    )

