# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal Claude Code plugin marketplace named **`v-skills`**. There is no build step or test suite — the repo is manifests plus Markdown skills.

## Layout

```
.claude-plugin/marketplace.json        # marketplace "v-skills"; lists every plugin by relative source
plugins/<plugin>/.claude-plugin/plugin.json
plugins/<plugin>/skills/<v-skill>/SKILL.md   (+ README.md, optional references/, scripts)
```

Every skill has a `README.md` for humans (what it is, what problem it solves, when to use it, then maintainer notes such as test commands); keep model-facing instructions in `SKILL.md`. The root `README.md` has a table of all skills; update it when adding, renaming or moving a skill.

Current plugins: `productivity` (`v-wiki-init`, `v-retro`, `v-grill`, `v-handoff`), `engineering` (`v-dotnet-as-java`), `finances` (empty). Empty plugins keep a `skills/.gitkeep` placeholder.

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

After editing a skill, `claude plugin marketplace update v-skills` (or reinstall) picks up the change; plugins are copied to a cache on install, and the marketplace refreshes rarely.

To make the current checkout live at once, `python3 scripts/sync_skills.py` (`py` on Windows; `--dry-run`, `--prune`, `--dest DIR`) mirrors every `plugins/*/skills/v-*` folder into `~/.claude/skills`. It is stdlib Python, touches only those folders (and, with `--prune`, stale `v-*` ones), and is meant as an alternative to the plugin install, not an addition (both together list each skill twice). Test it with `--dest <scratch dir>`. It requires every skill folder to start with `v-`; `v-handoff` reads `../v-retro/scripts/` and the flat target layout keeps that working.

## Git identity

**Every commit in this repo must be authored from the personal GitHub account**, whatever identity is set globally:

- user.name `v-orshulyak`, user.email `vladorshulyak@gmail.com`
- The identity is set in this repo's local git config (`git config --local`). If `git config --local user.email` is empty, set both before committing; do not rely on or change the global config.
- Verify before pushing: `git log -1 --format='%an <%ae>'` must print `v-orshulyak <vladorshulyak@gmail.com>`.
- The remote `origin` is `https://github.com/v-orshulyak/claude-skills.git`; push with credentials for the `v-orshulyak` account.
- Never run `gh auth login` yourself (it is interactive and needs the user's browser).
- On a machine that also has other GitHub accounts, `CLAUDE.local.md` (git-ignored, per machine) says how to switch accounts for a push and back. Without that file, assume `v-orshulyak` is the only account and push normally.

## Notes

- `v-dotnet-as-java` was copied from the unprefixed `~/.claude/skills/dotnet-for-java-devs`; that personal copy is separate from this repo.
- `v-wiki-init` scaffolds an LLM wiki (Karpathy pattern) as an Obsidian vault. Its output is the tree under `skills/v-wiki-init/assets/template/` filled in by `scripts/scaffold.py` (stdlib Python, must run on macOS and Windows). The vault ships six skills (`wiki-capture`, `-ingest`, `-lint`, `-refactor`, `-research`, `-synthesize`), a `wiki-source-reader` subagent, a path-scoped `synthesis` rule and hooks (`.claude/hooks/wiki_hooks.py`: `raw/` guard, session brief, Stop bookkeeping check) under `assets/template/dot-claude/`. Test it with `python3 scripts/scaffold.py --name X --dest <scratch dir>`; it self-checks wikilinks, JSON and tokens. The skill's `README.md` has the hook and refactor test recipes. The Obsidian setup (theme, 16 plugins, settings) is bundled in `assets/obsidian-profile/` (about 18 MB); refresh it with `--snapshot-profile <vault>`. `--obsidian-from <vault>` and `--no-profile` override it. Hidden template files are stored as `dot-*`.
- `v-retro` (manual-only) reviews a session for friction and suggests where fixes should live (CLAUDE.md, memory, permissions, hooks, scripts, skills). `scripts/session_digest.py` (stdlib Python) condenses a transcript from `~/.claude/projects/<project>/<session>.jsonl`; it finds the current session through `CLAUDE_CODE_SESSION_ID`, else the newest transcript for the working directory or its nearest parent, and refuses an ambiguous id prefix. Test it with `python3 scripts/session_digest.py --list`, `python3 scripts/session_digest.py <session-id> --with-text` and `python3 scripts/session_digest.py --recent 10` (friction recurring across sessions).
- `v-grill` (manual-only) interviews the user in rounds of 3-5 lettered questions (bold recommendation, A/B/C table, replies like `Q6: B, Q7: A but …` or `yes`) on a spec, idea or personal decision, and keeps a self-contained findings doc updated after every round, either as a claude.ai Artifact (a published `.md`) or `grills/<date>-<slug>.md`. Each reply gets the doc update, a short recap and the next round in one message (no separate `go`); passing an existing findings doc as the argument resumes that grill. Its format follows how the user answered questions in past sessions; `references/lenses.md` holds the question angles per topic type and `references/findings-template.md` the doc layout. No scripts; test it by running `/v-grill <topic>` in a fresh session.
- `v-handoff` (manual-only) writes a new handoff file per run (goal, state, decisions, verified/assumed findings with evidence, dead ends, next steps) to `~/.claude/handoffs/<project>/<date>-<HHmm>-<slug>.md`, or `<repo>/handoffs/` with the `repo` argument; it also hands off a past session by id. `/v-handoff list [--all]` lists saved handoffs and `/v-handoff load <id>` (file name, prefix or slug word) resumes one with a drift check against git. `scripts/handoffs.py` (stdlib) does `list`, `find` and `path`; for compacted or past sessions the skill runs `${CLAUDE_SKILL_DIR}/../v-retro/scripts/session_digest.py`, so moving `v-retro` out of `productivity` breaks that path. Test the script with `HOME=<scratch dir> python3 scripts/handoffs.py list --all` (and `find`, `path`) so nothing lands in the real `~/.claude/handoffs`; test the skill with a subagent running `/v-handoff <past-session-id>` into a scratch folder, then loading the result.
