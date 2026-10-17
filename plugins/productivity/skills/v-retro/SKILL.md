---
name: v-retro
description: Retro of a Claude Code session - friction, cost, and where the fixes should live.
argument-hint: "[session-id | recent [N] | focus]"
disable-model-invocation: true
---

# v-retro

A blameless retrospective of a Claude Code session, written for the **next** time this task (or one like it) comes up. The question is not "what went wrong" but "what would make the next run take fewer round trips, fewer failed commands, less re-discovery and fewer tokens", and where each fix should live so it actually takes effect.

The deliverable is a short, evidence-backed report in chat, followed by an offer to apply the fixes the user picks and, optionally, to save the report as a Markdown file.

## Arguments

`$ARGUMENTS` is optional:

- empty: retro of the current session
- a session id or a `.jsonl` path: retro of that session
- `recent` or `recent N`: a retro across the last N (default 10) sessions of this project, about what keeps recurring rather than about one session
- anything else: a focus for the current session ("git", "the test loop", "token use"). Still scan everything, but spend the report on that area.

Pass the argument to the script only when it is a `.jsonl` path or looks like a session id (hex digits and dashes, at least 8 characters); `recent N` becomes `--recent N`; a focus word never goes to the script. The script refuses an id prefix that matches more than one session and lists the candidates; pick one, or ask the user if the list doesn't make it obvious.

## 1. Gather evidence

