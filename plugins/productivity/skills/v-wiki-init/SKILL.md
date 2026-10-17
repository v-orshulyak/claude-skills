---
name: v-wiki-init
description: Scaffold a new LLM-maintained wiki (Karpathy's "LLM Wiki" pattern) as an Obsidian vault with raw, wiki and synthesis layers, a CLAUDE.md rulebook, page templates and a bundled Obsidian profile. Manual only - run /v-wiki-init.
disable-model-invocation: true
---

# v-wiki-init

Creates the starting point of an **LLM Wiki**: instead of retrieving raw document chunks on every question, the AI incrementally builds and maintains a persistent, interlinked set of Markdown pages between the user and their sources. The user curates sources and asks questions; the AI does the summarising, cross-referencing, filing and bookkeeping. Obsidian is the viewer; the AI is the maintainer.

This skill only does the **initial setup**. Day-to-day ingest / query / lint behaviour lives in the generated vault's `CLAUDE.md`, so any future session in that vault follows the same rules without this skill.

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
└── .obsidian/           # wikilinks, attachment folder, graph colours, templates
                         # + bundled profile: theme, plugins, settings
```

The `synthesis/` layer is deliberately separate from `wiki/`: the wiki is the single source of truth and is kept clean; reports, briefs, decks and FAQs are downstream products that read from the wiki, cite it with wikilinks, and can be regenerated or thrown away. Never write synthesis content into `wiki/`.

## Workflow

### 1. Ask first - nothing else before this

Your first action is to ask the user for two things, in one short message:

- **Project name**
- **Short description** (one or two sentences: what the wiki is about / what it is for)

Also mention, in the same message, the default destination (`./<slug>` under the current directory) and that the vault will come with their bundled Obsidian setup (theme, plugins, settings - see "Obsidian profile" below), so they can override the destination or ask for plain Obsidian defaults in the same reply. Do not scan the filesystem, create folders or run tools before they answer. If the invocation already contains a name and description (and possibly a destination), restate them in one line and ask for a quick confirmation; an explicit "just do it" from the user skips even that.

### 2. Resolve the destination

- Derive `slug` = lowercase ASCII kebab-case of the project name (the script does this too). `--dest` is the vault folder itself, not its parent, so for the default pass `./<slug>`.
- If the destination exists and is non-empty, say so and ask whether to scaffold into it anyway (existing files are never overwritten; the script reports what it skipped - this is how a user adds the structure to an existing Obsidian vault) or pick another path.
- If the path sits under iCloud Drive (`Mobile Documents`), OneDrive or Dropbox, mention that sync conflicts and git can fight each other, and let them choose.

### 3. Run the scaffold script

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/scaffold.py" --name "<Project name>" --description "<description>" --dest "<path>"
```

By default the vault gets the bundled Obsidian profile. Add `--no-profile` if the user wants minimal stock settings, or `--obsidian-from "<vault>"` to use another vault's `.obsidian` instead (see "Obsidian profile").

On Windows use `py` or `python` instead of `python3`. The script copies `assets/template/`, fills the `__PROJECT_NAME__`, `__DESCRIPTION__`, `__SLUG__`, `__DATE__` tokens, writes LF line endings on every OS, never overwrites existing files, and finishes with a self-check (valid JSON, no leftover tokens, every wikilink resolves, no duplicate note names). Read its report: it lists every file created or skipped, and exits non-zero if the self-check fails (fix the cause, then re-run with `--check`). If Python is unavailable, create the same files by hand from `assets/template/` (mapping `dot-X` to `.X`) and say you did.

### Obsidian profile

The skill is self-contained: `assets/obsidian-profile/` bundles the user's Obsidian setup (appearance, the active theme, 16 community plugins with their settings, core-plugin choices, property types), so a new vault looks and behaves like their others on any machine, with no dependency on another vault being present. The script applies it by default; `--obsidian-from` swaps in another vault's `.obsidian` for one run.

Applying a profile copies the appearance, active theme, core-plugin choices, enabled community plugins (code and settings), property types and hotkeys, and merges `app.json`, `templates.json` and `graph.json`. It then re-asserts the few settings the wiki rules depend on (wikilinks, shortest-path links, auto-update on rename, `raw/assets` attachments, the `templates/` folder, graph colour groups, and the core plugins templates, backlinks, graph, properties, bookmarks), so an imported setup can't silently break the link rules. It never copies workspace state, bookmarks, or caches, only takes an explicit list of settings files (so OneDrive-style conflict copies like `app 2.json` are ignored), and leaves `data.json` out of any plugin whose settings look like they hold an API key or token. Report which plugin settings were skipped and why.

Community plugins need Obsidian's "trust author / turn on community plugins" prompt accepted once per vault. Mention it in the hand-over.

### 4. Tailor to the project

The template is generic on purpose. Using the description, edit the generated vault - and only these places:

- `CLAUDE.md` -> replace the bullets under **Domain focus** (and the italic note above them) with what counts as a source here, the 4-6 kinds of entities and concepts worth their own pages, vocabulary/tag/unit conventions, and anything the user said that should shape the wiki (audience, language, depth). Keep it to roughly 15 lines: this file is read at the start of every session, so every line costs attention each time.
- `wiki/overview.md` -> replace the text under `## Scope` (the raw description) with a one-paragraph statement of scope; leave the other sections.
- `wiki/log.md` -> add a `schema` entry saying the domain focus was tailored.

Leave the layer rules, link rules and workflows untouched; they are what keeps the wiki consistent across sessions. Write any wikilink *examples* inside backticks, since a bare `[[x]]` becomes an unresolved ghost node in Obsidian's graph. Re-run the link check afterwards (`python3 "${CLAUDE_SKILL_DIR}/scripts/scaffold.py" --check "<path>"`) and fix anything it reports.

### 5. Propose CLI tooling (macOS and Windows)

The generated `TOOLS.md` holds the full table with install commands for both platforms. Detect the OS and which tools are already present, including the package manager the install commands need (`brew`, `pipx`, `node` on macOS; `scoop`, `pipx`, `node` on Windows). Use `command -v rg fd jq yq qmd pdftotext mutool markitdown docling ocrmypdf pandoc` on macOS/Linux, or `Get-Command` with the same names on Windows. Give the user a short summary - installed vs. missing - not the whole table:

- **Search:** `ripgrep` (always worth it), `fd`, `jq`/`yq` for frontmatter; `qmd` once the wiki outgrows `index.md` (~100+ pages) for hybrid keyword/semantic search with an MCP server.
- **PDFs:** Claude can read PDFs directly; add `poppler` (`pdftotext`, `pdfinfo`, `pdftoppm` to render pages as images when figures matter), and `markitdown` or `docling` for PDF/Office -> Markdown on large or table-heavy files; `ocrmypdf` for scans.

Offer the install commands for the missing ones, and run them only if the user says yes. Installing software changes their machine, so it needs their go-ahead each time.

### 6. Hand over

Show a compact tree of what was created (from the script's file list) and anything it skipped or flagged. Then give the three next steps, briefly:

1. In Obsidian: **Open folder as vault** -> the new folder (accept "trust author" so `.obsidian` settings load).
2. Drop a first source into `raw/` (or use the Obsidian Web Clipper) and say: "Ingest `raw/<file>`".
3. Open the vault folder in Claude Code (or any agent that reads `CLAUDE.md`/`AGENTS.md`) so the rules apply.

Offer `git init` rather than doing it. If they agree, the template already ships `.gitignore` and `.gitattributes` (LF endings, so Windows and macOS don't produce noisy diffs).

## Notes for maintaining this skill

- **Refreshing the bundled Obsidian profile** after the user changes their setup: `python3 scripts/scaffold.py --snapshot-profile "<vault>"`. It rewrites `assets/obsidian-profile/` with runtime files only (`main.js`, `manifest.json`, `styles.css`, sanitised `data.json`), blanks vault-specific plugin data (file colours, cached tags), and leaves out any `data.json` that looks like it holds a credential. The profile is about 18 MB of third-party plugin code; check the plugins' licences before making the repo public.

- Template files live in `assets/template/`; hidden files are stored with a `dot-` prefix (`dot-obsidian`, `dot-gitignore`) so they survive packaging and git ignore rules.
- Scaffold tokens use `__DOUBLE_UNDERSCORE__` syntax because the Obsidian Templates plugin owns `{{...}}`.
- Wikilink examples inside template docs must sit in backticks/code fences; a bare `[[example]]` becomes an unresolved ghost node in Obsidian's graph.
- Note filenames must stay unique across the whole vault (Obsidian's "shortest path" links depend on it), which is why the synthesis catalog is `synthesis-index.md` and not a second `index.md`.
