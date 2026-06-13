#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_VOICE = "course-narrator-v1"
DEFAULT_MODEL = "hexgrad/Kokoro-82M"
DEFAULT_FORMAT = "mp3"
DEFAULT_PADDING_MS = 800
SCHEMA = "slide-narration/v1"
NOTES_BLOCK_START = "::: {.notes}"
BLOCK_END = ":::"
HEADING_RE = re.compile(r"^(##+)\s+(.*?)(?:\s+\{.*\}\s*)?$")


@dataclass(frozen=True)
class SlideNotes:
    index: int
    heading: str
    slide_id: str
    text: str
    notes_hash: str


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    section_files = discover_section_files(repo_root, args.section)

    if not section_files:
        print("build-slide-narration: no video-lesson-slides.qmd files found", file=sys.stderr)
        return 1

    failures = 0
    for section_file in section_files:
        try:
            process_section(repo_root, section_file, args)
        except Exception as exc:
            failures += 1
            print(f"build-slide-narration: {section_file.relative_to(repo_root)}: {exc}", file=sys.stderr)

    return 1 if failures else 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build-slide-narration.py",
        description="Extract slide speaker notes, synthesize narration audio, and write manifest metadata.",
    )
    parser.add_argument(
        "--section",
        type=Path,
        help="Specific video-lesson-slides.qmd file or section directory to process. Defaults to all sections.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate extracted notes, audio files, and manifest entries without calling TTS.",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"TTS voice name. Default: {DEFAULT_VOICE}",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"TTS model identifier. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--format",
        choices=("wav", "mp3"),
        default=DEFAULT_FORMAT,
        help=f"Audio format to generate. Default: {DEFAULT_FORMAT}",
    )
    parser.add_argument(
        "--engine",
        default="auto",
        help="TTS engine forwarded to ../tts. Default: auto",
    )
    parser.add_argument(
        "--padding-ms",
        type=int,
        default=DEFAULT_PADDING_MS,
        help=f"Reveal auto-slide padding added after narration. Default: {DEFAULT_PADDING_MS}",
    )
    parser.add_argument(
        "--tts-dir",
        type=Path,
        default=Path("../tts"),
        help="Adjacent TTS repository path. Default: ../tts",
    )
    return parser.parse_args(argv)


def discover_section_files(repo_root: Path, section: Path | None) -> list[Path]:
    if section is None:
        return sorted(repo_root.glob("chapters/chapter-*/sections/[0-9][0-9]-*/video-lesson-slides.qmd"))

    candidate = (repo_root / section).resolve() if not section.is_absolute() else section.resolve()
    if candidate.is_dir():
        candidate = candidate / "video-lesson-slides.qmd"
    if not candidate.is_file():
        return []
    return [candidate]


def process_section(repo_root: Path, section_file: Path, args: argparse.Namespace) -> None:
    slides = extract_slides(section_file)
    source_text = section_file.read_text(encoding="utf-8")
    source_hash = sha256_text(source_text)
    section_dir = section_file.parent
    manifest_path = section_dir / "narration" / "manifest.json"
    existing_manifest = load_manifest(manifest_path)

    if args.check:
        validate_manifest(
            manifest_path=manifest_path,
            section_file=section_file,
            slides=slides,
            source_hash=source_hash,
            voice=args.voice,
            model=args.model,
            audio_format=args.format,
            padding_ms=args.padding_ms,
        )
        print(f"checked {section_file.relative_to(repo_root)}")
        return

    manifest = build_manifest(
        repo_root=repo_root,
        section_file=section_file,
        slides=slides,
        source_hash=source_hash,
        existing_manifest=existing_manifest,
        voice=args.voice,
        model=args.model,
        audio_format=args.format,
        engine=args.engine,
        padding_ms=args.padding_ms,
        tts_dir=(repo_root / args.tts_dir).resolve() if not args.tts_dir.is_absolute() else args.tts_dir.resolve(),
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"built {section_file.relative_to(repo_root)}")


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


def normalize_notes(note_lines: list[str]) -> str:
    stripped_lines = [line.strip() for line in note_lines]
    text = "\n".join(stripped_lines).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^\w\s-]", "", lowered)
    lowered = re.sub(r"[\s_]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered)
    return lowered.strip("-")


def sha256_text(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest(
    *,
    repo_root: Path,
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


def synthesize_slide(
    *,
    tts_dir: Path,
    text: str,
    output: Path,
    voice: str,
    model: str,
    engine: str,
) -> tuple[int, str]:
    if not tts_dir.is_dir():
        raise FileNotFoundError(f"TTS repository not found: {tts_dir}")
    if shutil.which("uv") is None:
        raise RuntimeError("uv is required to call ../tts")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="slide-narration-") as tmp_dir:
        text_file = Path(tmp_dir) / "slide.txt"
        text_file.write_text(text, encoding="utf-8")
        completed = subprocess.run(
            [
                "uv",
                "run",
                "tts-synthesize",
                "--text-file",
                str(text_file),
                "--output",
                str(output),
                "--voice",
                voice,
                "--model",
                model,
                "--engine",
                engine,
            ],
            cwd=tts_dir,
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "UV_CACHE_DIR": os.environ.get("UV_CACHE_DIR", "/tmp/uv-cache")},
        )

    payload = parse_tts_metadata(completed.stdout)
    duration_ms = int(payload["duration_ms"])
    engine_used = str(payload.get("engine", engine))
    return duration_ms, engine_used


def parse_tts_metadata(stdout: str) -> dict[str, Any]:
    for line in reversed([item.strip() for item in stdout.splitlines() if item.strip()]):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and "duration_ms" in payload:
            return payload
    raise ValueError("TTS command did not return metadata JSON")


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


if __name__ == "__main__":
    raise SystemExit(main())