Run the digest script. It reads the session transcript (`~/.claude/projects/<project>/<session>.jsonl`) and prints a compact summary: wall-clock and Claude-working time (waits on questions and permission prompts excluded), tokens by model, subagents, tool counts, failed calls with the start and end of their output, *possible silent failures* (a command that "succeeded" while its output shows an error, such as a failing step early in a `;` chain), files changed repeatedly (rework), repeated calls and re-reads, permission prompts, slow calls, and a per-prompt timeline. Prompts that were clicks on an offered button are marked `[button click]`; a click on "Not yet" is an answer, not a correction. Task-list and wrap-up calls are bookkeeping: they are left out of the counts and shown in the timeline as `☰` lines only when they carry a plan or a question.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/session_digest.py"                 # current session
python3 "${CLAUDE_SKILL_DIR}/scripts/session_digest.py" <id> --with-text # a past session
python3 "${CLAUDE_SKILL_DIR}/scripts/session_digest.py" --list           # recent sessions here
python3 "${CLAUDE_SKILL_DIR}/scripts/session_digest.py" --recent 10      # friction recurring across sessions
```

(Use `python` on Windows if `python3` is missing.) The output is already condensed, so read all of it rather than piping through `head`; for a very long session, lower `--max-turns`. `--with-text` adds Claude's own messages to the timeline, which you need for a past session you have no memory of. Failures and Claude's text are never collapsed; runs of successful calls beyond `--max-tools` are. When a session has more prompts than `--max-turns`, the timeline shows only its first and last prompts and says how many it skipped; if the outcome hinges on that middle, rerun with a higher `--max-turns` or grep the transcript for it.

Silent failures are heuristic: output that merely quotes an error (a script printing old logs) can be flagged too, so check the command before calling it friction. Subagent output tokens are under-counted in their transcripts; judge a subagent's cost by its cache reads, tool calls and duration.

The digest is a map, not the whole territory. When a step matters and the digest is ambiguous (why a command failed, what a truncated message decided, what an edit actually changed), grep the raw transcript at the `file:` path it prints for that detail. Don't read the whole file; it can be megabytes.

Then combine two sources:

- **The digest is the record.** Counts, errors, timings and the parts of a long session that were compacted out of your context. When your memory and the transcript disagree, trust the transcript.
- **Your context is the why.** What the user meant, what you were thinking, which assumption turned out wrong. The transcript only shows what happened.

Leave the retro's own turn out of the analysis (the timeline marks it `[retro request]`).

**Recurrence.** Half of the ranking below is "how likely is this to come back". For a session with real friction, run `--recent 10` once: a failure or permission prompt that shows up in several sessions is a stronger case for a fix than one that happened once. For a `recent` retro, this output is the main evidence; open the digest of the sessions it names for detail, and write the report about patterns rather than about any single session.

Before suggesting anything, look at what already exists, so you don't propose a rule that is already written down (that itself is a finding: a rule that exists but was not followed needs a stronger mechanism, not a second copy). Check only what is relevant: the project `CLAUDE.md`, `~/.claude/CLAUDE.md`, the memory index if the session has one, `.claude/settings*.json` permissions and hooks, and the `SKILL.md` of any skill the session used (built-in commands such as `/init` have none). A permission prompt the user answered with "always allow" is usually fixed already; check the settings before suggesting a rule.

## 2. Reconstruct the session

In a few lines for yourself: the goal (or goals), what was delivered, whether it is done, partial or abandoned, and the main phases. Everything else is measured against the goal: a step is friction only if a better path to the same result existed.

## 3. Find the friction

Read the timeline for these signals. Each one usually points to a particular kind of fix:

| Signal in the session | What it usually means | Typical fix |
|---|---|---|
| User corrected or redirected ("wait", "no", "actually", a re-stated requirement) | A requirement or piece of context was missing at the start | CLAUDE.md note or memory; a prompt habit for the user; or the skill in use should ask earlier |
| Failed tool calls or silent failures, especially the same kind more than once | An environment quirk: shell, OS, paths, auth, a tool's flags | A one-line "gotcha" in CLAUDE.md, or a script that does it right |
| The same file rewritten across prompts, or work built and then replaced | A design decision was guessed instead of asked, or a constraint surfaced late | Name the question that should have been asked first, and put it where it will be asked next time (the skill, CLAUDE.md, or the user's opening prompt) |
| Re-reads, wide `find`/`grep` sweeps before reaching the right file | No map of the codebase or of where things live | CLAUDE.md pointers to key files and commands |
| Permission prompts | A safe, recurring command is not allowlisted | A narrow allow rule in `.claude/settings.json` (or `settings.local.json` if personal) |
| A multi-step sequence done by hand that will recur | Procedure lives only in someone's head | A script, a skill, or a checklist in CLAUDE.md |
| Something that had to be remembered every time (validate, format, switch an account back) | An instruction where a guarantee is needed | A hook, so it happens deterministically |
| Long-running calls, huge outputs, one subagent burning most tokens | Work done at the wrong granularity | Narrower commands, background runs, a subagent or a cheaper model for read-only sweeps |
| Many round trips that were only confirmations ("commit and push" after each change) | Standing intent was never stated | A CLAUDE.md line stating the default, or batching requests |
| Questions to the user that the code could have answered, or long waits on the user | Asking instead of deciding | Decide from conventions and say so; ask only real decisions |

Note one to three things that **worked** and are worth repeating (a test loop that caught bugs, a good up-front question). A retro that only lists problems teaches the wrong lesson.

**Find the root cause, not just the symptom.** "The settings were built three times" is a symptom; "nobody asked at the start whether the skill must work on other machines" is the cause, and the cause is what the fix should target. Also ask whether a step can be removed rather than documented: a five-command checklist that runs on every push is better replaced by a script or a one-time setup change than by a better-written checklist.

**Calibrate.** For each friction point, estimate its cost with evidence from the digest (round trips, minutes, tokens, failed calls) and how likely it is to recur. Rank by cost × recurrence and drop trivia. A clean session gets a short retro: say it was clean and give zero to two suggestions. Generic advice ("write clearer prompts", "plan more") is worse than nothing, because it buries the suggestions that matter; every suggestion has to point at something that happened in this session.

## 4. Pick the right home for each fix

A fix only helps if it lands where the next session will see it. Prefer the lightest mechanism that reliably works:

- **Project `CLAUDE.md`**: facts and rules for anyone working in this repo: commands, gotchas, conventions, key paths. Checked in.
- **`~/.claude/CLAUDE.md`**: personal rules that apply across all projects.
- **Memory**: the user's preferences and context that are not facts about the repo (follow the memory rules in the system prompt, if this session has a memory directory).
- **Permissions** in `.claude/settings.json` / `settings.local.json`: to stop recurring prompts for safe commands. Keep patterns narrow.
- **Hooks**: only for things that must happen every time and whose omission has a real cost. A CLAUDE.md line is cheaper when forgetting is harmless.
- **A script** (in the repo or in a skill): a deterministic multi-step sequence that recurs.
- **A skill**, new or existing: a recurring workflow that needs judgment. If the session ran a skill and the friction came from it (it asked too late, missed a step, gave a wrong command), the fix belongs **in that skill**, which is often the highest-value suggestion of all. If the skill is someone else's (an installed plugin you don't maintain), suggest a local override in CLAUDE.md instead, and note what to report to its author.
- **A prompt habit**: what the user could say up front next time, written as an example opening prompt. This is for the user, not for Claude, so say it plainly and without lecturing. Nothing gets written for it, so put it in "Next time" rather than in the numbered suggestions.
- **A change only the user can make** (an SSH key, an account setting, global git config): describe it and say it is theirs to do. Don't put it in the list of things you will apply.

Make every suggestion concrete: the exact line, rule, JSON or command, and the file it goes into. If you propose a command or config you could not try, mark it "(untested)" rather than presenting it as known to work.

## 5. Report

Use this structure. Keep it tight (about 40-60 lines plus the content blocks); the user should be able to read it in two minutes.

```markdown
## Retro: <the session's goal in one line>

