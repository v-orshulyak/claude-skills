# __PROJECT_NAME__ - LLM Wiki rules

> __DESCRIPTION__

This vault is an **LLM Wiki** (pattern by Andrej Karpathy): knowledge is compiled once into interlinked Markdown pages and kept current, instead of being re-derived from raw documents on every question. The human curates sources and asks questions; **you** do the summarising, cross-referencing, filing and bookkeeping. The vault is opened in **Obsidian**, so everything must work as an Obsidian vault.

Start every session by reading [[index]] (what exists) and the tail of [[log]] (what happened recently). In Claude Code a session-start hook already shows the recent log entries and the raw files not ingested yet.

## Domain focus

_Tailor this section to the project (filled in when the vault was created; refine it together with the user over time)._

- **What counts as a source:** (e.g. papers, articles, meeting notes, transcripts)
- **Entity kinds worth a page:** (people, organisations, products, places ...)
- **Concept kinds worth a page:** (ideas, methods, themes, open problems ...)
- **Conventions:** language, tag vocabulary, depth, audience.

## The layers

| Layer | Folder | Owner | Rule |
|---|---|---|---|
| 1. Raw sources | `raw/` (`raw/assets/` for images and attachments) | Human | **Immutable.** Read, never edit, rename, move or delete. New sources are added with `wiki-capture`. Source of truth. |
| 2. Wiki | `wiki/`: `index.md`, `log.md`, `overview.md` (the evolving big picture) and `sources/`, `entities/`, `concepts/`, `analyses/` | You | You own it completely. Humans read it; you write it. |
| 3. Synthesis | `synthesis/` (catalog: `synthesis-index.md`) | You, on request | Artifacts generated *from* the wiki. Only when the user asks. Downstream of the wiki, never the other way round. |
| Schema | this file, `templates/` (one per page type) | Both | Co-evolved. Propose changes to the user before editing them. |

## Obsidian link rules

Links are what turn a pile of notes into a wiki, and Obsidian's backlinks, graph view and rename-safety all depend on them being written correctly.

1. **Internal links are always wikilinks:** `[[note-name]]`, with display text when needed: `[[note-name|display text]]`. Never use `[text](path.md)` for notes in the vault. External URLs use normal Markdown links. Write link syntax *examples* inside backticks, or Obsidian shows them as ghost nodes in the graph.
2. **Note names are globally unique.** The filename (minus `.md`) is the identity. Check that a name is free before creating a page. Link by name only (`[[attention-mechanism]]`), never by folder path, so links survive moves. Obsidian is configured with "shortest path" links and auto-update on rename.
3. **Link to a heading or block** with `[[note-name#Heading]]` or `[[note-name#^block-id]]`. Link to a PDF page with `[[paper.pdf#page=12]]`. Embed with `![[file]]`.
4. **Every page links out and is linked in.** Each page needs at least one outgoing link to a related page and at least one inbound link (from [[index]] at minimum). A page with no inbound links is an orphan; fix it.
5. **Link on first meaningful mention** of an entity or concept that has (or deserves) a page. Do not link every occurrence.
6. **Unresolved links are a to-do list, not a mistake**, but only deliberately: if you link `[[x]]` to a page that doesn't exist yet, create it in the same pass or record it under "Gaps" in [[overview]].
7. **Wikilinks inside YAML frontmatter must be quoted:** `sources: ["[[some-source]]"]`.

## Naming and frontmatter

- Filenames: lowercase kebab-case ASCII (`attention-mechanism.md`, `2024-03-board-meeting.md`). They must be valid on macOS **and** Windows: no `\ / : * ? " < > |`, no trailing dot or space, no Windows-reserved names (`con`, `nul`, `aux` ...), and no two files whose names differ only by case.
- **Never rename, move or delete a wiki page with `mv`, a delete or a Write under a new name**: links resolve by name and would break. Use the `wiki-refactor` skill, which rewrites every link like Obsidian does.
- Put the human-readable title in frontmatter `title:` (the templates leave it blank) and variants in `aliases:` so Obsidian's link autocomplete finds the page under any name.
- Every wiki and synthesis page starts with YAML frontmatter (see `templates/`). Common fields: `type`, `title`, `aliases`, `tags`, `created`, `updated`, `status`. Dates are ISO `YYYY-MM-DD`. Always bump `updated` when you change a page.
- `status`: `draft` (thin or unverified), `stable`, or `stale` (a newer source contradicts or supersedes it).

