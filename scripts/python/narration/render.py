from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

from .constants import HEADING_RE, VIDEO_AUTO_SLIDE_FALLBACK_MS
from .types import RenderedSlideTiming


def write_render_ready_slides(
    *,
    source_file: Path,
    rendered_file: Path,
    manifest: dict[str, Any],
) -> None:
    source_lines = source_file.read_text(encoding="utf-8").splitlines()
    source_lines = inject_video_front_matter_settings(source_lines)
    timings_by_index = {
        int(item["index"]): RenderedSlideTiming(
            index=int(item["index"]),
            heading_line=str(item["heading"]),
            autoslide_ms=int(item["autoslide_ms"]),
        )
        for item in manifest.get("slides", [])
    }

    output_lines: list[str] = []
    slide_index = 0

    for line in source_lines:
        heading_match = HEADING_RE.match(line)
        if heading_match and heading_match.group(1) == "##":
            slide_index += 1
            timing = timings_by_index.get(slide_index)
            if timing is not None:
                output_lines.append(with_autoslide_attribute(line, timing.autoslide_ms))
                continue
        output_lines.append(line)

    rendered_file.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


def inject_video_front_matter_settings(source_lines: list[str]) -> list[str]:
    output_lines: list[str] = []
    in_yaml = False
    in_revealjs = False
    inserted_auto_slide = False
    inserted_stoppable = False
    reveal_indent = ""
    reveal_option_indent = ""

    for index, line in enumerate(source_lines):
        stripped = line.strip()
        line_indent = len(line) - len(line.lstrip(" "))

        if index == 0 and stripped == "---":
            in_yaml = True
            output_lines.append(line)
            continue

        if in_yaml and stripped == "---":
            if in_revealjs and not inserted_auto_slide:
                output_lines.append(f"{reveal_indent}  auto-slide: {VIDEO_AUTO_SLIDE_FALLBACK_MS}")
            if in_revealjs and not inserted_stoppable:
                output_lines.append(f"{reveal_indent}  auto-slide-stoppable: false")
            in_yaml = False
            in_revealjs = False
            output_lines.append(line)
            continue

        if in_yaml and re.match(r"^\s*revealjs:\s*$", line):
            in_revealjs = True
            reveal_indent = re.match(r"^(\s*)", line).group(1)
            reveal_option_indent = f"{reveal_indent}  "
            output_lines.append(line)
            continue

        if in_yaml and in_revealjs and stripped and line_indent <= len(reveal_indent) and not re.match(rf"^{reveal_option_indent}(auto-slide|auto-slide-stoppable):", line):
            if not inserted_auto_slide:
                output_lines.append(f"{reveal_option_indent}auto-slide: {VIDEO_AUTO_SLIDE_FALLBACK_MS}")
            if not inserted_stoppable:
                output_lines.append(f"{reveal_option_indent}auto-slide-stoppable: false")
            in_revealjs = False

        if in_yaml and in_revealjs and re.match(rf"^{reveal_option_indent}auto-slide:\s*", line):
            output_lines.append(f"{reveal_option_indent}auto-slide: {VIDEO_AUTO_SLIDE_FALLBACK_MS}")
            inserted_auto_slide = True
            continue

        if in_yaml and in_revealjs and re.match(rf"^{reveal_option_indent}auto-slide-stoppable:\s*", line):
            output_lines.append(f"{reveal_option_indent}auto-slide-stoppable: false")
            inserted_stoppable = True
            continue

        output_lines.append(line)

    if in_yaml and in_revealjs:
        if not inserted_auto_slide:
            output_lines.append(f"{reveal_option_indent}auto-slide: {VIDEO_AUTO_SLIDE_FALLBACK_MS}")
        if not inserted_stoppable:
            output_lines.append(f"{reveal_option_indent}auto-slide-stoppable: false")

    return output_lines


def with_autoslide_attribute(line: str, autoslide_ms: int) -> str:
    autoslide_attr = f'data-autoslide="{autoslide_ms}"'
    if "{" in line and "}" in line:
        if "data-autoslide=" in line:
            return re.sub(r'data-autoslide="\d+"', autoslide_attr, line)
        return re.sub(r"\}\s*$", f" {autoslide_attr}" + "}", line)
    return f'{line} {{{autoslide_attr}}}'


def validate_rendered_slides(
    *,
    source_file: Path,
    rendered_file: Path,
    manifest_path: Path,
) -> None:
    if not rendered_file.is_file():
        raise FileNotFoundError(f"missing rendered slides file: {rendered_file}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_output = tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False)
    expected_path = Path(expected_output.name)
    expected_output.close()
    try:
        write_render_ready_slides(
            source_file=source_file,
            rendered_file=expected_path,
            manifest=manifest,
        )
        actual = rendered_file.read_text(encoding="utf-8")
        expected = expected_path.read_text(encoding="utf-8")
        if actual != expected:
            raise ValueError("render-ready slides file is stale")
    finally:
        expected_path.unlink(missing_ok=True)
