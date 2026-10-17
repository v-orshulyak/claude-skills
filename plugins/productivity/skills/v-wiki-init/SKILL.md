---
name: v-wiki-init
description: Scaffold a new LLM-maintained wiki (Karpathy's "LLM Wiki" pattern) as an Obsidian vault with raw, wiki and synthesis layers, a CLAUDE.md rulebook, page templates and a bundled Obsidian profile. Manual only - run /v-wiki-init.
argument-hint: "[project name] [short description]"
disable-model-invocation: true
---

# v-wiki-init

Creates the starting point of an **LLM Wiki**: instead of retrieving raw document chunks on every question, the AI incrementally builds and maintains a persistent, interlinked set of Markdown pages between the user and their sources. The user curates sources and asks questions; the AI does the summarising, cross-referencing, filing and bookkeeping. Obsidian is the viewer; the AI is the maintainer.

This skill only does the **initial setup**. Day-to-day behaviour ships inside the generated vault: the rules and the query workflow in its `CLAUDE.md`, and ingest and lint as project skills in `.claude/skills/` (`wiki-ingest`, and `wiki-lint` with a deterministic lint script). Any future session in that vault follows the same rules without this skill.

## What gets generated

```
<slug>/
├── CLAUDE.md            # the schema: rules + workflows (AGENTS.md points to it)
├── README.md, TOOLS.md  # human intro; CLI tool guide (macOS + Windows)
├── raw/                 # layer 1: immutable sources (raw/assets for attachments)
├── wiki/                # layer 2: AI-owned pages: index, log, overview,
│   ├── sources/ entities/ concepts/ analyses/
├── synthesis/           # layer 3: artifacts generated ON DEMAND from the wiki
├── templates/           # Obsidian templates for every page type
├── .claude/skills/      # wiki-ingest, wiki-lint (+ scripts/lint.py); hidden in Obsidian
└── .obsidian/           # wikilinks, attachment folder, graph colours, templates
                         # + bundled profile: theme, plugins, settings
```

The `synthesis/` layer is deliberately separate from `wiki/`: the wiki is the single source of truth and is kept clean; reports, briefs, decks and FAQs are downstream products that read from the wiki, cite it with wikilinks, and can be regenerated or thrown away. Never write synthesis content into `wiki/`.

## Workflow

### 1. Ask first - nothing else before this

Your first action is to ask the user for two things, in one short message:

- **Project name**
- **Short description** (one or two sentences: what the wiki is about / what it is for)

Also mention, in the same message, the default destination (`./<slug>` under the current directory) and that the vault will come with their bundled Obsidian setup (theme, plugins, settings), so they can override the destination or ask for plain Obsidian defaults in the same reply. Do not scan the filesystem, create folders or run tools before they answer. If the invocation already contains a name and description (and possibly a destination), restate them in one line and ask for a quick confirmation; an explicit "just do it" from the user skips even that.

### 2. Resolve the destination

- Derive `slug` = lowercase ASCII kebab-case of the project name (the script does this too). `--dest` is the vault folder itself, not its parent, so for the default pass `./<slug>`.
- If the destination exists and is non-empty, say so and ask whether to scaffold into it anyway or pick another path. Scaffolding into an existing Obsidian vault is supported: existing files are never overwritten, the vault keeps its own `.obsidian` setup (the bundled profile is skipped), and the script reports settings that clash with the wiki rules instead of changing them.
- If the path sits under iCloud Drive (`Mobile Documents`), OneDrive or Dropbox, mention that sync conflicts and git can fight each other, and let them choose.

### 3. Run the scaffold script

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/scaffold.py" --name "<Project name>" --description "<description>" --dest "<path>"
```

The script needs Python 3.9+; on Windows use `py` or `python` instead of `python3`. It copies `assets/template/`, fills the `__PROJECT_NAME__`, `__DESCRIPTION__`, `__SLUG__`, `__DATE__` tokens, never overwrites existing files, applies the Obsidian profile, and finishes with a self-check (valid JSON, no leftover tokens, every wikilink resolves, no duplicate note names). If Python is unavailable, create the same files by hand from `assets/template/` (mapping `dot-X` to `.X`) and say you did.

**Obsidian profile.** `assets/obsidian-profile/` bundles the user's Obsidian setup (theme, 16 community plugins with their settings, core-plugin choices, property types), so a new vault looks like their others on any machine. It is applied by default to a vault without a `.obsidian` folder; the script then re-asserts the settings the wiki rules depend on (wikilinks, shortest-path links, `raw/assets` attachments, the `templates/` folder). Pass `--no-profile` for stock settings, or `--obsidian-from "<vault>"` to use another vault's `.obsidian` instead. Plugin settings that look like they hold a credential are left out; tell the user which.

**Reading the report.** It lists every file created or skipped, then up to three sections:

- *Self-check problems in the wiki's own files* make the script exit non-zero. Fix the cause, then re-run with `--check "<path>"`.
- *Issues in pre-existing files outside the wiki* (the user's own notes, in an existing vault) are not yours to fix. Mention them briefly and leave those files alone.
- *Obsidian settings that conflict with the wiki rules* (e.g. Markdown links instead of wikilinks) were left unchanged because they belong to the user's existing vault. Explain what each breaks and offer to change it in `.obsidian/`; edit only on their yes.

### 4. Tailor to the project

The template is generic on purpose. Using the description, edit the generated vault - and only these places:

- `CLAUDE.md` -> replace the bullets under **Domain focus** (and the italic note above them) with what counts as a source here, the 4-6 kinds of entities and concepts worth their own pages, vocabulary/tag/unit conventions, and anything the user said that should shape the wiki (audience, language, depth). Keep it to roughly 15 lines: this file is read at the start of every session, so every line costs attention each time.
- `wiki/overview.md` -> replace the text under `## Scope` (the raw description) with a one-paragraph statement of scope; leave the other sections.
- `wiki/log.md` -> add a `schema` entry saying the domain focus was tailored.

Leave the layer rules, link rules and workflows untouched; they are what keeps the wiki consistent across sessions. Write any wikilink *examples* inside backticks, since a bare `[[x]]` becomes an unresolved ghost node in Obsidian's graph. Re-run the link check afterwards (`python3 "${CLAUDE_SKILL_DIR}/scripts/scaffold.py" --check "<path>"`) and fix anything it reports in the wiki's own files.

### 5. Propose CLI tooling (macOS and Windows)

The generated `TOOLS.md` holds the full table with install commands for both platforms. Detect the OS and which tools are already present, including the package manager the install commands need (`brew`, `pipx`, `node` on macOS; `scoop`, `pipx`, `node` on Windows). Use `command -v rg fd jq yq qmd pdftotext mutool markitdown docling ocrmypdf pandoc` on macOS/Linux, or `Get-Command` with the same names on Windows. Give the user a short summary - installed vs. missing - not the whole table:

- **Search:** `ripgrep` (always worth it), `fd`, `jq`/`yq` for frontmatter; `qmd` once the wiki outgrows `index.md` (~100+ pages) for hybrid keyword/semantic search with an MCP server.
- **PDFs:** Claude can read PDFs directly; add `poppler` (`pdftotext`, `pdfinfo`, `pdftoppm` to render pages as images when figures matter), and `markitdown` or `docling` for PDF/Office -> Markdown on large or table-heavy files; `ocrmypdf` for scans.

Offer the install commands for the missing ones, and run them only if the user says yes. Installing software changes their machine, so it needs their go-ahead each time.

### 6. Hand over

Show a compact tree of what was created (from the script's file list) and anything it skipped or flagged. Then give the three next steps, briefly:

1. In Obsidian: **Open folder as vault** -> the new folder. Accept "trust author / turn on community plugins" once, so the bundled plugins and settings load.
2. Open the vault folder in Claude Code, so the rules and the `wiki-ingest` / `wiki-lint` skills load. Other agents that read `AGENTS.md` are pointed to the same files.
3. Drop a first source into `raw/` (or use the Obsidian Web Clipper) and say: "Ingest `raw/<file>`". Every ~10 ingests, say "Health-check the wiki".

Offer `git init` rather than doing it. If they agree, the template already ships `.gitignore` and `.gitattributes` (LF endings, so Windows and macOS don't produce noisy diffs; plugin settings are committed so a clone looks the same).
