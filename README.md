# Algorithmic Trading: Winning Strategies and Their Rationale

This directory contains a Quarto stack for course material based on Ernest P.
Chan's algorithmic trading text.

## Outputs

- `chapters/`: chapter-section pages for the web reading experience
- `slides/video-lesson.qmd`: reveal.js slides for recording or autoplay
- `handouts/web-notes.qmd`: HTML handout for web publishing
- `handouts/pdf-notes.qmd`: PDF handout for printing or offline reading

## Chapter-Section Structure

Use `chapters/` as the canonical web content source:

```text
chapters/
  index.qmd
  _metadata.yml
  chapter-01/
    index.qmd
    sections/
      01-research-loop.qmd
      02-net-returns-costs.qmd
```

Each chapter gets an `index.qmd` overview, and each section gets its own page
under `sections/`. Prefix section filenames with two digits so the repository
order matches the reading order.

After adding a new chapter or section, add it to `website.sidebar.contents` in
`_quarto.yml`; the web frontend renders that sidebar as the chapter-section
navigation.

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
HTML, reveal.js slides, and PDF output:

```bash
sudo apt-get update
sudo apt-get install -y fonts-noto-core fonts-noto-cjk fonts-noto-mono
```

The HTML and reveal.js outputs use a sans-serif font stack. The PDF handout uses
Noto Serif CJK SC as the main serif font so English and Chinese text share a
single stable LuaLaTeX font path.
Code blocks use Maple Mono NF CN from `assets/fonts/`, so the website and PDF do
not depend on Maple Mono being installed on the runner.
The bundled Maple Mono font files are licensed under the SIL Open Font License
1.1; keep `assets/fonts/OFL-MapleMono.txt` with the fonts when copying them into
another repository. Upstream project: https://github.com/subframe7536/maple-font
For GitHub Actions on Ubuntu runners, install the same font packages before
`quarto render`.

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

The workflow in `.github/workflows/publish.yml` renders the entire Quarto project
in CI, including `handouts/pdf-notes.qmd`, then deploys the generated `_site/`
directory as a static GitHub Pages artifact.

Configure the repository under Settings -> Pages to use GitHub Actions as the
source. The published site serves `handouts/pdf-notes.pdf` as a static file, so
no PDF engine is needed at request time.

## Sync to Course Repositories

Use this repository as the Quarto infrastructure template, then sync it into a
real course repository when the Actions, fonts, or styles change:

```bash
scripts/sync-template.sh ../my-course --dry-run
scripts/sync-template.sh ../my-course
```

The default `infra` mode copies `.github/`, `.vscode/`, `styles/`, and
`assets/fonts/`. It copies `_quarto.yml` only when the target does not already
have one, so course-specific titles and navigation are preserved. To replace the
target Quarto config too, run:

```bash
scripts/sync-template.sh ../my-course --overwrite-quarto-config
```

It overwrites synced files with the same names but does not delete unrelated
course material.

For a brand-new repository, copy the whole template:

```bash
scripts/sync-template.sh ../new-course full
```

Use `full` mode only when the target is empty or disposable; it deletes files in
the target that are not part of this template, except `.git/`, Quarto caches,
and rendered site output.

## Why This Structure

The video deck and the reading material should not be the same artifact.

- slides favor timing, motion, sparse text, and narration
- handouts favor detail, derivations, and review

Quarto lets you keep those outputs in one project without forcing you back into a full Beamer workflow.

## Render Commands

```bash
quarto render chapters/index.qmd
quarto render chapters/chapter-01/index.qmd
quarto render chapters/chapter-01/sections/01-research-loop.qmd
quarto render chapters/chapter-01/sections/02-net-returns-costs.qmd
quarto render slides/video-lesson.qmd
quarto render handouts/web-notes.qmd
quarto render handouts/pdf-notes.qmd
quarto render
```

## Suggested Lecture Pattern

1. Put the core story into `slides/video-lesson.qmd`.
2. Keep narration in `::: {.notes}` blocks.
3. Generate TTS from notes and align it with slide timing.
4. Put extra derivations, assumptions, and figures into the handouts.
5. Publish `_site/` to GitHub Pages and export PDF when needed.

## TTS / Video Notes

The deck already demonstrates the key pieces:

- reveal.js `auto-slide` for automatic pacing
- speaker notes as a clean source for narration text
- formula, code, and figure layout for quant topics

In practice you will likely want to set `auto-slide` per slide once your narration timings are stable.
