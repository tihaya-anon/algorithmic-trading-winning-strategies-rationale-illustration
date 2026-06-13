# Slide Narration Contract

This document defines the contract between slide speaker notes, TTS audio
generation, and reveal.js auto-slide timing.

## Goal

`video-lesson-slides.qmd` speaker notes are the source of truth for narration.
Each slide should produce one TTS input, one audio file, and one timing record.
The timing record should drive reveal.js auto-slide duration at slide granularity.

Reveal supports per-slide timing overrides with the `data-autoslide` attribute.
Quarto reveal slides can pass attributes through slide headings, so the timing
pipeline can target the rendered slide with `data-autoslide` rather than relying
only on one global `auto-slide` value.

References:

- Reveal auto-slide timing: <https://revealjs.com/auto-slide/>
- Quarto reveal slide headings and attributes: <https://quarto.org/docs/presentations/revealjs/>

## Technology Stack

The narration pipeline should be provider-neutral. The Quarto repository owns
slide-note extraction, manifest validation, timing metadata, and render-time
integration. TTS inference should live behind a small CLI or service boundary so
the provider can change without rewriting the manifest logic.

Recommended first implementation:

- `illustration/scripts/shell/build-slide-narration.sh`: repository-facing command
  that authors and checks call.
- `illustration/scripts/python/build_slide_narration.py`: deterministic extraction,
  hashing, manifest comparison, audio duration probing, and manifest writing.
- `../tts`: adjacent Python project for local TTS models, dependencies, caches,
  and optional service code.
- `ffmpeg` and `ffprobe`: required system tools for audio conversion and exact
  duration probing.

The adjacent `../tts` project keeps large model weights and ML dependencies out
of this Quarto repository:

```text
algorithmic-trading-winning-strategies-rationale/
  illustration/
    scripts/shell/build-slide-narration.sh
    chapters/.../narration/manifest.json
    chapters/.../narration/slide-001.mp3
  tts/
    pyproject.toml
    uv.lock
    .venv/
    src/tts_service/
      synthesize.py
    models/
```

`../tts` should expose a stable command-line interface first. A long-running HTTP
service can be added later if startup time becomes the bottleneck.

Example local CLI contract:

```bash
uv run tts-synthesize \
  --text-file /tmp/slide-001.txt \
  --output /path/to/narration/slide-001.wav \
  --voice course-narrator-v1 \
  --model hexgrad/Kokoro-82M
```

Example duration probe:

```bash
ffprobe -v error \
  -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  narration/slide-001.mp3
```

For Ubuntu or WSL, install the audio tools with:

```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version
ffprobe -version
```

`ffprobe` is distributed by the `ffmpeg` package on Ubuntu.

## TTS Provider Strategy

Use a local provider for the first end-to-end implementation.

Recommended MVP:

- `provider`: `local`
- `model`: `hexgrad/Kokoro-82M`
- `voice`: a repository-defined voice name such as `course-narrator-v1`
- `format`: `mp3` for committed/generated slide assets, with temporary WAV
  allowed during synthesis

Kokoro-82M is a lightweight local model and is a good fit for validating the
pipeline on CPU. It is not the final answer for voice cloning, but it is small
enough to prove extraction, caching, audio generation, duration probing, and
manifest writing before adopting a heavier model.

Future provider options:

- `openai`: hosted TTS, low operational burden, paid API usage.
- `local-cosyvoice`: stronger multilingual and voice-cloning path, but heavier
  runtime requirements.
- `local-f5-tts` or `local-xtts`: useful for experiments, subject to model
  license and hardware constraints.

Voice cloning must use only owned or explicitly licensed reference audio. Model
license, voice rights, and course distribution rights should be checked before a
cloned voice is used in published material.

## Contract File

Each section with generated narration should own a local manifest:

```text
chapters/chapter-NN/sections/NN-section-slug/narration/manifest.json
```

