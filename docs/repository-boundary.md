# Repository Boundary

This repository is the course-content source for
`algorithmic-trading-winning-strategies-rationale`.

Its primary job is to maintain author-owned Quarto content:

- `video-lesson-slides.qmd`
- `web-notes.qmd`
- `pdf-notes.qmd`
- figures, styles, fonts, and chapter/section structure

It should stay lightweight and content-focused.

## What Belongs Here

- chapter and section source files under `chapters/`
- Quarto website and PDF configuration
- shared styles and static assets
- content-side documentation for narration and video contracts

## What Does Not Belong Here

The following are build artifacts or video-pipeline responsibilities and should
live in a separate companion repository or build workspace:

- TTS model/runtime dependencies
- audio generation commands and caches
- generated narration audio such as `.wav` and `.mp3`
- generated narration metadata such as `manifest.json`
- generated autoplay slide sources such as `video-lesson-slides.auto.qmd`
- browser automation, screen capture, ffmpeg composition, and final video files
- subtitles, thumbnails, and other derived media assets

In other words:

- this repository owns the content source
- a companion repository owns narration, autoplay render sources, and video outputs

## Recommended Split

Recommended structure:

```text
algorithmic-trading-winning-strategies-rationale/
  illustration/   # content source
  tts/            # TTS engine and model runtime
  course-video/   # companion pipeline for narration/video generation
```

The `course-video/` repository should read `illustration/` as input, call the
adjacent `tts/` tooling, and write all generated artifacts into its own build or
artifacts directories.

## Practical Rule

If a file can be regenerated from the source `.qmd` files plus external tools,
it should not be treated as a long-lived authoring asset in this repository.
