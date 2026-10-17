---
name: wiki-ingest
description: Ingest a source into this LLM wiki. Read a file from raw/ (PDF, paper, article, web clipping, transcript, meeting notes, export), write its wiki/sources summary page, update or create the entity and concept pages it touches with cited claims, flag contradictions, and update index, overview and log. Use whenever the user says "ingest raw/x.pdf", "add this paper/article to the wiki", "process the new files in raw/", "file this source", "I dropped something in raw", or pastes a URL or text they want in the wiki (capture it first with wiki-capture), even if they never say "ingest".
---

# Wiki ingest

Ingest is how knowledge enters the wiki: one source is read once, carefully, and its content is filed into the pages it belongs to, so later questions are answered from the wiki rather than by re-reading originals. A good ingest leaves every claim cited, every new page linked in and out, and the index, overview and log current.

`${CLAUDE_SKILL_DIR}` below is this skill's folder (`.claude/skills/wiki-ingest` in the vault). The helper commands use the lint script from the sibling `wiki-lint` skill. On Windows use `py` or `python` instead of `python3`. Agents without skill support can run the same paths directly.

## 1. Find the source

- Sources live in `raw/`, the human's immutable layer. If the user gives a URL, pasted text or a file elsewhere, save it into `raw/` first with the `wiki-capture` skill, because every source page must point at an original that stays put.
- For "ingest the new files", list what no source page covers yet:
  ```bash
  python3 "${CLAUDE_SKILL_DIR}/../wiki-lint/scripts/lint.py" --new-sources
  ```
- If a source page already links this raw file in `raw:`, it is a re-ingest: say so and ask whether to update that page instead of creating a second one.

## 2. Read it in full and agree on emphasis

Read the whole source; `TOOLS.md` covers PDFs (text extraction, rendering pages with figures, OCR for scans). Then tell the user the 3-5 key takeaways and ask what to emphasise. Skip the question when the user asked for a quiet or batch ingest.

**Long sources** (roughly 30+ pages, or a long transcript): delegate the reading to the `wiki-source-reader` subagent, which reads the whole file and returns metadata, a summary, key claims with locators, and the entities and concepts mapped to existing page names. That keeps the full document out of this conversation. Before you cite a claim from its report, open the cited page or section and check it; the extraction is a map, not a source.

## 3. Plan the pages and check the names

List the entities and concepts the source touches (typically 5-15 pages, most of them existing). Before creating any page, check its name:

```bash
python3 "${CLAUDE_SKILL_DIR}/../wiki-lint/scripts/lint.py" --names source-slug entity-a concept-b
```

- `free`: create it under that lowercase kebab-case name.
- `taken`: that page exists; update it instead.
- `similar`: an existing page has a matching name, title or alias. Usually it is the same thing, so update it and add the new spelling to its `aliases:`.

Names matter because links resolve by note name alone. A second page for the same thing splits the knowledge and makes links ambiguous.

## 4. Write the source page

Create `wiki/sources/<slug>.md` from `templates/tpl-source.md`. Fill every placeholder yourself: `{{title}}` and `{{date:...}}` are only expanded by Obsidian when a human inserts a template. Set a human-readable `title:`, link the original in `raw:` (for example `raw: "[[paper.pdf]]"`), and fill `kind`, `author`, `origin`, `published`, and today's date in `ingested`, `created` and `updated`. Give each key claim a locator where one exists, e.g. `[[paper.pdf#page=4]]`.

## 5. Update the entity and concept pages

For each page from step 3:

- Add what this source says, citing it on every non-trivial claim, e.g. `... ([[source-slug]])`, and add it to the page's `sources:` frontmatter as a quoted wikilink.
- Create missing pages from the matching template with `status: draft`.
- Link on first meaningful mention, in both directions: the source page links to each entity and concept, and each of those links back.
- Bump `updated:` on every page you change.

## 6. Handle contradictions

Never silently overwrite an existing claim. Keep both, cite both sources, and add a callout on the affected page:

```
> [!warning] Contradiction
> [[source-a]] says X; [[source-b]] says Y. Unresolved.
```

Mark pages whose claims this source supersedes as `status: stale`.

## 7. Update index, overview and log

- `wiki/index.md`: add every new page under its group (`## Sources`, `## Entities`, `## Concepts`, `## Analyses`) as `- [[page-name]] - one-line summary`, and refresh the summaries of changed pages.
- `wiki/overview.md`: revise it if the big picture shifted. If you deliberately linked a page you are not writing yet, record it under "Gaps".
- `wiki/log.md`: append one entry per source (lint counts these entries):
  ```
  ## [YYYY-MM-DD] ingest | <source title>
  ```
  Beneath it, list the pages created and updated as wikilinks, plus anything left open.

## 8. Check and hand back

Run the lint script:

```bash
python3 "${CLAUDE_SKILL_DIR}/../wiki-lint/scripts/lint.py"
```

Fix any findings in pages you touched during this ingest; `--files <page> ...` limits the report to them. In Claude Code a Stop hook runs the same check on everything changed this turn, plus the log entry and `updated:` dates. Mention other findings without fixing them; they belong to a lint pass, which needs the user's go-ahead. Then give the user a short summary: pages created and updated, contradictions found, and open questions the source raised.

**Batches:** ask about emphasis once for the whole batch (or not at all if it is quiet). Start one `wiki-source-reader` per source in parallel, then process the sources one at a time through steps 3-7 (pages written by an earlier source in the batch change what later ones update), write one log entry per source, and run the check once at the end.
