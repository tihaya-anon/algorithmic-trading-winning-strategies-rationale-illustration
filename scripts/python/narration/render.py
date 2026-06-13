from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

from .constants import HEADING_RE
from .types import RenderedSlideTiming


def write_render_ready_slides(
    *,
    source_file: Path,
    rendered_file: Path,
    manifest: dict[str, Any],
) -> None:
    source_lines = source_file.read_text(encoding="utf-8").splitlines()
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

