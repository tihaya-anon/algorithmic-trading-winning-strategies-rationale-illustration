from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


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

