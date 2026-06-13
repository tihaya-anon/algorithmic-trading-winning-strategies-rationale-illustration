# Repository Guidelines

## Project Structure & Module Organization

This is a Quarto course-material repository for `algorithmic-trading-winning-strategies-rationale`. `_quarto.yml` defines the website, navigation, formats, and shared execution settings. `index.qmd` is the site home. `chapters/` is the canonical source tree, using section folders such as `chapters/chapter-01/sections/01-the-importance-of-backtesting/`.

Content is organized by section. Each section has three deliverables: narration-backed `video-lesson-slides.qmd`, browser `web-notes.qmd`, and printable `pdf-notes.qmd`. Slides should be engaging, visually strong, and may simplify details. `web-notes` and `pdf-notes` should be nearly identical; prefer SVG for web images and TIFF or PNG for PDF images.

Shared CSS is in `styles/`, figures and fonts are in `assets/`, routing sync logic is in `scripts/shell/sync-section-structure.sh`, output-format sync logic is in `scripts/shell/sync-output-formats.sh`, and Python helpers are in `scripts/python/`. Treat `_site/`, `.quarto/`, rendered HTML, PDF, TeX, logs, and generated narration assets as output.

## Build, Test, and Development Commands

- Agents must not run `quarto render` or `quarto preview`; ask a human to execute render/preview commands.
- `scripts/shell/sync-output-formats.sh` regenerates per-file Quarto `format`, `execute`, and PDF header settings for section outputs.
- `scripts/shell/sync-output-formats.sh --check` verifies section output settings are current without rendering.
- `scripts/shell/sync-section-structure.sh` regenerates `_quarto.yml`, `chapters/index.qmd`, and CI routing from section folders.
- `scripts/shell/sync-section-structure.sh --check` verifies generated routing is current without rendering.
- `scripts/shell/sync-section-structure.sh --verify-rendered` checks `_site` artifacts after a human has rendered.
- `scripts/shell/sync-template.sh ../my-course --dry-run` previews template sync changes.

## Coding Style & Naming Conventions

Use Quarto Markdown with YAML front matter at the top of each `.qmd` file. For section outputs, authors should only maintain descriptive metadata such as `title`, `subtitle`, `author`, and `date`; do not hand-edit generated `format`, `execute`, or `include-in-header` blocks. Prefer clear ATX headings (`#`, `##`), short paragraphs, and two-space indentation in YAML. Name chapter directories `chapter-NN` and section directories `NN-descriptive-slug`. Use lowercase, hyphenated filenames unless an upstream asset requires otherwise. For shell scripts, keep the existing Bash style: `set -euo pipefail`, small helpers, and quoted paths.

## Testing Guidelines

There is no separate automated test suite. Agents should run non-render checks only: `bash -n scripts/shell/sync-output-formats.sh`, `scripts/shell/sync-output-formats.sh --check`, `bash -n scripts/shell/sync-section-structure.sh`, `scripts/shell/sync-section-structure.sh --check`, and `scripts/shell/build-slide-narration.sh --check` when narration assets are in scope. When adding chapters or sections, run the sync scripts instead of editing formats, `_quarto.yml`, or CI by hand. Ask a human to render the smallest affected `.qmd` file and then `quarto render`.

## Agent-Specific Instructions

When book-specific facts are needed, use the `book-knowledge` MCP tools to search or read the indexed source instead of relying on memory. Keep teaching content faithful to the book: concise and visual for slides, fuller and reference-oriented for notes. Do not execute Quarto render commands yourself.

## Commit & Pull Request Guidelines

History uses concise Conventional Commits, for example `feat(content): add chapter-section web structure`. Use `<type>(scope): summary` where practical, with types such as `feat`, `fix`, `docs`, or `chore`.

Pull requests should describe the change, list the render command used, and include screenshots for visual changes. Do not commit `_site/`, `.quarto/`, HTML, PDF, TeX, or logs.
