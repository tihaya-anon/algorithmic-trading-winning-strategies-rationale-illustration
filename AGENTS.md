# Repository Guidelines

## Project Structure & Module Organization

This is a Quarto course-material repository for `algorithmic-trading-winning-strategies-rationale`. `_quarto.yml` defines the website, navigation, formats, and shared execution settings. `index.qmd` is the site home. `chapters/` is the canonical web reading source, using paths such as `chapters/chapter-01/sections/`. Prefix section filenames with two digits, for example `01-research-loop.qmd`.

Content is organized by section. Each section has three deliverables: narration-backed `video-lesson-slides`, browser `web-notes`, and printable `pdf-notes`. Slides should be engaging, visually strong, and may simplify details. `web-notes` and `pdf-notes` should be nearly identical; prefer SVG for web images and TIFF or PNG for PDF images.

Slides live in `slides/video-lesson.qmd`; handouts live in `handouts/`. Shared CSS is in `styles/`, figures and fonts are in `assets/`, and sync logic is in `scripts/sync-template.sh`. Treat `_site/`, `.quarto/`, rendered HTML, PDF, TeX, and logs as generated output.

## Build, Test, and Development Commands

- `quarto preview` starts a website preview.
- `quarto render` renders the full project into `_site/`.
- `quarto render chapters/chapter-01/sections/01-research-loop.qmd` validates one page.
- `quarto render slides/video-lesson.qmd` renders the reveal.js deck.
- `quarto render handouts/pdf-notes.qmd` builds the PDF handout; TinyTeX is required.
- `scripts/sync-template.sh ../my-course --dry-run` previews template sync changes.

## Coding Style & Naming Conventions

Use Quarto Markdown with YAML front matter at the top of each `.qmd` file. Prefer clear ATX headings (`#`, `##`), short paragraphs, and two-space indentation in YAML. Name chapter directories `chapter-NN` and section files `NN-descriptive-slug.qmd`. Use lowercase, hyphenated filenames unless an upstream asset requires otherwise. For shell scripts, keep the existing Bash style: `set -euo pipefail`, small helpers, and quoted paths.

## Testing Guidelines

There is no separate automated test suite. Render the smallest affected `.qmd` file first, then run `quarto render` before opening a pull request. When adding chapters or sections, update `website.sidebar.contents` in `_quarto.yml`. For PDF edits, verify `handouts/pdf-notes.qmd`.

## Agent-Specific Instructions

When book-specific facts are needed, use the `book-knowledge` MCP tools to search or read the indexed source instead of relying on memory. Keep teaching content faithful to the book: concise and visual for slides, fuller and reference-oriented for notes.

## Commit & Pull Request Guidelines

History uses concise Conventional Commits, for example `feat(content): add chapter-section web structure`. Use `<type>(scope): summary` where practical, with types such as `feat`, `fix`, `docs`, or `chore`.

Pull requests should describe the change, list the render command used, and include screenshots for visual changes. Do not commit `_site/`, `.quarto/`, HTML, PDF, TeX, or logs.
