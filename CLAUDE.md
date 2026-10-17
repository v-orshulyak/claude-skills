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

Current plugins: `productivity` (`v-wiki-init`), `engineering` (`v-dotnet-as-java`), `finances` (empty). Empty plugins keep a `skills/.gitkeep` placeholder.

## Conventions

- **Every skill is prefixed `v-`**, so they are recognisable at a glance. The directory name and the `name:` in `SKILL.md` frontmatter must both be `v-<name>`. Plugin names are *not* prefixed (they are already namespaced by the `v-skills` marketplace, e.g. `engineering@v-skills`).
- Plugins group skills by theme; add a new skill to an existing plugin when it fits, otherwise create a new plugin.
- Adding a plugin means doing **both**: create `plugins/<name>/.claude-plugin/plugin.json` *and* add an entry to `.claude-plugin/marketplace.json` (`source: "./plugins/<name>"`). A plugin missing from the marketplace file is not installable.
- Skills must not hardcode install locations such as `.claude/skills/...`. Reference bundled files relative to the skill, and use `${CLAUDE_SKILL_DIR}` in shell commands.
- Keep SKILL.md `description:` rich in trigger phrases — it is what makes the skill fire.

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

## Notes

- `v-dotnet-as-java` was copied from the unprefixed `~/.claude/skills/dotnet-for-java-devs`; that personal copy is separate from this repo.
- `v-wiki-init` scaffolds an LLM wiki (Karpathy pattern) as an Obsidian vault. Its output is the tree under `skills/v-wiki-init/assets/template/` filled in by `scripts/scaffold.py` (stdlib Python, must run on macOS and Windows). Test it with `python3 scripts/scaffold.py --name X --dest <scratch dir>`; it self-checks wikilinks, JSON and tokens. The Obsidian setup (theme, 16 plugins, settings) is bundled in `assets/obsidian-profile/` (about 18 MB); refresh it with `--snapshot-profile <vault>`. `--obsidian-from <vault>` and `--no-profile` override it. Hidden template files are stored as `dot-*`.
