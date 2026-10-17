---
name: wiki-research
description: Find new sources to fill the gaps in this LLM wiki - collect open questions, Gaps, thin draft pages and lint suggestions, search the web for credible sources, present a shortlist with what each would fill, and capture the chosen ones into raw/ for ingest. Use whenever the user says "research X for the wiki", "find sources on ...", "fill the gaps", "what's missing and where can we find it", "look for newer/better sources", "follow up on the open questions", or after a lint pass suggests sources worth finding.
---

# Wiki research

Research feeds the wiki through the front door: knowledge only enters as a captured source in `raw/` followed by an ingest, so every claim stays traceable. Search results and snippets are leads, never wiki content.

On Windows use `py` or `python` instead of `python3` in the commands below.

## 1. Collect the questions

Start from what the user asked. If they asked generally ("fill the gaps"), gather the wiki's own to-do list:

- the `## Gaps` and `## Open questions` sections of `wiki/overview.md`;
- "Open questions" on source pages, `status: draft` pages that are thin, and `status: stale` pages;
- the script's starting points: `python3 "${CLAUDE_SKILL_DIR}/../wiki-lint/scripts/lint.py"` (unresolved links recorded under Gaps, stale pages).

Turn them into 3-5 concrete research questions and confirm them with the user before searching; this is where the user steers depth and direction.

## 2. Search

For each question, run a few targeted web searches. Prefer primary and durable sources (papers, official documentation, standards, datasets, filings, first-hand reports) over aggregators and SEO pages; note date and author, and check whether a newer version exists. Read a candidate far enough to know what it would actually contribute. Check what the wiki already holds (`rg -il "<term>" wiki raw`) so you don't propose sources that are already captured.

## 3. Shortlist

Present one compact list: per candidate the title, author/publisher, date, link, which question or gap it fills, and why it is credible. Mark anything paywalled. Flag candidates that would contradict current wiki claims; those are valuable, not a reason to drop them. Don't write anything to the vault yet.

## 4. Capture and ingest what the user picks

Use the `wiki-capture` skill for each chosen source (it names, saves and logs it in `raw/`), then offer a batch ingest with `wiki-ingest`. Questions the search could not answer go under `## Gaps` or `## Open questions` in `wiki/overview.md` with a note of what was tried, so the next round starts from there.
