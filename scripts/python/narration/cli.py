#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .constants import DEFAULT_FORMAT, DEFAULT_MODEL, DEFAULT_PADDING_MS, DEFAULT_VOICE
from .manifest import build_manifest, load_manifest, validate_manifest
from .parser import extract_slides
from .render import validate_rendered_slides, write_render_ready_slides
from .text import sha256_text


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[3]
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
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"TTS voice name. Default: {DEFAULT_VOICE}")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"TTS model identifier. Default: {DEFAULT_MODEL}")
    parser.add_argument(
        "--format",
        choices=("wav", "mp3"),
        default=DEFAULT_FORMAT,
        help=f"Audio format to generate. Default: {DEFAULT_FORMAT}",
    )
    parser.add_argument("--engine", default="auto", help="TTS engine forwarded to ../tts. Default: auto")
    parser.add_argument(
        "--padding-ms",
        type=int,
        default=DEFAULT_PADDING_MS,
        help=f"Reveal auto-slide padding added after narration. Default: {DEFAULT_PADDING_MS}",
    )
    parser.add_argument("--tts-dir", type=Path, default=Path("../tts"), help="Adjacent TTS repository path. Default: ../tts")
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
    source_hash = sha256_text(section_file.read_text(encoding="utf-8"))
    section_dir = section_file.parent
    manifest_path = section_dir / "narration" / "manifest.json"
    rendered_slides_path = section_dir / "narration" / "video-lesson-slides.auto.qmd"
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
        validate_rendered_slides(
            source_file=section_file,
            rendered_file=rendered_slides_path,
            manifest_path=manifest_path,
        )
        print(f"checked {section_file.relative_to(repo_root)}")
        return

    manifest = build_manifest(
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
    write_render_ready_slides(
        source_file=section_file,
        rendered_file=rendered_slides_path,
        manifest=manifest,
    )
    print(f"built {section_file.relative_to(repo_root)}")
