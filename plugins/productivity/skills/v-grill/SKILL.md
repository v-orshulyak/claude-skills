---
name: v-grill
description: Grill me on a spec, idea or decision in rounds of lettered questions, keeping a findings doc up to date.
argument-hint: "[topic | path | link | ticket | findings doc to resume]"
disable-model-invocation: true
---

# v-grill

An interview in rounds. Claude asks, the user answers, and every round sharpens a topic: a feature or design spec, an idea or plan, or a personal decision. The point is to surface what the user has not decided yet, test the reasons behind what they have, and leave a findings doc that someone who was not in the conversation could act on.

The deliverable is that findings doc, updated after every round, plus the rounds themselves in chat.

## How this user answers (design constraints)

These come from how the user actually answered questions in past sessions. Follow them; they are why the format below looks the way it does.

- They answer fastest with letters: `A`, `Q3: B`, `Q1: B, Q2: A`, `yes`. They often add a change: `B but default it to false`. Record the change, not just the letter.
- They accept a well-argued recommendation, but when an option rests on a wrong premise they replace it with free text. So check the premise (step 2) before asking; a question built on a wrong assumption wastes a round.
- A side request tucked into a question ("…and tell me the ticket key") gets ignored. One decision per question.
- Jargon and vague wording get "what do you mean?". Use plain words and say what each option leads to.
- They revise earlier answers later. That is normal, not friction; supersede the old decision.
- Messages are short and may have typos. Read intent, don't ask them to rephrase.
- Every extra turn costs them attention, so a round never needs a separate "go" to start.
- They want output that stands on its own, and they decide when anything is committed.

## Arguments

`$ARGUMENTS` is the topic: free text, a file path, a link or a ticket key, optionally with a goal ("grill me on the token cache design before I write the story"). When it is empty, ask for the topic in one line and do nothing else.

**Resuming.** If the argument is an existing findings doc (a `grills/*.md` file, or a claude.ai artifact link to one), continue that grill instead of starting over: read it (an artifact with the `Artifact` tool's `read` action), keep its location, carry on the round and Q numbering, and build the next round from its Open questions and Next steps. Skip the setup message: say in one line what you are resuming, then go straight to research (if anything changed) and the next round.

## 1. Setup: one short message, then wait

Before any research or tool call, send one message that:

1. Names the topic and the type you infer: **spec / design**, **idea / plan** or **personal decision**. The type picks the lens (step 3).
2. States the goal of the grill in one line ("done = an agreed scope and AC list ready for a Jira story"), so the user can correct it.
3. Asks where the findings doc goes, in the same lettered format the rounds use, with a recommendation (the file if the directory already has a `grills/` folder, otherwise whichever fits the topic):
   - **A) Claude Artifact**: a private page on claude.ai, republished after every round so the link stays the same. Offer this only when the session has an `Artifact` tool; otherwise say the doc will be a file and skip the question.
   - **B) File in the current directory**: `grills/<YYYY-MM-DD>-<slug>.md` (any path the user gives is fine; mention the folder can be git-ignored).

   If the arguments already say where the doc goes, skip this question.

End the turn there and wait for the reply. The user can correct the type or goal in the same reply (`B, and it's a decision, not a spec`).

**Artifact output.** Load the `artifact-design` skill before the first publish. Write the doc as `<slug>.md` in the scratchpad directory (or the working directory if there is no scratchpad) and publish that file with the Artifact tool. This skill explicitly asks for a Markdown artifact, so publish the `.md` itself rather than building an HTML page, and use the Artifact tool even if a docs connector is attached: the user picked a page they can reopen by link. Pass a short `icon` (for example `question`) on the first publish only. After each round, edit the same file and publish the same path again so the URL does not change. Give the user the link once, after the first publish.

## 2. Research before asking

Read what the topic points at before the first round: the referenced files, docs, spec or ticket; for a spec, the relevant code (use an Explore subagent for a wide sweep). For an idea or a decision, read whatever material the user named and nothing more.

- Never ask what you can look up. If the code already decides something, state it as a fact in the round's preamble ("the API already returns 409 on duplicates, so I'm not asking about that").
- If research contradicts something the user said, that is the first challenge of round 1.
- Keep the research short and proportional; a personal decision usually needs none.

## 3. Rounds

Read `references/lenses.md` (next to this file) for the angles to draw questions from for the topic type. Don't walk the list in order; pick what is most uncertain and most costly to get wrong.

