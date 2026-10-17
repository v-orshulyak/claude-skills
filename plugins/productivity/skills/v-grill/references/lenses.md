# Lenses

Angles to draw questions from, per topic type. Pick the ones that are uncertain and costly to get wrong; skip what research already settled. Most topics need only half of a list.

## Spec / design

- **Goal and users**: who uses it, what problem goes away, how we'll know it worked.
- **Scope**: what is in, what is explicitly out, what is deferred to a later story.
- **Data and contracts**: inputs, outputs, API shape, persistence, ownership of each piece of data.
- **Behaviour at the edges**: empty, duplicate, concurrent, partial failure, retries, timeouts, very large input.
- **Errors**: what the caller sees, what gets logged, what is retried, what is fatal.
- **Security and auth**: who may call it, which identity it runs as, tokens and secrets, tenant/account boundaries.
- **Compatibility and migration**: existing callers, old data, feature flags, rollback.
- **Testing and acceptance criteria**: which cases prove it works; what a reviewer would check.
- **Rollout and operations**: environments, config, observability, who gets paged.
- **Alternatives**: the simplest version that would do; what was rejected and why.

## Idea / plan

- **Problem**: who has it, how painful, how they cope today.
- **Why now**: what changed; what happens if it waits six months.
- **Smallest test**: the cheapest way to learn whether it's worth doing.
- **Success**: one measurable signal, and by when.
- **Cost**: time, money, attention; what gets dropped to make room.
- **Risks and kill criteria**: what would make you stop, decided in advance.
- **Alternatives**: existing tools, a smaller variant, someone else doing it.
- **Sequencing**: first three steps; what is blocked on what.

## Personal decision

- **What's really being optimised**: money, time, stress, growth, family, optionality. Rank them.
- **Options**: always include "do nothing" and "wait"; look for a hybrid.
- **Descartes square** (for a yes/no choice between doing X and not doing it): four cells, what I gain and what I lose if I do it, and what I gain and what I lose if I don't. The cell people skip is *what I lose if I don't* (lost momentum, time and money already invested, a goal left unmet), so ask it directly. Then pair items that mirror each other across cells ("I'm an expert now" vs "I'd be a beginner again", "more free time" vs "evenings spent learning") and ask which side of each pair weighs more; cross out the weaker side. What's left points to the answer.
- **Reversibility**: how hard and costly it is to undo each option.
- **Costs**: up front, ongoing, hidden (time, maintenance, regret).
- **Worst case**: for each option, and whether it is survivable.
- **Deadline**: real or self-imposed; what forces the decision.
- **Information**: what new fact would change the answer, and whether it can be got cheaply first.
- **Gut check**: which option they'd be relieved to hear was picked for them.
