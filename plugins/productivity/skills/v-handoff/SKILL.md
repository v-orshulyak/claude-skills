---
name: v-handoff
description: Save this session as a handoff Markdown file (state, decisions, findings, next steps), list saved handoffs, or load one to pick up the work.
argument-hint: "[repo] [focus | session-id] | list [--all] | load <id>"
disable-model-invocation: true
---

# v-handoff

Writes a handoff: a Markdown file that lets a fresh session, a teammate or the user next week pick up this work without the chat. It records what the session knows that git does not: why things were decided, what was learned, what failed, and exactly where the work stopped.

It is not a recap of the conversation. Commits, diffs and PRs already say *what* changed; a handoff that retells them is noise. Spend the words on the things that would otherwise cost the next session time to rediscover.

Usually run once, at the end of a session. Every run writes a **new** file; old handoffs are never edited. The same skill lists saved handoffs and loads one at the start of the next session.

The bundled script finds and places handoff files; run it rather than globbing folders by hand:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/handoffs.py" list [--all] [--limit N]
python3 "${CLAUDE_SKILL_DIR}/scripts/handoffs.py" find <id>
python3 "${CLAUDE_SKILL_DIR}/scripts/handoffs.py" path <slug> [--repo]
```

(Use `python` on Windows if `python3` is missing.)

## Arguments

`$ARGUMENTS` is optional. The first word decides the mode:

- `list` (optionally `--all`, `--limit N`): see "Listing".
- `load <id>`: see "Loading". `<id>` is a handoff's file name without `.md`, any unique prefix of it, or a word from its slug or goal (`load v-retro`). A path to a handoff file works too, with or without `load`.
- anything else writes a handoff. `repo` comes first when present; the rest can be a session id, a focus, or both (`repo 8215cc15 auth bug only`):

- empty: hand off the current session to the global folder (below).
- `repo` as the first word: write into the repository instead (below).
- a session id (hex digits and dashes, at least 8 characters) or a `.jsonl` path: hand off that past session instead of this one.
- anything else: a focus ("only the auth bug, skip the docs detour"). Cover everything still relevant to it, and leave the rest out.

## Where the file goes

- **Default, global:** `~/.claude/handoffs/<project>/<YYYY-MM-DD>-<HHmm>-<slug>.md`. This keeps work repositories clean, and the file survives a deleted worktree. `<project>` is the basename of the main repository (`git rev-parse --path-format=absolute --git-common-dir`, then its parent folder, so every worktree of one repo shares a folder), or the working directory's basename outside git.
- **`repo`:** `<repository root>/handoffs/<YYYY-MM-DD>-<HHmm>-<slug>.md`. Teammates can read it. Mention once that the folder can be git-ignored, and don't commit it; the user decides.
- A path given by the user wins over both.

`<HHmm>` is the local time, so two handoffs on one day don't collide. `<slug>` is the goal in two to five kebab-case words (`token-cache-refresh`). Get the full path from `handoffs.py path <slug>` (add `--repo` for the repository folder): it works out the project, creates the folder, and never returns a path that already exists.

## 1. Gather

**Your own context is the main source.** You know what was asked, what you tried and why. Two cases need the transcript as well:

- **The session was compacted** (your context starts with a summary of earlier conversation), so early decisions and dead ends may be gone from memory.
- **A past session** was given as the argument.

For these, run the digest script from the sibling `v-retro` skill, which condenses `~/.claude/projects/<project>/<session>.jsonl` into a timeline with failed calls and changed files:

```bash
python3 "${CLAUDE_SKILL_DIR}/../v-retro/scripts/session_digest.py" --with-text              # current session
python3 "${CLAUDE_SKILL_DIR}/../v-retro/scripts/session_digest.py" <session-id> --with-text # a past session
```

(Use `python` on Windows if `python3` is missing.) If the script is not there, say so in one line and work from context. The digest truncates long messages, subagent prompts and the user's answers to questions, and for a past session those often hold the decisions. So when something matters and the digest is cut short, grep or parse the raw transcript at the `file:` path it prints for that detail; don't read the whole file, it can be megabytes.

**Then the live state**, in one shell call, from the working directory (skip the git parts outside a repository):

```bash
git rev-parse --abbrev-ref HEAD; git log -1 --format='%h %s'; git status --short; git log --oneline @{u}..HEAD 2>/dev/null; git stash list
```

Uncommitted changes, unpushed commits and stashes matter most here: they are exactly what gets lost between sessions. If some of them belong to other work, list them anyway but label them as not part of this handoff.

**For a past session**, the git state now is not the state the session ended in. Describe the session's end in State (from the digest), then find what happened since: `git log --oneline --since='<session end>'`, plus `git log --oneline -- <files it changed>` to see whether its uncommitted work was committed later. Add that as a "Since then" line in State. The frontmatter `branch` and `commit` are always the live values at the time of writing, because resuming compares against them. Also note any PR, ticket, artifact or doc link the session produced or used, and the session id (`$CLAUDE_CODE_SESSION_ID`, or the id from the digest).

## 2. Decide what goes in

Ask of every candidate item: *would the next session lose time without it?* Keep it if yes.

- **Decisions** are choices made, each with its *why* and the alternative that lost. These are the most valuable part, because the code shows the result but never the reason.
- **Findings** are facts learned about the system, the data or the problem that took effort to discover ("the token refresh happens in `AuthMiddleware.cs:88`, not in the client"; "the flaky test is a timezone bug, not a race"). Give each one its evidence (`file:line`, a command and what it printed, a link), and mark it **verified** (you saw it) or **assumed** (inferred, not checked). A finding with no evidence turns into folklore.
- **Dead ends** are approaches that were tried and did not work, with the reason, so nobody tries them again.
- **Open questions** are things still undecided or unknown, and who or what would settle them.
- **Next steps** are concrete and in order. The first one should be startable cold: the file to open or the command to run.
- **Gotchas** are environment traps hit along the way (an auth quirk, a command that needs a flag, a test that must run alone).

Leave out the play-by-play, things already obvious from the diff or commit messages, tool chatter, and anything resolved that has no lasting lesson. Never copy secrets, tokens, passwords or personal data into the file; name the secret ("the staging API key from 1Password") instead.

**Previous handoff.** If this session started from a handoff (it was loaded with this skill, or the user pointed you at a handoff file), put its path in `previous:` so handoffs form a chain. Don't edit that older file.

## 3. Write

Use this layout. Leave out any section with nothing in it, except Goal, State and Next steps, so a short session gives a short file. Aim for 30-120 lines; a long session earns more Findings and Decisions, not more narrative. The file must stand on its own: no "as discussed above", no references to the chat.

```markdown
---
type: handoff
date: <YYYY-MM-DD HH:mm, when this handoff was written>
project: <project>
cwd: <absolute working directory>
branch: <branch>
commit: <short sha>
session: <session id>
status: <in progress | blocked | done>
previous: <path of the handoff this session started from, or omit>
---