**Shape of a round.** 3 to 5 questions. Round 1 is broad: goal, constraints, success criteria, non-goals. Later rounds go deeper: edge cases, failure modes, trade-offs, sequencing, and whatever the previous answers opened up. Put the highest-impact question first.

**Numbering continues across rounds** (round 2 starts at Q6 if round 1 ended at Q5), so any answer can be referred to later.

**Each question**:

```markdown
**Q6. <one decision, in plain words>**
<one line of context only if needed: what it affects, or a fact found in research>
Recommended: **B**. <why, in one or two sentences>

| | Option | What it leads to |
|---|---|---|
| A | <option> | <consequence> |
| B | <option> | <consequence> |
| C | <option> | <consequence> |
```

- Two to four options. Make them genuinely different; drop an option nobody would pick.
- Always give a recommendation and commit to it. If you truly can't recommend, say what information would decide it.
- For an open question where options would be fake ("what does success look like in 3 months?"), ask it plainly and offer an example answer instead of a table. Keep these to at most one per round.

**End each round with**:

```markdown
Reply like `Q6: B, Q7: A but …, Q8: skip`, or `yes` to take every recommendation. Free text is fine; `redirect: <focus>` or `stop` also work.
```

**Rounds live in the message text.** Don't move questions into a question tool (AskUserQuestion) or an end-of-turn button box: those can't show the recommendation and table, cap the number of questions, and can't take a `B but …` answer. If the host requires an end-of-turn summary call, give it a recap only, with no question, so the round stays the last thing the user reads.

**Grilling.** At most one deliberate challenge per round, clearly marked (`Challenge:`). Use it where it counts: an answer that conflicts with an earlier one or with a fact from research, a reason that sounds like an assumption, a risk the user hasn't priced in, the "do nothing" option for a decision. Be direct, not adversarial; if the user holds their ground with a reason, record it and move on.

Never put a side request inside a question. If you need something else from the user (a ticket key, a file), ask it as its own line after the round, or look it up.

## 4. Reading answers

- `yes` or `ok`: every recommendation in this round is accepted.
- A letter: that option. A letter plus text: that option with the change; write the change into the decision.
- Free text that replaces the options: that is the decision, and often a sign the premise was off; note what was wrong.
- `skip`, `later`, `not sure`, or no answer for a question: it goes to **Open questions**.
- An answer that changes an earlier decision ("actually Q2 should be A"): update it and mark the old one superseded. Check whether later decisions depended on it and raise any knock-on in the next round.
- `redirect: <focus>` (or any message that steers instead of answering): record whatever answers it contains, then build the next round around the new focus. Unanswered questions from this round go to Open questions. A new topic altogether becomes a new section of the same doc unless the user says otherwise.
- `stop` or `done`: record any answers in the same message, then wrap up (step 6).
- If an answer is ambiguous, don't stop to ask; make it a question in the next round.
- "What do you mean?" about a question: explain it in plain terms with a concrete example, then wait for the answer before starting the next round.

## 5. After each round: update, recap, next round in one message

1. Update the findings doc using `references/findings-template.md` (next to this file): decisions, assumptions, open questions, challenges, next steps, and the round's Q&A log. Rewrite the Summary so it reflects the current state, not a history. Republish if it is an artifact.
2. Reply with a recap of at most four lines: what was settled, what is still open overall, anything superseded or contradicting, and the doc's path or link the first time.
3. In the same message, ask the next round, opening with its focus in one line. Then wait.

**Know when to stop.** Most grills settle in three to five rounds. When a round comes back as mostly `yes`, or what is left is small or can't be decided yet, don't invent another round: suggest stopping in the recap and ask only the one or two questions that still matter, or none.

## 6. Wrap up

On `stop` or `done`, or once the user agrees nothing material is still open:

1. Finalise the doc: Summary rewritten as the outcome, Next steps as concrete actions with an owner where it matters, status set to `done`, open questions left honestly open.
2. Tell the user where it lives (path or link) in one line, with a two-line outcome.
3. Offer follow-ups without doing them: commit the file, turn it into a Jira story / spec / implementation plan, or grill the open questions later with `/v-grill <path or link>`.

Don't commit on your own; the user decides. Never write a doc that refers to other local Markdown files for its meaning; it has to stand on its own.
