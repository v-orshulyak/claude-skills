---
name: wiki-capture
description: Save a new source into raw/ of this LLM wiki so it can be ingested - a web page or PDF from a URL, text the user pastes, or a file from elsewhere on disk - under a clean dated kebab-case name with capture metadata, never touching existing raw files. Use whenever the user says "save this article", "capture this URL", "clip this", "add this PDF to raw", "here's a link/paper/transcript for the wiki", pastes a URL or a block of text meant for the wiki, or when wiki-ingest or wiki-research needs a source saved first.
---

# Wiki capture

`raw/` is the human's layer of original sources: every source page in the wiki links to a file there, so the original must exist and stay put. Capturing is how a source from outside gets there faithfully. After capture the file is immutable like the rest of `raw/` (a hook enforces this in Claude Code: new files may be added, existing ones never changed).

On Windows use `py` or `python` instead of `python3` in the commands below.

## 1. Name it

- Web page or pasted text: `raw/YYYY-MM-DD-<short-slug>.md` (date = published date if known, else today).
- PDF or other file: keep its extension, kebab-case the rest: `raw/2024-smith-attention-survey.pdf`. Images and attachments that belong to a source go in `raw/assets/`.
- Check the name is free; links resolve by name across the whole vault, so it must not clash with any note:
  ```bash
  python3 "${CLAUDE_SKILL_DIR}/../wiki-lint/scripts/lint.py" --names 2025-03-04-some-article
  ```

## 2. Capture faithfully

The point of `raw/` is the original wording, so don't summarise or "clean up" content while capturing.

- **PDF URL:** download it as is, e.g. `curl -L -o raw/<name>.pdf "<url>"`.
- **Web page:** best fidelity first. If the user has the Obsidian Web Clipper, suggest it (it writes straight into `raw/`). Otherwise fetch the HTML and convert it locally (`curl -L "<url>" -o <scratch>/page.html`, then `markitdown <scratch>/page.html` or `pandoc -f html -t gfm`), keeping scratch files outside the vault. The web-fetch tool returns a model-processed version of the page; use it only as a fallback, ask it for the full text verbatim, and record `capture: web-fetch (may be abridged)`.
- **Pasted text:** save it exactly as given.
- **File elsewhere on disk:** copy it in (`cp`), don't move it, unless the user asks.
- Paywalled, login-only or bot-protected pages: don't work around them; ask the user to save the page themselves (Web Clipper, print to PDF) and drop it in `raw/`.

For Markdown captures, put a small frontmatter block on top so provenance survives:

```yaml
---
title: "Original title"
source: "https://example.com/article"
author: "Name"
published: 2025-03-04
captured: 2025-03-05
capture: curl+markitdown
---
```

Binary files (PDFs, Office files) carry no frontmatter; the source page written at ingest records their origin.

## 3. Log and hand over

- Append to `wiki/log.md`: `## [YYYY-MM-DD] capture | <title>` with the file path in backticks (it has no source page yet, so no wikilink).
- Tell the user what was saved where, and offer to ingest it now (the `wiki-ingest` skill). For several captures, offer one batch ingest.
