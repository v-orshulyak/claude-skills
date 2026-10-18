# v-handoff

Saves a session's working knowledge to a Markdown handoff file, so a fresh session, a teammate or you next week can pick up the work without the chat. It also lists saved handoffs and loads one to resume. Run it with `/v-handoff`. It is manual only, so Claude never starts it by itself.

## What it is

A skill that writes, lists and loads handoffs:

| Command | Does |
|---|---|
| `/v-handoff [focus]` | Writes a new handoff for the current session, optionally limited to one focus ("only the auth bug") |
| `/v-handoff <session-id>` | Writes a handoff for a past session from its transcript |
| `/v-handoff repo ...` | Writes into `<repo>/handoffs/` instead of the global folder, so teammates can read it |
| `/v-handoff list [--all]` | Lists saved handoffs for this project (or all projects), newest first |
| `/v-handoff load <id>` | Loads a handoff by file name, prefix or a word from its slug, checks it against git and starts the first next step |

A handoff records what git does not:

- **Goal** and definition of done.
- **State**: branch, commit, uncommitted files, unpushed commits, stashes, PR and ticket links.
- **Decisions** with the reason and the alternative that lost.
- **Findings**, each with evidence (`file:line`, a command and its output, a link) and marked *verified* or *assumed*.
- **Dead ends**, **open questions**, **gotchas** and ordered **next steps**, the first one startable cold.

By default files go to `~/.claude/handoffs/<project>/<date>-<HHmm>-<slug>.md`, which keeps work repositories clean and survives a deleted worktree. Every run writes a new file; a handoff started from another one links back to it in `previous:`, so they form a chain. Nothing is committed.

`scripts/handoffs.py` (stdlib Python) does the file work: `list`, `find <id>` and `path <slug>`. For a compacted or past session, the skill reads the transcript with `v-retro`'s `session_digest.py`.

When loading, it compares the handoff with the live repository and reports drift (another branch, new commits, uncommitted changes that are not in the file, files that no longer exist) before doing anything.

## What problem it solves

When a session ends, most of what it learned is lost. Commits and diffs show *what* changed, but not why a design was chosen, which approach was tried and failed, which fact took an hour to find, or exactly where the work stopped. The next session spends its first half hour rediscovering that, or repeats the same dead end.

`claude --resume` reopens the full conversation, but only on the same machine, and a long or compacted chat is a poor way to find the three facts that matter. A handoff is short (30-120 lines), stands on its own, can be read by a person, and works across machines, worktrees and teammates.

It is deliberately not a recap of the conversation. Every item has to pass one test: would the next session lose time without it?

## When to use it

- At the end of a session whose work is not finished.
- Before a worktree or branch is deleted, or before switching to other work for a while.
- When handing work to a teammate (use `repo`, so the file is in the repository).
- After a long session that got compacted, to get the early decisions back on record.
- For a past session you want to continue, by passing its session id.
- At the start of the next session: `/v-handoff list`, then `/v-handoff load <id>`.

Not needed when the work is done and the commit messages already explain it. It also does not replace `CLAUDE.md` or memory: when finishing, it points out findings that are true of the project rather than the task and offers to move them there.

## Maintainer notes

Test the script with a scratch home, so nothing lands in the real `~/.claude/handoffs`:

```bash
HOME=<scratch dir> python3 scripts/handoffs.py list --all
HOME=<scratch dir> python3 scripts/handoffs.py path test-slug
HOME=<scratch dir> python3 scripts/handoffs.py find test
```

Test the skill with a subagent that runs `/v-handoff <past-session-id>` into a scratch folder, then load the result. The skill depends on `${CLAUDE_SKILL_DIR}/../v-retro/scripts/session_digest.py`, so `v-retro` must stay in the same plugin.
