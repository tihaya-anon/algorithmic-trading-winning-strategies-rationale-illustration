# Algorithmic Trading: Winning Strategies and Their Rationale

This directory contains a Quarto stack for course material based on Ernest P.
Chan's algorithmic trading text.

Repository scope note:
see [docs/repository-boundary.md](docs/repository-boundary.md) for the intended
split between this content repository and an external narration/video pipeline.

## Outputs

- `video-lesson-slides.qmd`: reveal.js slides with narration notes
- `web-notes.qmd`: HTML notes for browser reading
- `pdf-notes.qmd`: PDF notes for printing or offline reading

Each section owns all three outputs. Video slides should be visually strong and
may simplify details; web and PDF notes should stay nearly identical in
substance. Prefer SVG figures for web notes, and PNG or TIFF exports for PDF
notes when final figures are available.

Section authors should maintain only descriptive front matter such as `title`,
`subtitle`, `author`, and `date`. Do not hand-write output `format` blocks in
section files; generate them with `scripts/shell/sync-output-formats.sh`.

## Chapter-Section Structure

Use `chapters/` as the canonical content source:

```text
chapters/
  index.qmd
  _metadata.yml
  chapter-01/
    index.qmd
    sections/
      01-the-importance-of-backtesting/
        video-lesson-slides.qmd
        web-notes.qmd
        pdf-notes.qmd
      02-common-pitfalls-of-backtesting/
        video-lesson-slides.qmd
        web-notes.qmd
        pdf-notes.qmd
```

Each chapter gets an `index.qmd` overview, and each section gets its own folder
under `sections/`. Prefix section folders with two digits so repository order
matches reading order.

After adding, renaming, or removing a chapter or section folder, run:

```bash
scripts/shell/sync-output-formats.sh
scripts/shell/sync-section-structure.sh
```

The first command regenerates per-file Quarto output settings for slides, web
notes, and PDF notes. The second command regenerates `_quarto.yml`,
`chapters/index.qmd`, and CI routing from the directory tree. Do not
hand-maintain output formats, section links in `_quarto.yml`, or the publish
workflow.

## Local Setup

Install Quarto first. On Ubuntu/Debian, download the latest `.deb` installer
from the Quarto download page, then install it:

https://quarto.org/docs/download/

```bash
sudo apt install ./quarto-*-linux-amd64.deb
quarto --version
```

Install TinyTeX for PDF rendering:

```bash
quarto install tinytex
```

Do not run this command with `sudo`. Quarto installs TinyTeX as a Quarto-managed
tool for the current user; running it as root can put the tool in root's Quarto
directory and can also drop proxy or GitHub credentials from your environment.

If TinyTeX install fails with `403 - Forbidden`, your anonymous GitHub API quota
is likely exhausted. Authenticate GitHub CLI and expose its token only for the
current shell:

```bash
gh auth login -h github.com
export GH_TOKEN="$(gh auth token)"
quarto install tinytex
```

Install Noto fonts so English and Simplified Chinese render consistently in
HTML and reveal.js slides:

```bash
sudo apt-get update
sudo apt-get install -y fonts-noto-core fonts-noto-cjk fonts-noto-mono
```

The HTML and reveal.js outputs use a sans-serif font stack. The PDF notes use
XeLaTeX with repository-bundled Noto CJK fonts under `assets/fonts/` so PDF
rendering does not depend on host font installation.
Add these files to `assets/fonts/`:

- `NotoSerifCJKsc-Regular.otf`
- `NotoSerifCJKsc-Bold.otf`
- `NotoSansCJKsc-Regular.otf`
- `NotoSansCJKsc-Bold.otf`

Code blocks use Maple Mono NF CN from `assets/fonts/`, so the website and PDF do
not depend on Maple Mono being installed on the runner.
The bundled Maple Mono font files are licensed under the SIL Open Font License
1.1; keep `assets/fonts/OFL-MapleMono.txt` with the fonts when copying them into
another repository. Upstream project: https://github.com/subframe7536/maple-font
For GitHub Actions on Ubuntu runners, system Noto packages are still useful for
HTML and reveal.js output, but PDF rendering should use the bundled font files.

