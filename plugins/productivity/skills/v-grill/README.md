# v-grill

Claude interviews you about a spec, an idea or a personal decision, in rounds of short lettered questions, and keeps a findings doc up to date as you answer. Run it with `/v-grill <topic>`. It is manual only, so Claude never starts it by itself.

## What it is

An interview in rounds. You give a topic: free text, a file path, a link or a ticket key, optionally with a goal ("grill me on the token cache design before I write the story"). Claude then:

1. Names the topic type (**spec / design**, **idea / plan** or **personal decision**), states what "done" means for the grill, and asks where the findings doc goes: a claude.ai Artifact or `grills/<date>-<slug>.md`.
2. Reads what the topic points at (files, spec, ticket, code), so it never asks what it can look up.
3. Asks 3-5 questions per round. Each question is one decision with a bold recommendation and an A/B/C table that says what each option leads to. Numbering continues across rounds, so you can revise any answer later.

You answer in one short line: `Q6: B, Q7: A but default it to false, Q8: skip`, or `yes` to accept every recommendation. `redirect: <focus>` steers the next round and `stop` wraps up. At most one deliberate **Challenge** per round questions an answer that conflicts with an earlier one, a reason that sounds like an assumption, or an unpriced risk.

After every round you get the doc update, a recap of up to four lines and the next round, all in one message. The doc holds the summary, decisions (superseded ones marked), assumptions, open questions, challenges, next steps and a Q&A log. It stands on its own, so someone who was not in the conversation can act on it.

`references/lenses.md` holds the question angles for each topic type (a personal decision gets, for example, a Descartes square). `references/findings-template.md` is the doc layout.

## What problem it solves

A spec or plan written in one go hides what you have not decided yet. Asking Claude to "review" it gives a list of comments, not decisions. A free-form chat about it wanders, asks one thing at a time, and leaves nothing behind except a long transcript.

v-grill makes the decisions explicit and cheap to make. Each question already has a recommendation and its consequences, so most answers take one letter. It checks the premise of each question against the code or material first, so you are not asked to pick between options built on a wrong assumption. And the findings doc means the result survives the chat: a list of agreed decisions and open questions you can turn into a ticket, a spec or a plan.

## When to use it

- **Before writing a spec, story or implementation plan**: to settle scope, acceptance criteria, edge cases and failure modes.
- **On an idea or plan** you are not sure about: to test goals, constraints, risks and the "do nothing" option.
- **On a personal decision** (a job offer, a purchase, a move): to separate what you know from what you assume and get to a clear next step.
- **To continue a grill later**: pass the findings doc (`/v-grill grills/2026-10-01-token-cache.md` or its artifact link) and it carries on from the open questions with the same numbering.

Not the right tool for a quick factual question, or when the decisions are already made and you only need the document written.

## Maintainer notes

There are no scripts. Test it by running `/v-grill <topic>` in a fresh session: once with a file doc, once with an Artifact doc, and once resuming from an existing findings doc. The format follows how the user answered questions in past sessions; the "How this user answers" section of `SKILL.md` lists those constraints, so check a format change against it.
