# Tools for __PROJECT_NAME__

Everything here works from **macOS** (zsh/bash, Homebrew) and **Windows** (PowerShell, Scoop or winget). Linux works like macOS with the distro's package manager. Rules and workflows are in [[CLAUDE.md]].

## Required

| Need | mac | win | Why |
|---|---|---|---|
| **Python 3.9+** | `brew install python` (or `xcode-select --install`) | `winget install --id Python.Python.3.13` (or `scoop install python`) | Runs the Claude Code hooks (`raw/` guard, session brief, end-of-turn check) and the lint, refactor and source-size scripts. Check: `python3 --version` / `py --version`. |
| **Git Bash** (Windows only) | - | `winget install --id Git.Git` | Claude Code runs hook commands through Git Bash; without it it falls back to PowerShell, and every hook reports an error on that machine. Using git for the vault stays optional. |

Without Python the wiki still works as plain Markdown, but nothing checks it: the session brief says so when that happens. After installing, restart Claude Code so it sees the new PATH.

## Optional tools

All of these are optional: the AI can fall back to its built-in file tools. They make search and PDF handling faster and cheaper as the wiki grows.

> Check the platform before running anything. Commands marked **mac** run in zsh/bash; **win** commands run in PowerShell. Use forward slashes in paths inside notes on both systems.

macOS needs [Homebrew](https://brew.sh); Windows needs [Scoop](https://scoop.sh) (or winget). Package names below are Scoop names; check with `scoop search <name>` / `winget search <name>` if one has moved.

| Need | Tool | mac | win | Notes |
|---|---|---|---|---|
| Search text | **ripgrep** (`rg`) | `brew install ripgrep` | `scoop install ripgrep` | Fast regex search across the vault. The one tool worth installing first. |
| Find files | **fd** | `brew install fd` | `scoop install fd` | Quick filename search; `fd -e md` lists notes. |
| Frontmatter / data | **jq**, **yq** | `brew install jq yq` | `scoop install jq yq` | Query JSON, and YAML frontmatter (`yq --front-matter=extract`). |
| Semantic search | **qmd** | `npm install -g @tobilu/qmd` | same (needs Node 22+) | Local Markdown search: BM25 + vectors + reranking, plus an MCP server. Downloads ~2 GB of local models on first use. Windows support isn't documented by the project; try it, or run it in WSL. |
| PDF text and pages | **poppler** | `brew install poppler` | `scoop install poppler` | Gives `pdftotext`, `pdfinfo`, `pdftoppm`, `pdfimages`. |
| PDF alternative | **mupdf-tools** | `brew install mupdf-tools` | `scoop install mupdf` | `mutool` renders pages to PNG and extracts text; good on odd PDFs. |
| PDF to Markdown | **markitdown** | `pipx install "markitdown[all]"` | same | One CLI for PDF, DOCX, PPTX, XLSX, HTML to Markdown. Weaker on complex tables. |
| PDF to Markdown (layout-aware) | **docling** | `pipx install docling` | same | Heavier ML pipeline; best on tables and multi-column papers. |
| Scanned PDFs | **ocrmypdf** | `brew install ocrmypdf` | `pip install ocrmypdf` plus Tesseract and Ghostscript, or use WSL | Adds a text layer to scans so the other tools can read them. |
| Document conversion | **pandoc** | `brew install pandoc` | `scoop install pandoc` | DOCX, EPUB, HTML to and from Markdown. |
| Version history | **git** | `brew install git` | `scoop install git` | Optional. Skip it if the vault lives in OneDrive, iCloud or Dropbox: the sync service keeps file history, and the two fight over files. Otherwise `.gitignore` and `.gitattributes` are ready. |
| Obsidian itself | Obsidian | `brew install --cask obsidian` | `winget install Obsidian.Obsidian` | Has an official CLI (1.12+; enable in Settings, General) that drives the running app. |

`pipx` needs Python: `brew install pipx` / `scoop install pipx`.

## PDFs: what the AI should do

1. **Try reading the PDF directly first.** Claude Code's file reader handles PDFs, by page range for long ones.
2. **Long or text-heavy PDF:** `pdftotext -layout file.pdf -` (stdout) is cheap and keeps columns readable. Check size first with `pdfinfo file.pdf`.
3. **Figures, charts, equations matter:** render only the pages needed and view the image, e.g. `pdftoppm -png -r 150 -f 5 -l 5 file.pdf page` (writes `page-5.png`; put scratch images outside `raw/`).
4. **Tables or multi-column layout garbled:** `docling file.pdf` or `markitdown file.pdf > out.md`.
5. **No text layer (scan):** `ocrmypdf in.pdf out.pdf` into a scratch location; never overwrite the original in `raw/`.

Never write derived files into `raw/`; it is immutable. Keep any conversions in a scratch folder outside the vault, and record the key facts in the source page instead.

## Search: by scale

| Wiki size | Use |
|---|---|
| Up to ~100 pages | Read [[index]], open the relevant pages. Add `rg` for exact terms. |
| ~100 pages and up | Add **qmd** for semantic queries: `qmd collection add . --name __SLUG__`, then `qmd embed`; query with `qmd query "..."` (hybrid), `qmd search` (keywords) or `qmd vsearch` (semantic); fetch with `qmd get`. `qmd mcp` exposes it to the AI as an MCP server. |

## Same job on both platforms

| Job | mac (zsh/bash) | win (PowerShell) |
|---|---|---|
| Last 5 log entries | `rg '^## \[' wiki/log.md \| tail -5` | `Select-String '^## \[' wiki/log.md \| Select-Object -Last 5` |
| Pages mentioning a term | `rg -il "term" wiki synthesis` | `rg -il "term" wiki synthesis` |
| All notes | `fd -e md . wiki` | `fd -e md . wiki` |
| Pages not marked stable | `rg --files-without-match '^status: stable' wiki --glob '*.md'` | `rg --files-without-match '^status: stable' wiki --glob '*.md'` |
| Notes linking to a page | `rg -l '\[\[page-name' wiki synthesis` | `rg -l '\[\[page-name' wiki synthesis` |
| PDF page count | `pdfinfo f.pdf \| grep Pages` | `pdfinfo f.pdf \| Select-String Pages` |

`rg` and `fd` behave the same on both systems, so prefer them over `grep` and `find`, which differ.

## Portability checklist

- Filenames: lowercase kebab-case, no `\ / : * ? " < > |`, no reserved Windows names, no names differing only by case (macOS and Windows file systems are case-insensitive by default).
- No symlinks, no absolute paths in notes, short paths (Windows path-length limits).
- LF line endings everywhere (`.gitattributes` enforces it); configure your editor not to convert.
- Cloud-synced folders (OneDrive, iCloud, Dropbox) are fine; use the sync service's version history rather than adding git on top. Let a sync finish before opening the vault on another machine, or the two copies of a page can turn into a conflict file.
