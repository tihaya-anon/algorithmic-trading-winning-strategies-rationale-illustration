from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import SCHEMA
from .tts import synthesize_slide
from .types import SlideNotes


def load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest(
    *,
    section_file: Path,
    slides: list[SlideNotes],
    source_hash: str,
    existing_manifest: dict[str, Any] | None,
    voice: str,
    model: str,
    audio_format: str,
    engine: str,
    padding_ms: int,
    tts_dir: Path,
) -> dict[str, Any]:
    section_dir = section_file.parent
    narration_dir = section_dir / "narration"
    existing_by_index = {
        int(item["index"]): item for item in (existing_manifest or {}).get("slides", []) if "index" in item
    }
    manifest_slides: list[dict[str, Any]] = []

    for slide in slides:
        audio_name = f"slide-{slide.index:03d}.{audio_format}"
        audio_path = narration_dir / audio_name
        previous = existing_by_index.get(slide.index)
        needs_regeneration = not audio_path.is_file() or slide_changed(
            slide=slide,
            previous=previous,
            voice=voice,
            model=model,
            audio_format=audio_format,
            padding_ms=padding_ms,
        )

        if needs_regeneration:
            duration_ms, engine_used = synthesize_slide(
                tts_dir=tts_dir,
                text=slide.text,
                output=audio_path,
                voice=voice,
                model=model,
                engine=engine,
            )
        else:
            duration_ms = int(previous["duration_ms"])
            engine_used = str(previous.get("engine", "cached"))

        manifest_slides.append(
            {
                "index": slide.index,
                "slide_id": slide.slide_id,
                "heading": slide.heading,
                "notes_hash": slide.notes_hash,
                "text": slide.text,
                "audio": str(audio_path.relative_to(section_dir)),
                "duration_ms": duration_ms,
                "autoslide_ms": duration_ms + padding_ms,
                "engine": engine_used,
            }
        )

    return {
        "schema": SCHEMA,
        "source": section_file.name,
        "source_hash": source_hash,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "tts": {
            "provider": "local",
            "model": model,
            "voice": voice,
            "format": audio_format,
            "padding_ms": padding_ms,
        },
        "slides": manifest_slides,
    }


def slide_changed(
    *,
    slide: SlideNotes,
    previous: dict[str, Any] | None,
    voice: str,
    model: str,
    audio_format: str,
    padding_ms: int,
) -> bool:
    if previous is None:
        return True
    return any(
        [
            previous.get("notes_hash") != slide.notes_hash,
            previous.get("slide_id") != slide.slide_id,
            previous.get("heading") != slide.heading,
            previous.get("audio", "").endswith(f".{audio_format}") is False,
            previous.get("autoslide_ms") != int(previous.get("duration_ms", 0)) + padding_ms,
            previous.get("voice") not in (None, voice),
            previous.get("model") not in (None, model),
        ]
    )


def validate_manifest(
    *,
    manifest_path: Path,
    section_file: Path,
    slides: list[SlideNotes],
    source_hash: str,
    voice: str,
    model: str,
    audio_format: str,
    padding_ms: int,
) -> None:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing narration manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA:
        raise ValueError(f"unexpected manifest schema: {manifest.get('schema')!r}")
    if manifest.get("source") != section_file.name:
        raise ValueError("manifest source does not match section file")
    if manifest.get("source_hash") != source_hash:
        raise ValueError("manifest source_hash is stale")

    tts = manifest.get("tts", {})
    if tts.get("voice") != voice:
        raise ValueError("manifest voice does not match requested voice")
    if tts.get("model") != model:
        raise ValueError("manifest model does not match requested model")
    if tts.get("format") != audio_format:
        raise ValueError("manifest format does not match requested format")
    if int(tts.get("padding_ms", -1)) != padding_ms:
        raise ValueError("manifest padding_ms does not match requested padding")

    manifest_slides = manifest.get("slides", [])
    if len(manifest_slides) != len(slides):
        raise ValueError("manifest slide count does not match extracted notes")

    for slide, entry in zip(slides, manifest_slides, strict=True):
        if int(entry.get("index", -1)) != slide.index:
            raise ValueError(f"slide index mismatch for {slide.heading!r}")
        if entry.get("slide_id") != slide.slide_id:
            raise ValueError(f"slide_id mismatch for {slide.heading!r}")
        if entry.get("heading") != slide.heading:
            raise ValueError(f"heading mismatch for slide {slide.index}")
        if entry.get("notes_hash") != slide.notes_hash:
            raise ValueError(f"notes_hash mismatch for slide {slide.index}")
        if entry.get("text") != slide.text:
            raise ValueError(f"text mismatch for slide {slide.index}")

        audio_rel = entry.get("audio")
        if not isinstance(audio_rel, str) or not audio_rel.endswith(f".{audio_format}"):
            raise ValueError(f"audio path mismatch for slide {slide.index}")
        audio_path = section_file.parent / audio_rel
        if not audio_path.is_file():
            raise FileNotFoundError(f"missing audio file for slide {slide.index}: {audio_path}")

        duration_ms = int(entry.get("duration_ms", -1))
        autoslide_ms = int(entry.get("autoslide_ms", -1))
        if duration_ms < 0:
            raise ValueError(f"invalid duration_ms for slide {slide.index}")
        if autoslide_ms != duration_ms + padding_ms:
            raise ValueError(f"autoslide_ms mismatch for slide {slide.index}")

