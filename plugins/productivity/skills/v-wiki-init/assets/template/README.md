# __PROJECT_NAME__

__DESCRIPTION__

An LLM-maintained wiki, created on __DATE__. You add sources and ask questions; the AI writes and maintains the wiki. Rules for the AI live in [[CLAUDE.md]]; recommended command-line tools (macOS and Windows) are in [[TOOLS]].

## Open it in Obsidian

1. Obsidian -> **Open folder as vault** -> choose this folder (`__SLUG__`).
2. If asked, trust the vault author so the bundled `.obsidian` settings load.
3. Start at [[index]]. Use **Graph view** to spot hubs and orphans, and **Backlinks** to see what points at a page.

Obsidian is preconfigured for wikilinks, `raw/assets` as the attachment folder, and `templates/` for the Templates plugin.

## The layers

| Folder | What | Who writes |
|---|---|---|
| `raw/` | Original sources, never edited | You |
| `wiki/` | Summaries, entity and concept pages, [[index]], [[log]], [[overview]] | The AI |
| `synthesis/` | Reports, briefs, decks, FAQs generated from the wiki when you ask; catalog in [[synthesis-index]] | The AI, on request |

## Everyday use

Open this folder in Claude Code (or another agent that reads `CLAUDE.md` / `AGENTS.md`) and say things like:

- **Ingest:** "Ingest `raw/some-paper.pdf`" - the AI summarises it and updates 5-15 related pages.
- **Query:** "What do we know about X? Where do sources disagree?"
- **Save an answer:** "Save that comparison as an analysis page."
- **Lint:** "Health-check the wiki."
- **Synthesize:** "Write a one-page brief for the leadership team from the wiki." (lands in `synthesis/`)

## Handy Obsidian add-ons (optional)

- **Web Clipper** browser extension: clip articles to Markdown straight into `raw/`.
- **Dataview** community plugin: dynamic tables from page frontmatter.
- **Marp Slides** community plugin: render Markdown slide decks from `synthesis/`.
- Fix a hotkey for "download attachments for current file" so images are stored locally in `raw/assets` (the AI can then view them).

Put the vault under git if you want history: `.gitignore` and `.gitattributes` are already set up.
