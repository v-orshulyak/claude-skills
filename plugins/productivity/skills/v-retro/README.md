# v-retro

A blameless retrospective of a Claude Code session. It finds where the session lost time, tokens or round trips, and suggests a concrete fix for each problem in the place where the next session will actually pick it up. Run it with `/v-retro`. It is manual only, so Claude never starts it by itself.

## What it is

A skill that reviews a session transcript and writes a short report in chat:

- **Outcome and cost**: what was delivered, Claude's working time against wall-clock time, prompts, tool calls, failed calls and tokens.
- **What worked**: one to three things worth repeating.
- **Friction**, ranked by cost × how likely it is to come back: corrections and redirects, failed or silently failed commands, files rewritten across prompts, wide searches before finding the right file, permission prompts, slow calls, confirmation-only round trips.
- **Suggestions**: for each fix, the exact text, rule, JSON or command and where it goes.
- **Next time**: an example opening prompt and the shortest path through the task.

Then it asks which suggestions to apply and can save the report to `retros/<date>-<slug>.md`. It never commits.

The evidence comes from `scripts/session_digest.py` (stdlib Python). It condenses `~/.claude/projects/<project>/<session>.jsonl` into timings, token use by model, failures, rework, repeated calls, permission prompts and a per-prompt timeline. Claude's own memory of the session supplies the *why*; the transcript is the record.

| Argument | Retro of |
|---|---|
| _(none)_ | the current session |
| `<session-id>` or a `.jsonl` path | a past session |
| `recent [N]` | the last N sessions of this project (default 10): what keeps recurring |
| any other text, e.g. `git` or `token use` | the current session, with the report focused on that area |

## What problem it solves

The same friction tends to come back in every session: a shell quirk that fails the first command, a requirement that only comes up after the work is built, a safe command that asks for permission every time, a manual checklist before each push. Each time it costs a few minutes and some tokens, and nobody writes down the fix, because by the end of the session the work is done and the pain is forgotten.

Writing the fix down is not enough either, if it lands in the wrong place. A rule in chat is gone next session; a reminder in `CLAUDE.md` does not help when what is needed is a guarantee. v-retro chooses the lightest mechanism that reliably works for each problem: project or global `CLAUDE.md`, memory, a narrow permission rule, a hook, a script, a change to the skill that caused the friction, or a prompt habit for the user. It checks first what already exists, so it does not suggest a rule that is already there; a rule that exists but was not followed needs a stronger mechanism.

## When to use it

- At the end of a long or bumpy session: many corrections, failed commands, rework or permission prompts.
- After running a skill you maintain, to find out where it asked too late, missed a step or gave a wrong command.
- Every few weeks with `recent`, to find patterns across sessions rather than one-off problems.
- With a focus word when one area clearly hurt ("the test loop", "git").

Not worth running on a short, clean session. If you do, it says the session was clean and gives zero to two suggestions.

## Maintainer notes

Test the digest script directly:

```bash
python3 scripts/session_digest.py --list
python3 scripts/session_digest.py <session-id> --with-text
python3 scripts/session_digest.py --recent 10
```

It finds the current session through `CLAUDE_CODE_SESSION_ID`, otherwise the newest transcript for the working directory or its nearest parent, and refuses an id prefix that matches more than one session. `v-handoff` calls this script through `${CLAUDE_SKILL_DIR}/../v-retro/scripts/session_digest.py`, so moving `v-retro` out of the `productivity` plugin breaks `v-handoff`.