# Handoff: <the goal in one line>

## Goal

<What we are trying to achieve and why, in two to four lines. Include the definition of done if it was stated.>

## State

<Where things stand right now, in a few lines: what is done, what is half-done, and what is broken.>

- **Branch / commit:** `<branch>` at `<sha> <subject>`
- **Uncommitted:** <files from git status, or "none">
- **Unpushed / stashed:** <commits or stashes, or omit>
- **Links:** <PR, ticket, artifact, doc>

## Decisions

| Decision | Why | Rejected alternative |
|---|---|---|
| <what was chosen> | <the reason> | <what lost, and why> |

## Findings

- **<the fact, stated plainly>** (verified): <evidence: `path:line`, a command and its output, or a link>
- **<the fact>** (assumed): <why it is believed, and how to check it>

## Dead ends

- <what was tried>: <why it did not work>

## Open questions

- <question>: <what would settle it, and who decides>

## Gotchas

- <the trap, and how to avoid it>

## Next steps

1. <first step, startable cold: the file, command or decision>
2. <...>

<When status is done, list only real follow-ups (verification never done, a release step), or write "None.">

## Resume

Start a new session in `<cwd>` and run `/v-handoff load <this file's id, the file name without .md>`, or `claude --resume <session id>` to reopen the full conversation on this machine.
```

## 4. Finish

Tell the user in at most four lines:

1. The file's path, as a link if the host renders file links.
2. The status and the first next step.
3. Anything at risk: uncommitted changes, unpushed commits, or a worktree that will be deleted. Say it plainly; this is the point of a handoff.
4. **Worth keeping permanently**, if any: findings or gotchas that are true of the project rather than this task (a build quirk, where config lives). These belong in the project's `CLAUDE.md` or in memory, where every future session sees them. Check first that they are not already written there, then offer to add the rest, naming each one; don't add them unasked.

Don't commit anything.

## Listing

Run `handoffs.py list` (pass `--all` and `--limit` through). It prints one line per handoff, newest first: id, project (with `--all`), status, branch, where it lives (`global` or `repo`) and the goal. Show that as a short table, and end with one line on how to load one (`/v-handoff load <id>`). Don't open the files. If there are none, say where the script looked.

## Loading

Resolve the id with `handoffs.py find <id>`. It checks this project first, then every project. Exit 1 means nothing matched: say so and offer `list --all`. Exit 2 means several matched, and it prints the candidates: show them and ask which one, with no guessing. With one match, continue with the path it printed.

1. Read it. If `previous:` is set and the Goal or Decisions refer to something you can't follow without it, read that one too, but no further back.
2. Compare it with the live state: run the git command from step 1 and `git log --oneline <commit>..HEAD` in the handoff's `cwd` (say so if the session is in a different directory). Note any drift: a different branch, new commits since, uncommitted changes that are not in the file, or files named in State and Next steps that no longer exist. Uncommitted work the handoff already lists is not drift.
3. Reply in at most eight lines: the goal, the state, anything that drifted, the open questions that block the next step, and the first next step.
4. If the first next step is unambiguous and only reads or edits files in the project, start it. Ask first if it needs a decision or an open question answered, changes tool or machine state (installing, updating plugins, config), is outward-facing (push, deploy, sending a message), or has to happen in another session. When `status` is `done`, there is nothing to resume: list the follow-ups and ask which, if any, to do.

Remember the path: if this session later runs `/v-handoff`, it goes into `previous:`.
