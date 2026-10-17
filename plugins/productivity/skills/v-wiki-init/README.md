# v-wiki-init - maintainer notes

Notes for changing this skill. `SKILL.md` is what the model reads when the skill runs; keep it to what that run needs and put maintenance detail here.

## Testing

```bash
python3 scripts/scaffold.py --name "Test" --description "Scratch run" --dest <scratch dir>/test
python3 scripts/scaffold.py --check <scratch dir>/test
```

Worth covering after a change: a fresh vault (with and without `--no-profile`), a re-run into the same folder (everything skipped), and an existing vault that has its own `.obsidian`, its own notes with broken links, and `"useMarkdownLinks": true` in `app.json`. The last one must exit 0, skip the bundled profile, list the user's broken links as warnings, and report the setting conflict without changing it.

## Bundled Obsidian profile

- Refresh it after changing your Obsidian setup: `python3 scripts/scaffold.py --snapshot-profile "<vault>"`. It rewrites `assets/obsidian-profile/` with runtime files only (`main.js`, `manifest.json`, `styles.css`, sanitised `data.json`), blanks vault-specific plugin data (file colours, cached tags), and leaves out any `data.json` that looks like it holds a credential.
- Applying it copies appearance, the active theme, core-plugin choices, the enabled community plugins (code and settings), property types and hotkeys, and merges `app.json`, `templates.json` and `graph.json`, then re-asserts the wiki-critical settings. It only reads an explicit list of settings files (so OneDrive-style conflict copies like `app 2.json` are ignored) and never copies workspace state, bookmarks or caches.
- In an existing vault only files the run created are rewritten; the theme is copied only if the run also set `appearance.json`, and plugin folders only for plugins the destination's `community-plugins.json` enables.
- The profile is about 18 MB of third-party plugin code; check the plugins' licences before making the repo public.

## Template conventions

- Template files live in `assets/template/`; hidden files (including `.gitkeep`) are stored with a `dot-` prefix so they survive packaging and git ignore rules.
- Scaffold tokens use `__DOUBLE_UNDERSCORE__` syntax because the Obsidian Templates plugin owns `{{...}}`.
- Wikilink examples inside template docs must sit in backticks or code fences; a bare `[[example]]` becomes an unresolved ghost node in Obsidian's graph.
- Note filenames must stay unique across the whole vault (Obsidian's "shortest path" links depend on it), which is why the synthesis catalog is `synthesis-index.md` and not a second `index.md`.
