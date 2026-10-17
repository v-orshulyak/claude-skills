# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal Claude Code plugin marketplace named **`v-skills`**. There is no build step or test suite — the repo is manifests plus Markdown skills.

## Layout

```
.claude-plugin/marketplace.json        # marketplace "v-skills"; lists every plugin by relative source
plugins/<plugin>/.claude-plugin/plugin.json
plugins/<plugin>/skills/<v-skill>/SKILL.md   (+ optional references/, scripts)
```

Current plugins: `productivity` (`v-wiki-init`, `v-retro`), `engineering` (`v-dotnet-as-java`), `finances` (empty). Empty plugins keep a `skills/.gitkeep` placeholder.

## Conventions

- **Every skill is prefixed `v-`**, so they are recognisable at a glance. The directory name and the `name:` in `SKILL.md` frontmatter must both be `v-<name>`. Plugin names are *not* prefixed (they are already namespaced by the `v-skills` marketplace, e.g. `engineering@v-skills`).
- Plugins group skills by theme; add a new skill to an existing plugin when it fits, otherwise create a new plugin.
- Adding a plugin means doing **both**: create `plugins/<name>/.claude-plugin/plugin.json` *and* add an entry to `.claude-plugin/marketplace.json` (`source: "./plugins/<name>"`). A plugin missing from the marketplace file is not installable.
- Skills must not hardcode install locations such as `.claude/skills/...`. Reference bundled files relative to the skill, and use `${CLAUDE_SKILL_DIR}` in shell commands.
- Keep SKILL.md `description:` rich in trigger phrases — it is what makes the skill fire. Exception: skills with `disable-model-invocation: true` (e.g. `v-wiki-init`) fire only when the user types `/<skill>`, so their description is just a short summary for the slash-command menu.

## Commands

```bash
claude plugin validate .                 # validate marketplace.json
claude plugin validate plugins/<name>    # validate one plugin manifest

claude plugin marketplace add .          # register this checkout locally as "v-skills"
claude plugin install <plugin>@v-skills  # install a plugin from it
```

After editing a skill, `claude plugin marketplace update v-skills` (or reinstall) picks up the change; plugins are copied to a cache on install.

## Git identity

**Every commit in this repo must be authored from the personal GitHub account**, never the work identity that is set globally:

- user.name `v-orshulyak`, user.email `vladorshulyak@gmail.com`
- The identity is set in this repo's local git config (`git config --local`). If `git config --local user.email` is empty, set both before committing; do not rely on or change the global config.
- Verify before pushing: `git log -1 --format='%an <%ae>'` must print `v-orshulyak <vladorshulyak@gmail.com>`.
- The remote `origin` is `https://github.com/v-orshulyak/claude-skills.git`; push with credentials for the `v-orshulyak` account, not the work one.
- **Switch `gh` to the personal account before any push or other GitHub operation on this repo**, and switch back to the work account (`OnLocation-Vorshulyak-Contractor`) when done, because the active `gh` account applies to every repo on the machine:
  1. `gh auth switch --user v-orshulyak`
  2. Check `gh auth status` shows `v-orshulyak` as active.
  3. Push: `git -c credential.helper= -c "credential.helper=!gh auth git-credential" push origin main` (plain `git push` uses the macOS keychain, not `gh`, so it may authenticate as the wrong account).
  4. `gh auth switch --user OnLocation-Vorshulyak-Contractor`
  
  The switch changes the user's global auth state, so tell the user before doing it; never run `gh auth login` yourself (it is interactive and needs their browser).

## Notes

- `v-dotnet-as-java` was copied from the unprefixed `~/.claude/skills/dotnet-for-java-devs`; that personal copy is separate from this repo.
- `v-wiki-init` scaffolds an LLM wiki (Karpathy pattern) as an Obsidian vault. Its output is the tree under `skills/v-wiki-init/assets/template/` filled in by `scripts/scaffold.py` (stdlib Python, must run on macOS and Windows). Test it with `python3 scripts/scaffold.py --name X --dest <scratch dir>`; it self-checks wikilinks, JSON and tokens. The Obsidian setup (theme, 16 plugins, settings) is bundled in `assets/obsidian-profile/` (about 18 MB); refresh it with `--snapshot-profile <vault>`. `--obsidian-from <vault>` and `--no-profile` override it. Hidden template files are stored as `dot-*`.
- `v-retro` (manual-only) reviews a session for friction and suggests where fixes should live (CLAUDE.md, memory, permissions, hooks, scripts, skills). `scripts/session_digest.py` (stdlib Python) condenses a transcript from `~/.claude/projects/<project>/<session>.jsonl`; it finds the current session through `CLAUDE_CODE_SESSION_ID`, else the newest transcript for the working directory or its nearest parent, and refuses an ambiguous id prefix. Test it with `python3 scripts/session_digest.py --list`, `python3 scripts/session_digest.py <session-id> --with-text` and `python3 scripts/session_digest.py --recent 10` (friction recurring across sessions).
