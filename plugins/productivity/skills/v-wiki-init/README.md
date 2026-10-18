# v-wiki-init

Sets up a knowledge base that Claude writes and maintains for you: an Obsidian vault built on Andrej Karpathy's "LLM Wiki" pattern. Run it once per topic with `/v-wiki-init [name] [description]`. It is manual only, so Claude never starts it by itself.

## What it is

A one-time scaffolder. It asks for a project name and a short description, then creates a vault with three layers:

| Layer | Holds | Written by |
|---|---|---|
| `raw/` | Original sources (PDFs, articles, transcripts, exports). Never edited. | You, or Claude saving a source for you |
| `wiki/` | Source summaries and entity, concept and analysis pages, all linked, plus `index`, `log` and `overview` | Claude |
| `synthesis/` | Reports, briefs, decks, FAQs and timelines built from the wiki when you ask | Claude, on request |

It also fits the vault's `CLAUDE.md` to your topic (what counts as a source, which entities and concepts deserve their own pages, vocabulary), applies your bundled Obsidian setup (theme, 16 plugins, settings), checks that Python is installed and suggests optional CLI tools such as ripgrep and poppler.

The skill is only needed for setup. Everything the vault needs afterwards ships inside it, in `.claude/`:

- **Six workflows as project skills**: `wiki-capture` (save a URL, file or pasted text into `raw/`), `wiki-ingest` (summarise a source and update the 5-15 pages it touches; whole books are read in resumable chunks), `wiki-lint` (orphans, broken links, missing dates and sources, stale artifacts), `wiki-refactor` (rename or merge pages and rewrite every link), `wiki-research` (find sources for open questions) and `wiki-synthesize` (build an artifact from the wiki, with citations).
- **A `wiki-source-reader` subagent** for reading long sources.
- **Hooks** that block edits and deletes in `raw/`, open each session with the recent log and sources not yet ingested, and stop Claude from finishing a turn that changed the wiki without a log entry, updated dates and working links.

So the vault works on any machine or clone that has Claude Code, even without this plugin.

## What problem it solves

Asking an AI about your documents usually means retrieval: on every question it searches raw chunks, pieces an answer together and forgets it. Nothing builds up. Contradictions between sources stay hidden, a good answer is lost when the chat ends, and the same documents are read again and again.

An LLM wiki turns that into compounding work. Each source is read once, carefully, and its content is filed into durable, cross-linked pages with citations back to the original. Later questions are answered from the wiki, which is already organised, and good answers can be saved as pages too. You curate sources and ask questions; Claude does the summarising, cross-referencing and bookkeeping that people usually give up on.

Setting this up by hand is fiddly: folder layout, a rulebook strict enough to keep pages consistent across sessions, page templates, Obsidian settings that match the link rules, and guard rails so the AI does not rewrite your sources or skip the bookkeeping. This skill does all of it in one run, the same way every time, on macOS and Windows.

## When to use it

Use it when you start a body of knowledge that will grow over weeks or months, from many sources, and that you will keep asking questions about. For example:

- researching a field or technology (papers, articles, talks)
- learning from books, courses or lecture notes
- tracking a market, competitors or a long-running project (reports, meeting notes, exports)
- a personal knowledge base on a hobby, health topic or big decision

It is not the right tool when:

- you have a handful of documents and one question: just give them to Claude in a chat
- the content is code or project docs that belong in a repository
- you want to write the notes yourself: in this setup Claude owns `wiki/`

You can also run it inside an existing Obsidian vault. It never overwrites files, keeps that vault's `.obsidian` settings, and reports settings that clash with the wiki rules instead of changing them.

## After setup

1. In Obsidian, **Open folder as vault** and allow community plugins once.
2. Open the folder in Claude Code and accept the folder-trust prompt, so the skills and hooks load.
3. Add a first source ("Save this article: <url>", or drop a file into `raw/`) and say "Ingest `raw/<file>`". About every 10 ingests, say "Health-check the wiki".

