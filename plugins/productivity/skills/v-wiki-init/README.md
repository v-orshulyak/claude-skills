# v-wiki-init - maintainer notes

Notes for changing this skill. `SKILL.md` is what the model reads when the skill runs; keep it to what that run needs and put maintenance detail here.

## Testing

```bash
python3 scripts/scaffold.py --name "Test" --description "Scratch run" --dest <scratch dir>/test
python3 scripts/scaffold.py --check <scratch dir>/test
```

The vault's lint script runs on its own too: `python3 <vault>/.claude/skills/wiki-lint/scripts/lint.py` (add `--json`, `--names a b`, `--new-sources`). A fresh vault must report no findings.

Worth covering after a change: a fresh vault (with and without `--no-profile`), a re-run into the same folder (everything skipped), and an existing vault that has its own `.obsidian`, its own notes with broken links, and `"useMarkdownLinks": true` in `app.json`. The last one must exit 0, skip the bundled profile, list the user's broken links as warnings, and report the setting conflict without changing it.

## Bundled Obsidian profile

- Refresh it after changing your Obsidian setup: `python3 scripts/scaffold.py --snapshot-profile "<vault>"`. It rewrites `assets/obsidian-profile/` with runtime files only (`main.js`, `manifest.json`, `styles.css`, sanitised `data.json`), blanks vault-specific plugin data (file colours, cached tags), and leaves out any `data.json` that looks like it holds a credential.
- Applying it copies appearance, the active theme, core-plugin choices, the enabled community plugins (code and settings), property types and hotkeys, and merges `app.json`, `templates.json` and `graph.json`, then re-asserts the wiki-critical settings. It only reads an explicit list of settings files (so OneDrive-style conflict copies like `app 2.json` are ignored) and never copies workspace state, bookmarks or caches.
- In an existing vault only files the run created are rewritten; the theme is copied only if the run also set `appearance.json`, and plugin folders only for plugins the destination's `community-plugins.json` enables.
- The profile is about 18 MB of third-party plugin code; check the plugins' licences before making the repo public.

## Vault skills

- The template ships two project skills in `dot-claude/skills/` (becomes `.claude/skills/`): `wiki-ingest` (procedure only) and `wiki-lint` (procedure + `scripts/lint.py`). They are deliberately vault-local rather than skills in this plugin: the vault stays self-contained (works on a clone without the plugin), and each vault's rules can evolve with its user, like its `CLAUDE.md`. The cost is that a fix here reaches only vaults scaffolded afterwards; copy the files into older vaults by hand.
- The vault's `CLAUDE.md` keeps a 1-2 line summary of each workflow and points at the `SKILL.md`, so agents without skill support still find the procedure.
- `wiki-ingest` calls the sibling `../wiki-lint/scripts/lint.py` (`--new-sources`, `--names`, plain lint) rather than shipping a second script.
- `lint.py` is the single source of truth for wikilink parsing: `scaffold.py` imports it from the template for its self-check. Keep it stdlib-only, Python 3.9+ and read-only, and never write the scaffold tokens (`__PROJECT_NAME__` and friends) in it: the scaffold replaces them in every file it copies.
- Obsidian ignores hidden folders, so the skills add no graph nodes; the self-check still scans their `SKILL.md` for tokens and stray wikilinks, so keep link examples there in backticks.

## Template conventions

- Template files live in `assets/template/`; hidden files (including `.gitkeep`) are stored with a `dot-` prefix so they survive packaging and git ignore rules.
- Scaffold tokens use `__DOUBLE_UNDERSCORE__` syntax because the Obsidian Templates plugin owns `{{...}}`.
- Wikilink examples inside template docs must sit in backticks or code fences; a bare `[[example]]` becomes an unresolved ghost node in Obsidian's graph.
- Note filenames must stay unique across the whole vault (Obsidian's "shortest path" links depend on it), which is why the synthesis catalog is `synthesis-index.md` and not a second `index.md`.
