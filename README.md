# v-skills

A personal Claude Code plugin marketplace. Skills are grouped into plugins by theme, and every skill name starts with `v-` so it is easy to recognise.

## Install

```bash
claude plugin marketplace add v-orshulyak/claude-skills   # or a local path to this checkout
claude plugin install productivity@v-skills
claude plugin install engineering@v-skills
```

Plugins are copied to a cache on install. After the repo changes, run `claude plugin marketplace update v-skills` to pick up the new version.

### Or copy the skills straight into `~/.claude/skills`

The marketplace cache refreshes rarely. To use the current checkout right away, mirror every skill into your personal skills folder (they then load in every project, no install step):

```bash
python3 scripts/sync_skills.py --dry-run   # preview
python3 scripts/sync_skills.py             # copy new and changed files, remove files the repo dropped
python3 scripts/sync_skills.py --prune     # also remove v-* skills deleted from the repo
```

On Windows use `py` instead of `python3`. Run it after each change you want live, and start a new Claude Code session to pick it up. Skills show up as `/v-grill` rather than `/productivity:v-grill`. Use either this or the plugin install, not both, or each skill is listed twice. Folders that are not `v-*` skills from this repo are never touched.

## Skills

| Plugin | Skill | What it does | Runs |
|---|---|---|---|
| `productivity` | [`v-wiki-init`](plugins/productivity/skills/v-wiki-init/README.md) | Scaffolds an LLM-maintained wiki (Karpathy's "LLM Wiki" pattern) as an Obsidian vault, with workflows, hooks and your Obsidian setup | `/v-wiki-init` |
| `productivity` | [`v-retro`](plugins/productivity/skills/v-retro/README.md) | Retrospective of a session: friction, cost, and where each fix should live (CLAUDE.md, memory, permissions, hooks, scripts, skills) | `/v-retro` |
| `productivity` | [`v-grill`](plugins/productivity/skills/v-grill/README.md) | Interviews you on a spec, idea or decision in rounds of lettered questions and keeps a findings doc | `/v-grill <topic>` |
| `productivity` | [`v-handoff`](plugins/productivity/skills/v-handoff/README.md) | Saves a session as a handoff file (state, decisions, findings, next steps), lists handoffs and loads one to resume | `/v-handoff` |
| `engineering` | [`v-dotnet-as-java`](plugins/engineering/skills/v-dotnet-as-java/README.md) | Explains .NET and C# to a Java/Spring developer through analogies, and flags where they break | automatically on .NET work |
| `finances` | _none yet_ | | |

Each skill's README explains what it is, what problem it solves and when to use it. The `productivity` skills run only when you type the slash command.

## Layout

```
.claude-plugin/marketplace.json                  # the "v-skills" marketplace; lists every plugin
plugins/<plugin>/.claude-plugin/plugin.json
plugins/<plugin>/skills/<v-skill>/SKILL.md       # what Claude reads when the skill runs
plugins/<plugin>/skills/<v-skill>/README.md      # what it is, when to use it, maintainer notes
scripts/sync_skills.py                           # mirrors all skills into ~/.claude/skills
```

Validate the manifests with `claude plugin validate .` (marketplace) and `claude plugin validate plugins/<plugin>` (one plugin).