**Outcome:** <done | partial | abandoned> - <what was delivered>
**Cost:** ~<Claude working time> of Claude work over <wall clock> · <N> prompts · <N> tool calls · <N> failed (+<N> silent) · <tokens: output and cache reads, by model if more than one>

### What worked
- <one to three items>

### Friction
1. **<short title>**: <what happened, with evidence: time, tool, error> · cost ≈ <round trips / minutes / tokens>
2. ...

### Suggestions
| # | Fix | Where | Effort |
|---|-----|-------|--------|
| 1 | <one line> | <file or mechanism> | <one line / small / medium> |

**1. <title>**: <why, tied to friction #n>
<exact content to add, in a code block>

### Next time
<An example opening prompt that would have avoided the corrections, and the shortest path through the task in 3-6 steps.>

### Loose ends
<Only if any: things the session left unverified or unfinished (never run on Windows, never opened in the app, uncommitted work). Skip the section when there are none.>
```

Write in plain language; the user may skim. Don't quote secrets, tokens or personal data from the transcript into the report (the digest redacts common secret patterns, but check).

## 6. Offer to apply

End by asking which of the numbered suggestions to apply (by number, "all" or "none"), and offer, as a separate option, to save the report as a Markdown file. Suggest `retros/<YYYY-MM-DD>-<slug>.md` under the current directory and accept any path the user gives; mention that the folder can be git-ignored if they don't want retros in the repo. When AskUserQuestion is available and there are at most four suggestions, a multi-select question works well; otherwise ask in chat.

Apply only what the user picks:

- Edit `CLAUDE.md` files inside their existing structure; extend a section rather than adding a near-duplicate.
- Write memories following the memory rules in the system prompt.
- For permissions and hooks, use the `update-config` skill when it is available (it knows the settings format); show the JSON before writing it.
- For a new or substantially changed skill, don't write it inline at the end of a retro: suggest running `/skill-creator` (or a separate session) with a brief taken from the suggestion. Small fixes to an existing skill's `SKILL.md` are fine to make directly.
- Don't commit. Say which files changed; if the user asks to commit, the repo's own commit conventions apply.