The manifest is generated output. Authors should edit `video-lesson-slides.qmd`
notes, not the manifest by hand.

Recommended schema:

```json
{
  "schema": "slide-narration/v1",
  "source": "video-lesson-slides.qmd",
  "source_hash": "sha256:...",
  "generated_at": "2026-06-12T00:00:00Z",
  "tts": {
    "provider": "local",
    "model": "hexgrad/Kokoro-82M",
    "voice": "course-narrator-v1",
    "format": "mp3",
    "padding_ms": 800
  },
  "slides": [
    {
      "index": 1,
      "slide_id": "a-backtest-is-useful-only-when-it-rehearses-the-live-strategy",
      "heading": "A backtest is useful only when it rehearses the live strategy.",
      "notes_hash": "sha256:...",
      "text": "Narration text extracted from the slide notes.",
      "audio": "narration/slide-001.mp3",
      "duration_ms": 11840,
      "autoslide_ms": 12640
    }
  ]
}
```

## Slide Identity

The binding should not rely on index alone.

Use all of these fields:

- `index`: stable ordering for humans and generated filenames.
- `slide_id`: the rendered reveal section id, derived from the slide heading.
- `notes_hash`: detects stale TTS when notes change.

If the heading changes but the notes do not, `notes_hash` can still prove the
audio is current, while `slide_id` tells the render-time timing injector where
to attach `data-autoslide`.

## Timing Rule

`duration_ms` is the exact TTS audio duration returned by the provider or read
from the generated audio file.

`autoslide_ms` is the value used by reveal:

```text
autoslide_ms = duration_ms + padding_ms
```

The padding should be explicit in `tts.padding_ms`, not hidden inside scripts.
The default should be small, around 500-1000 ms, to give the final spoken phrase
room before the deck advances.

## Pipeline

The pipeline should be separated into deterministic extraction and external TTS
generation.

1. Extract slide notes from `video-lesson-slides.qmd`.
2. Build normalized TTS text per slide.
3. Compare `notes_hash` values with the existing manifest.
4. Regenerate audio only for slides whose notes, provider, voice, model, or
   format changed.
5. Write `duration_ms` and `autoslide_ms` into `narration/manifest.json`.
6. During slide rendering, attach each `autoslide_ms` to its matching slide as
   `data-autoslide`.

TTS generation may call the adjacent `../tts` project or a hosted provider, but
all deterministic work should remain in this repository. `--check` must validate
existing outputs only and must not import local TTS packages, load model weights,
start a TTS service, or call a hosted provider.

## Render Integration

There are two viable integration points.

Preferred approach:

- Add a Quarto/Pandoc filter or pre-render script that reads
  `narration/manifest.json`.
- It injects `{data-autoslide="12640"}` into each slide heading in the generated
  AST or a temporary render source such as
  `narration/video-lesson-slides.auto.qmd`.
- Source `.qmd` files remain clean and author-owned.

Fallback approach:

- Add a reveal runtime script such as `styles/reveal-narration.js`.
- It fetches `narration/manifest.json` next to the rendered slide deck.
- It finds each rendered section by `slide_id` and sets `data-autoslide`.

The preferred approach is easier to validate before render. The fallback is less
intrusive but depends on browser-time loading and path resolution.

## Checks

Add a non-render check command:

```text
bash scripts/shell/build-slide-narration.sh --check
```

The check should fail when:

- a slide has notes but no manifest entry;
- a manifest entry points to a missing audio file;
- the generated render-ready slide source is missing or stale;
- `notes_hash` does not match the current notes;
- `autoslide_ms` is not equal to `duration_ms + padding_ms`;
- slide ids in the manifest no longer match current slide headings.

The check should not call the TTS provider.

## Authoring Rule

Authors write narration only in:

```markdown
::: {.notes}
Narration text.
:::
```

Authors should not hand-edit `data-autoslide` attributes in
`video-lesson-slides.qmd` when generated narration exists. Per-slide timing is
owned by the narration manifest.