## Page types (use the matching file in `templates/`)

- **source** (`wiki/sources/`): one per raw file (a large source gets a book page with a reading map plus one page per ingested chunk). Summary, key claims with locators, entities/concepts mentioned, open questions. Frontmatter `raw:` links the original, e.g. `raw: "[[paper.pdf]]"`.
- **entity** (`wiki/entities/`): a thing in the world. What it is, role in this domain, timeline, relations, where each fact came from.
- **concept** (`wiki/concepts/`): an idea or topic. Definition, how it's used, competing views, related concepts.
- **analysis** (`wiki/analyses/`): a valuable answer, comparison or investigation saved back so explorations compound instead of vanishing into chat history.
- **synthesis** (`synthesis/`): a generated artifact; see "Synthesis layer".

**Provenance:** every non-trivial claim on an entity, concept or analysis page cites a source page, e.g. `... ([[some-source]])`, with a locator when possible (`[[paper.pdf#page=4]]`). Claims without a source are marked `(unsourced)` so lint can find them.

**Contradictions:** never silently overwrite. Keep both claims, cite both sources, and add a callout:

```
> [!warning] Contradiction
> [[source-a]] says X; [[source-b]] says Y. Unresolved.
```

## Workflows

Full procedures live in `.claude/skills/<name>/SKILL.md`. Claude Code loads them as skills; any other agent should read the matching `SKILL.md` before starting.

| Skill | When |
|---|---|
| `wiki-capture` | Save a URL, pasted text or outside file into `raw/` |
| `wiki-ingest` | File a source from `raw/` into the wiki. Size is estimated first: long sources go to the `wiki-source-reader` subagent; large ones (books) are surveyed and ingested in chunks, with progress kept in a reading map on the book page |
| `wiki-lint` | Health check, on request or every ~10 ingests: script + judgement, report first, fix on the go-ahead |
| `wiki-refactor` | Rename, merge or split pages without breaking links |
| `wiki-research` | Find sources for gaps and open questions, then capture them |
| `wiki-synthesize` | Produce or regenerate an artifact in `synthesis/` |

**Guardrails (Claude Code hooks, `.claude/settings.json`):** edits, overwrites, moves and deletes in `raw/` are blocked (adding new files is allowed); when a turn changed `wiki/` or `synthesis/`, a Stop hook checks for a log entry, today's `updated:` on changed pages, and lint findings on those pages. If it sends you back, fix what it lists.

### Query (no skill: the everyday case)

1. Read [[index]], then open the relevant pages (use search tools from [[TOOLS]] once the wiki is big). Answer from the wiki, citing pages with wikilinks.
2. If the wiki can't answer, say so and propose which source to ingest or search for; don't fill gaps from memory without labelling it as such.
3. If the answer is worth keeping, offer to save it as an `analysis` page (then update [[index]] and [[log]]).

## Synthesis layer (`synthesis/`)

The wiki answers "what do we know?"; `synthesis/` holds **things made from that knowledge** (reports, briefs, decks, FAQs, timelines, drafts), produced **only on request**, built from wiki pages (never `raw/`), citing them with wikilinks, registered in [[synthesis-index]], and regenerated rather than patched when stale. Wiki pages never link to artifacts. The full rules load from `.claude/rules/synthesis.md` when you touch `synthesis/`; the procedure is the `wiki-synthesize` skill.

## index.md and log.md

**[[index]]** is the content catalog. One line per page: `- [[page-name]] - one-line summary`, grouped under `## Sources`, `## Entities`, `## Concepts`, `## Analyses`. Keep summaries current. Read it first on every query.

**[[log]]** is append-only, newest at the bottom. Every entry starts with a parseable heading so `grep`/`rg` can pull recent history:

```
## [YYYY-MM-DD] <op> | <title>
```

`<op>` is one of `capture`, `ingest`, `query`, `lint`, `refactor`, `synthesize`, `schema`, `setup`. Beneath it, list pages created and updated as wikilinks and note anything unresolved. Never rewrite old entries (link targets rewritten by `wiki-refactor` are the exception).

## Environment: macOS and Windows

The vault is used from both. Check the OS before suggesting commands and never make a workflow depend on a Unix-only tool; [[TOOLS]] has the commands for both and the portability checklist (forward slashes, no absolute paths or symlinks, LF endings).

## Evolving these rules

When the user corrects how you work, or a convention proves useful, propose the change to this file and log it as `schema`. Keep this file short enough to be read at the start of every session.
