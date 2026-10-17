---
name: wiki-synthesize
description: Produce an artifact from this LLM wiki into synthesis/ - a report, brief, memo, FAQ, timeline, comparison table, study guide, slide deck, article draft, spreadsheet - built only from wiki pages, citing them, registered in synthesis-index, and regenerated when stale. Use whenever the user asks to "write a brief/report/summary for ...", "make a deck/FAQ/timeline from the wiki", "draft an article about X", "turn what we know about X into ...", "regenerate the stale artifacts", or asks for any deliverable built from the wiki's knowledge rather than a chat answer.
---

# Wiki synthesize

The wiki answers "what do we know?"; `synthesis/` holds things made from that knowledge for a reader. Artifacts are downstream and disposable: they read the wiki, cite it, and get regenerated when the wiki moves on. The wiki never depends on them.

On Windows use `py` or `python` instead of `python3` in the commands below.

## 1. Pin down the request

Only produce an artifact when the user asked for one. Settle, briefly and only what is unclear: the **kind** (brief, report, FAQ, deck ...), the **audience** and its level, **length**, **format** (Markdown by default; Marp-style Markdown for slides; `.pptx` / `.xlsx` / `.docx` / `.html` / `.pdf` when asked), and the **scope** (which topics, which period).

Check `synthesis/synthesis-index.md` first: if an artifact of that kind and topic exists, regenerate it (step 6) rather than creating a second one.

## 2. Gather from the wiki, not from raw/

Read `wiki/index.md`, then the pages in scope (entities, concepts, analyses, source pages; `rg -il "term" wiki` once the wiki is big). Build only from wiki pages: they are the single source of truth, and an artifact that cites `raw/` directly bypasses the provenance and contradiction handling the wiki provides.

If something the artifact needs is missing or thin, say so before writing and offer to ingest a source or research it (the `wiki-research` skill). With the user's OK you can proceed and mark the gap in the artifact rather than filling it from memory.

## 3. Write it

Create `synthesis/<kind>-<topic>.md` (e.g. `brief-board-update.md`; subfolders by kind such as `reports/`, `decks/` once there are many) from `templates/tpl-synthesis.md`, filling every placeholder yourself:

- frontmatter: `type: synthesis`, a human `title:`, `artifact:` (the kind), `audience:`, `generated:` today, `based-on:` listing every wiki page used as quoted wikilinks (`based-on: ["[[page-a]]", "[[page-b]]"]`), `status: draft` until the user is happy.
- body: every factual statement links to the wiki page it came from. Keep open contradictions visible rather than picking a side silently.

Write for the stated audience: an artifact is allowed a voice, structure and selection that wiki pages don't have. It is not allowed facts the wiki doesn't hold.

## 4. Other formats

For `.pptx`, `.xlsx`, `.docx`, `.html` or `.pdf`, produce the file with whatever is available (a document skill, `pandoc`, Marp), save it in `synthesis/` and add a companion note with the same stem (`deck-q3.pptx` + `deck-q3.md`) that carries the frontmatter, a one-paragraph summary, an embed or link to the file (`![[deck-q3.pptx]]`) and the wikilinks to the pages it is based on. The companion note is what the index, lint and staleness checks see.

## 5. New insights go back into the wiki

Synthesising often surfaces a comparison or conclusion that is knowledge, not presentation. Save it as an `analysis` page in `wiki/analyses/` (cited, linked, added to the index) and cite that page from the artifact. Never link from a wiki page to an artifact: the dependency is one-way, and lint flags the reverse.

## 6. Regenerating stale artifacts

An artifact is stale when a page in its `based-on:` was updated after its `generated:` date; lint lists these. Regenerate on request: rebuild from the current wiki pages, keep the file name, update `generated:` and `based-on:`, and tell the user what changed in substance. Don't hand-patch individual sentences: patches drift from the wiki.

## 7. Register and check

- Add or update its line in `synthesis/synthesis-index.md` under `## Artifacts` (remove the "None yet" placeholder line): `- [[artifact-name]] - kind, audience, generated YYYY-MM-DD`.
- Append to `wiki/log.md`: `## [YYYY-MM-DD] synthesize | <artifact title>`, listing the artifact and any analysis pages created.
- Run lint and fix what it reports about the pages you touched:
  ```bash
  python3 "${CLAUDE_SKILL_DIR}/../wiki-lint/scripts/lint.py" --files synthesis/<artifact>.md
  ```
