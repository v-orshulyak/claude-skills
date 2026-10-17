# Findings doc template

Fill this in after round 1 and keep it current after every round. The doc must stand on its own: no links to other local Markdown files, no "see above in chat". Leave a section out until it has content, except Summary, Decisions and Open questions.

```markdown
# Grill: <topic>

<YYYY-MM-DD> · <spec / design | idea / plan | personal decision> · rounds: <N> · status: <in progress | done>

**Goal:** <what "done" means for this grill, in one line>

## Summary

<3-5 lines describing the current state: what is decided, what the main open risk is. Rewrite it every round; it is not a history.>

## Decisions

| # | Question | Decision | Why | Round |
|---|---|---|---|---|
| Q1 | <question, short> | <decision, including any change the user added to the option> | <the reason given or the accepted recommendation> | 1 |
| ~~Q2~~ | ~~<question>~~ | ~~<old decision>~~ | superseded by Q9 | 1 |

## Descartes square

<Only for a yes/no personal decision. Fill the cells as answers come in. Rank each cell by importance as the user tells you. In the last round, cross out the weaker side of each mirror pair (~~like this~~) so only the items that decide it remain.>

| | If I do it | If I don't |
|---|---|---|
| **Gain** | <item> | <item> |
| **Lose** | <item> | <item> |

**Pairs weighed:** <item> vs <item> → <the one that matters more> (Q7)

## Assumptions and constraints

- <a fact from research, or something the user stated as given>

## Open questions

- **Q4** <question>: <why it is still open, and what would settle it>

## Challenges raised

- <the challenge> → <how it was resolved, or that the user held their position and why>

## Next steps

- [ ] <concrete action> (<owner, if it matters>)

## Q&A log

### Round 1

- **Q1. <question>** Recommended B. Answer: `<the user's reply, verbatim>`
- ...
```