If TinyTeX setup happens in GitHub Actions, pass the workflow token to avoid
anonymous GitHub API rate limits:

```yaml
- uses: quarto-dev/quarto-actions/setup@v2
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tinytex: true
```

## GitHub Pages

The workflow in `.github/workflows/publish.yml` renders the entire Quarto
project in CI, including section-level PDF notes, then deploys the generated
`_site/` directory as a static GitHub Pages artifact.

CI runs `scripts/shell/sync-output-formats.sh --check` and
`scripts/shell/sync-section-structure.sh --check` before rendering, then
`scripts/shell/sync-section-structure.sh --verify-rendered` after rendering, so the
artifact checks stay aligned with section folders automatically.

Configure the repository under Settings -> Pages to use GitHub Actions as the
source. The published site serves rendered section PDFs as static files, so no
PDF engine is needed at request time.

## Sync to Course Repositories

Use this repository as the Quarto infrastructure template, then sync it into a
real course repository when the Actions, fonts, or styles change:

```bash
scripts/shell/sync-template.sh ../my-course --dry-run
scripts/shell/sync-template.sh ../my-course
```

The default `infra` mode copies `.github/`, `.vscode/`, `styles/`, and
`assets/fonts/`. It copies `_quarto.yml` only when the target does not already
have one, so course-specific titles and navigation are preserved. To replace the
target Quarto config too, run:

```bash
scripts/shell/sync-template.sh ../my-course --overwrite-quarto-config
```

It overwrites synced files with the same names but does not delete unrelated
course material.

For a brand-new repository, copy the whole template:

```bash
scripts/shell/sync-template.sh ../new-course full
```

Use `full` mode only when the target is empty or disposable; it deletes files in
the target that are not part of this template, except `.git/`, Quarto caches,
and rendered site output.

## Why This Structure

The video deck and the reading material should not be the same artifact.

- slides favor timing, motion, sparse text, and narration
- handouts favor detail, derivations, and review

Quarto lets you keep those outputs in one project without forcing you back into a full Beamer workflow.

## Human Render Commands

Agents should not execute Quarto render or preview commands. After content or
structure changes, ask a human to run the relevant command:

```bash
quarto render chapters/index.qmd
quarto render chapters/chapter-01/index.qmd
quarto render chapters/chapter-01/sections/01-the-importance-of-backtesting/video-lesson-slides.qmd
quarto render chapters/chapter-01/sections/01-the-importance-of-backtesting/web-notes.qmd
quarto render chapters/chapter-01/sections/01-the-importance-of-backtesting/pdf-notes.qmd
quarto render chapters/chapter-01/sections/02-common-pitfalls-of-backtesting/video-lesson-slides.qmd
quarto render chapters/chapter-01/sections/02-common-pitfalls-of-backtesting/web-notes.qmd
quarto render chapters/chapter-01/sections/02-common-pitfalls-of-backtesting/pdf-notes.qmd
quarto render
```

## Suggested Lecture Pattern

1. Put the core story into each section's `video-lesson-slides.qmd`.
2. Keep narration in `::: {.notes}` blocks.
3. Generate TTS from notes and align it with slide timing in `../course-video`.
4. Put extra derivations, assumptions, and figures into `web-notes.qmd` and
   `pdf-notes.qmd`.
5. Publish `_site/` to GitHub Pages and export PDF when needed.

## TTS / Video Notes

This repository keeps only the source `video-lesson-slides.qmd` files and their
speaker notes. Narration audio, manifest files, render-ready autoplay slide
sources, and video composition should live in `../course-video`.

In practice you will likely want to set `auto-slide` per slide once your
narration timings are stable, but the generated autoplay slide sources and
their timing manifests belong in `../course-video`, not here.
