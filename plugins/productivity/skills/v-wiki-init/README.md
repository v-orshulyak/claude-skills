# v-wiki-init - maintainer notes

Notes for changing this skill. `SKILL.md` is what the model reads when the skill runs; keep it to what that run needs and put maintenance detail here.

## Testing

```bash
python3 scripts/scaffold.py --name "Test" --description "Scratch run" --dest <scratch dir>/test
python3 scripts/scaffold.py --check <scratch dir>/test
```

The vault's lint script runs on its own too: `python3 <vault>/.claude/skills/wiki-lint/scripts/lint.py` (add `--json`, `--names a b`, `--new-sources`, `--files <page> ...`). A fresh vault must report no findings.

Hooks and the refactor script are testable without Claude Code: feed the hook a JSON event on stdin with `CLAUDE_PROJECT_DIR` set to the vault, e.g. `echo '{"tool_name":"Bash","tool_input":{"command":"rm raw/a.md"},"cwd":"<vault>"}' | CLAUDE_PROJECT_DIR=<vault> python3 <vault>/.claude/hooks/wiki_hooks.py guard` must print a `deny`. For the Stop check run `prompt`, change a wiki page, then `stop`. Run these from bash: zsh does not word-split a command held in a variable. For refactor, build two concept pages that link each other plus index and log lines, then `rename` and `merge` with and without `--dry-run`; lint must come back clean and links inside code must stay.

Worth covering after a change: a fresh vault (with and without `--no-profile`), a re-run into the same folder (everything skipped), and an existing vault that has its own `.obsidian`, its own notes with broken links, and `"useMarkdownLinks": true` in `app.json`. The last one must exit 0, skip the bundled profile, list the user's broken links as warnings, and report the setting conflict without changing it.

## Bundled Obsidian profile

- Refresh it after changing your Obsidian setup: `python3 scripts/scaffold.py --snapshot-profile "<vault>"`. It rewrites `assets/obsidian-profile/` with runtime files only (`main.js`, `manifest.json`, `styles.css`, sanitised `data.json`), blanks vault-specific plugin data (file colours, cached tags), and leaves out any `data.json` that looks like it holds a credential.
- Applying it copies appearance, the active theme, core-plugin choices, the enabled community plugins (code and settings), property types and hotkeys, and merges `app.json`, `templates.json` and `graph.json`, then re-asserts the wiki-critical settings. It only reads an explicit list of settings files (so OneDrive-style conflict copies like `app 2.json` are ignored) and never copies workspace state, bookmarks or caches.
- In an existing vault only files the run created are rewritten; the theme is copied only if the run also set `appearance.json`, and plugin folders only for plugins the destination's `community-plugins.json` enables.
- The profile is about 18 MB of third-party plugin code; check the plugins' licences before making the repo public.

## Vault skills, hooks, rules and agents

- The template ships six project skills in `dot-claude/skills/` (becomes `.claude/skills/`): `wiki-capture`, `wiki-ingest`, `wiki-research`, `wiki-synthesize` (procedures only), `wiki-lint` (+ `scripts/lint.py`) and `wiki-refactor` (+ `scripts/refactor.py`, which imports lint.py for parsing). They are deliberately vault-local rather than skills in this plugin: the vault stays self-contained (works on a clone without the plugin), and each vault's rules can evolve with its user, like its `CLAUDE.md`. The cost is that a fix here reaches only vaults scaffolded afterwards; copy the files into older vaults by hand.
- The vault's `CLAUDE.md` keeps a 1-2 line summary of each workflow and points at the `SKILL.md`, so agents without skill support still find the procedure.
- `wiki-ingest` calls the sibling `../wiki-lint/scripts/lint.py` (`--new-sources`, `--names`, `--files`, plain lint) rather than shipping a second script.
- `dot-claude/agents/wiki-source-reader.md` is a read-only subagent (`model: inherit`; set `sonnet` to make long-source reading cheaper) that `wiki-ingest` delegates long sources and batches to.
- `dot-claude/rules/synthesis.md` (`paths: synthesis/**`) holds the synthesis invariants, so the vault's `CLAUDE.md` keeps only a summary. Path-scoped rules load when Claude reads or writes a matching file, not at session start.
- `dot-claude/settings.json` wires `dot-claude/hooks/wiki_hooks.py`:
  - **PreToolUse** (`Bash|Edit|MultiEdit|Write|NotebookEdit`): denies edits, overwrites, moves out of and deletes in `raw/` (a best-effort parse of shell commands; not a sandbox), and auto-approves `python <vault>/.claude/skills/wiki-*/scripts/*.py` with no shell operators. It is a hook rather than a permission rule because `Edit(/raw/**)` deny rules also block `Write`, which `wiki-capture` needs to add new files.
  - **SessionStart**: recent log headings, raw files not ingested, lint nudge after 10 ingests.
  - **UserPromptSubmit** snapshots `wiki/` + `synthesis/` (mtime, size, a hash that ignores link targets and date fields) into `.claude/.wiki-state.json` (gitignored); **Stop** compares against it and blocks once per turn (`stop_hook_active`) if the log has no new entry, a content-changed page lacks today's `updated:`/`generated:`, or lint finds problems in changed pages. The hash ignores link targets so renames and link rewrites from `wiki-refactor` don't demand date bumps.
  - The hook command picks `py`, then `python3`, then `python`: on Windows `python3` is often the Microsoft Store stub. Hooks run through Git Bash on Windows; this path is untested on Windows so far.
  - Any exception exits 1 (a non-blocking hook error), so a bug never locks the session.
- Allowed Bash commands in `settings.json` are read-only tools (`rg`, `fd`, PDF tools). Mid-string wildcards like `Bash(python3 *lint.py*)` are valid but trigger a startup warning, which is why the scripts are approved by the hook instead.
- `lint.py` is the single source of truth for wikilink parsing: `scaffold.py` imports it from the template for its self-check. Keep it stdlib-only, Python 3.9+ and read-only, and never write the scaffold tokens (`__PROJECT_NAME__` and friends) in it: the scaffold replaces them in every file it copies.
- Obsidian ignores hidden folders, so nothing in `.claude/` adds graph nodes; the self-check still scans every `.claude/**/*.md` for tokens and stray wikilinks (keep link examples in backticks) and validates `.claude/*.json`.
- Scaffolding into a vault that already has `.claude/settings.json` keeps it and prints that the hooks are not active; SKILL.md tells the model to offer a merge.

## Template conventions

- Template files live in `assets/template/`; hidden files (including `.gitkeep`) are stored with a `dot-` prefix so they survive packaging and git ignore rules.
- Scaffold tokens use `__DOUBLE_UNDERSCORE__` syntax because the Obsidian Templates plugin owns `{{...}}`.
- Wikilink examples inside template docs must sit in backticks or code fences; a bare `[[example]]` becomes an unresolved ghost node in Obsidian's graph.
- Note filenames must stay unique across the whole vault (Obsidian's "shortest path" links depend on it), which is why the synthesis catalog is `synthesis-index.md` and not a second `index.md`.