Prerequisites: Python 3.9+ (the scaffold and the vault's hooks and scripts use it), and Git for Windows on Windows (Claude Code runs hooks through Git Bash). The skill checks both before creating anything and offers to install what is missing (`brew` on macOS, `winget` on Windows). If you decline or the install fails, it stops without creating a vault and lists what you need to install. Git itself is optional, and best avoided for a vault in OneDrive, iCloud or Dropbox.

## Maintainer notes

Notes for changing this skill. `SKILL.md` is what the model reads when the skill runs; keep it to what that run needs and put maintenance detail here.

### Testing

```bash
python3 scripts/scaffold.py --name "Test" --description "Scratch run" --dest <scratch dir>/test
python3 scripts/scaffold.py --check <scratch dir>/test
```

The vault's lint script runs on its own too: `python3 <vault>/.claude/skills/wiki-lint/scripts/lint.py` (add `--json`, `--names a b`, `--new-sources`, `--files <page> ...`). A fresh vault must report no findings.

Hooks and the refactor script are testable without Claude Code: feed the hook a JSON event on stdin with `CLAUDE_PROJECT_DIR` set to the vault, e.g. `echo '{"tool_name":"Bash","tool_input":{"command":"rm raw/a.md"},"cwd":"<vault>"}' | CLAUDE_PROJECT_DIR=<vault> python3 <vault>/.claude/hooks/wiki_hooks.py guard` must print a `deny`. For the Stop check run `prompt`, change a wiki page, then `stop`. Run these from bash: zsh does not word-split a command held in a variable. For refactor, build two concept pages that link each other plus index and log lines, then `rename` and `merge` with and without `--dry-run`; lint must come back clean and links inside code must stay.

Worth covering after a change: a fresh vault (with and without `--no-profile`), a re-run into the same folder (everything skipped), and an existing vault that has its own `.obsidian`, its own notes with broken links, and `"useMarkdownLinks": true` in `app.json`. The last one must exit 0, skip the bundled profile, list the user's broken links as warnings, and report the setting conflict without changing it.

### Bundled Obsidian profile

- Refresh it after changing your Obsidian setup: `python3 scripts/scaffold.py --snapshot-profile "<vault>"`. It rewrites `assets/obsidian-profile/` with runtime files only (`main.js`, `manifest.json`, `styles.css`, sanitised `data.json`), blanks vault-specific plugin data (file colours, cached tags), and leaves out any `data.json` that looks like it holds a credential.
- Applying it copies appearance, the active theme, core-plugin choices, the enabled community plugins (code and settings), property types and hotkeys, and merges `app.json`, `templates.json` and `graph.json`, then re-asserts the wiki-critical settings. It only reads an explicit list of settings files (so OneDrive-style conflict copies like `app 2.json` are ignored) and never copies workspace state, bookmarks or caches.
- In an existing vault only files the run created are rewritten; the theme is copied only if the run also set `appearance.json`, and plugin folders only for plugins the destination's `community-plugins.json` enables.
- The profile is about 18 MB of third-party plugin code; check the plugins' licences before making the repo public.

### Vault skills, hooks, rules and agents

- Python 3.9+ is a prerequisite: SKILL.md step 3 checks it (and Git Bash on Windows) before scaffolding and offers the install; `TOOLS.md` lists both under "Required". Git is optional and not suggested for vaults in a sync folder.
- There is deliberately no hand-built fallback: if Python (or Git Bash on Windows) is missing and the user declines the install, SKILL.md step 3 blocks before creating anything. A Windows run that hand-wrote the vault into the real folder crashed half-way, left a partial `.obsidian` (so the profile was skipped later) and made cleanup look destructive.
- After installing Python in the same session, the scaffold runs by the interpreter's full path (macOS `$(brew --prefix)/bin/python3`, Windows `%LOCALAPPDATA%\Programs\Python\Python3*\python.exe`), since the shell's PATH is stale; the hooks need a restarted Claude Code, and the hand-over asks the user to confirm them with `/hooks`. The macOS path is untested.
- The template ships six project skills in `dot-claude/skills/` (becomes `.claude/skills/`): `wiki-capture`, `wiki-ingest`, `wiki-research`, `wiki-synthesize` (procedures only), `wiki-lint` (+ `scripts/lint.py`) and `wiki-refactor` (+ `scripts/refactor.py`, which imports lint.py for parsing). They are deliberately vault-local rather than skills in this plugin: the vault stays self-contained (works on a clone without the plugin), and each vault's rules can evolve with its user, like its `CLAUDE.md`. The cost is that a fix here reaches only vaults scaffolded afterwards; copy the files into older vaults by hand.
- The vault's `CLAUDE.md` keeps a 1-2 line summary of each workflow and points at the `SKILL.md`, so agents without skill support still find the procedure.
- `wiki-ingest` calls the sibling `../wiki-lint/scripts/lint.py` (`--new-sources`, `--names`, `--files`, plain lint) rather than shipping a second script.
- `wiki-ingest` estimates size first with its own `scripts/source_info.py` (pages via `pdfinfo`, else the PDF page tree, including compressed object streams; words for md/txt/html/docx/epub; outline via `mutool` when installed). The verdict picks the flow: small = read directly, medium = one reader subagent, large (100+ pages / 50k+ words) = `references/large-sources.md`: survey, reading map on a book page (`ingest-status: partial`, `- [x]`/`- [ ]`/`- [-]` lines), chunk pages with `part-of:`, 2-3 chunks per batch, resume from the map. Thresholds are constants at the top of the script. `lint.py` reports partial sources and does not flag sibling chunk pages (same `raw:`) as near-duplicates; the session brief lists them.
- Large-source progress lives in the wiki, not in a cache: each chunk leaves the wiki consistent, so an interrupted session loses at most one chunk.
- `dot-claude/agents/wiki-source-reader.md` is a read-only subagent (`model: inherit`; set `sonnet` to make long-source reading cheaper) that `wiki-ingest` delegates to, in whole-file, survey or page-range mode. Locators are PDF page indices, because that is what `[[file.pdf#page=N]]` opens.
- `dot-claude/rules/synthesis.md` (`paths: synthesis/**`) holds the synthesis invariants, so the vault's `CLAUDE.md` keeps only a summary. Path-scoped rules load when Claude reads or writes a matching file, not at session start.
- `dot-claude/settings.json` wires `dot-claude/hooks/wiki_hooks.py`:
  - **PreToolUse** (`Bash|Edit|MultiEdit|Write|NotebookEdit`): denies edits, overwrites, moves out of and deletes in `raw/` (a best-effort parse of shell commands; not a sandbox), and auto-approves `python <vault>/.claude/skills/wiki-*/scripts/*.py` with no shell operators. It is a hook rather than a permission rule because `Edit(/raw/**)` deny rules also block `Write`, which `wiki-capture` needs to add new files.
  - **SessionStart**: recent log headings, raw files not ingested, lint nudge after 10 ingests.
  - **UserPromptSubmit** snapshots `wiki/` + `synthesis/` (mtime, size, a hash that ignores link targets and date fields) into `<temp>/claude-wiki-<vault hash>-<session id>.json`. It lives outside the vault because vaults usually sit in OneDrive/iCloud/Dropbox, where a file rewritten on every prompt would sync and spawn conflict copies; **Stop** compares against it and blocks once per turn (`stop_hook_active`) if the log has no new entry, a content-changed page lacks today's `updated:`/`generated:`, or lint finds problems in changed pages. The hash ignores link targets so renames and link rewrites from `wiki-refactor` don't demand date bumps.
  - Every hook command is `sh "${CLAUDE_PROJECT_DIR}/.claude/hooks/run.sh" <action>`. `run.sh` (POSIX sh, no external commands) tries `py`, `python3`, `python`, skips the Windows Store stub (`*WindowsApps*`), requires 3.9+, and `exec`s `wiki_hooks.py`. With no usable Python it exits 0 quietly, except on `session-start`, where it prints one line that becomes context, so Claude tells the user once instead of a hook error on every tool call.
  - On Windows, hooks run through Git Bash; without it Claude Code uses PowerShell, `sh` is not found and every hook errors. That is why SKILL.md checks for Git Bash on Windows even though git itself is optional. This path is untested on Windows so far.
  - Any exception exits 1 (a non-blocking hook error), so a bug never locks the session.
- Allowed Bash commands in `settings.json` are read-only tools (`rg`, `fd`, PDF tools). Mid-string wildcards like `Bash(python3 *lint.py*)` are valid but trigger a startup warning, which is why the scripts are approved by the hook instead.
- `lint.py` is the single source of truth for wikilink parsing: `scaffold.py` imports it from the template for its self-check. Keep it stdlib-only, Python 3.9+ and read-only, and never write the scaffold tokens (`__PROJECT_NAME__` and friends) in it: the scaffold replaces them in every file it copies.
- Obsidian ignores hidden folders, so nothing in `.claude/` adds graph nodes; the self-check still scans every `.claude/**/*.md` for tokens and stray wikilinks (keep link examples in backticks) and validates `.claude/*.json`.
- Scaffolding into a vault that already has `.claude/settings.json` keeps it and prints that the hooks are not active; SKILL.md tells the model to offer a merge.

### Template conventions

- Template files live in `assets/template/`; hidden files (including `.gitkeep`) are stored with a `dot-` prefix so they survive packaging and git ignore rules.
- Scaffold tokens use `__DOUBLE_UNDERSCORE__` syntax because the Obsidian Templates plugin owns `{{...}}`.
- Wikilink examples inside template docs must sit in backticks or code fences; a bare `[[example]]` becomes an unresolved ghost node in Obsidian's graph.
- Note filenames must stay unique across the whole vault (Obsidian's "shortest path" links depend on it), which is why the synthesis catalog is `synthesis-index.md` and not a second `index.md`.
