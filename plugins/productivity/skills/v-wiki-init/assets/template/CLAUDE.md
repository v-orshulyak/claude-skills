# __PROJECT_NAME__ - LLM Wiki rules

> __DESCRIPTION__

This vault is an **LLM Wiki** (pattern by Andrej Karpathy). Knowledge is compiled once into interlinked Markdown pages and kept current, instead of being re-derived from raw documents on every question. The human curates sources and asks questions; **you** do the summarising, cross-referencing, filing and bookkeeping. The vault is always opened in **Obsidian**, so everything here must work as an Obsidian vault.

Start every session by reading [[index]] (what exists) and the tail of [[log]] (what happened recently).

## Domain focus

_Tailor this section to the project (filled in when the vault was created; refine it together with the user over time)._

- **What counts as a source:** (e.g. papers, articles, meeting notes, transcripts)
- **Entity kinds worth a page:** (people, organisations, products, places ...)
- **Concept kinds worth a page:** (ideas, methods, themes, open problems ...)
- **Conventions:** language, tag vocabulary, depth, audience.

## The layers

| Layer | Folder | Owner | Rule |
|---|---|---|---|
| 1. Raw sources | `raw/` (`raw/assets/` for images and attachments) | Human | **Immutable.** Read, never edit, rename, move or delete. Source of truth. |
| 2. Wiki | `wiki/` | You | You own it completely. Humans read it; you write it. |
| 3. Synthesis | `synthesis/` | You, on request | Artifacts generated *from* the wiki. Only when the user asks. Downstream of the wiki, never the other way round. |
| Schema | this file, `templates/` | Both | Co-evolved. Propose changes to the user before editing them. |

```
raw/                     originals (PDFs, clippings, exports) + raw/assets/
wiki/
  index.md               catalog of every wiki page (you maintain)
  log.md                 append-only chronological record (you maintain)
  overview.md            the evolving big picture / current thesis
  sources/               one summary page per ingested raw source
  entities/              people, organisations, products, places, ...
  concepts/              ideas, methods, themes, terms
  analyses/              saved query answers, comparisons, investigations
synthesis/               generated artifacts + synthesis-index.md
templates/               one Obsidian template per page type
```

## Obsidian link rules

Links are what turn a pile of notes into a wiki, and Obsidian's backlinks, graph view and rename-safety all depend on them being written correctly.

1. **Internal links are always wikilinks:** `[[note-name]]`, with display text when needed: `[[note-name|display text]]`. Never use `[text](path.md)` for notes in the vault. External URLs use normal Markdown links.
2. **Note names are globally unique.** The filename (minus `.md`) is the identity. Check that a name is free before creating a page. Link by name only (`[[attention-mechanism]]`), never by folder path, so links survive moves. Obsidian is configured with "shortest path" links and auto-update on rename.
3. **Link to a heading or block** with `[[note-name#Heading]]` or `[[note-name#^block-id]]`. Link to a PDF page with `[[paper.pdf#page=12]]`. Embed with `![[file]]`.
4. **Every page links out and is linked in.** Each page needs at least one outgoing link to a related page and at least one inbound link (from [[index]] at minimum). A page with no inbound links is an orphan; fix it.
5. **Link on first meaningful mention** of an entity or concept that has (or deserves) a page. Do not link every occurrence.
6. **Unresolved links are a to-do list, not a mistake**, but only deliberately: if you link `[[x]]` to a page that doesn't exist yet, create it in the same pass or record it under "Gaps" in [[overview]].
7. **Wikilinks inside YAML frontmatter must be quoted:** `sources: ["[[some-source]]"]`.
8. **Examples of link syntax in documentation go inside backticks or code fences**, otherwise Obsidian shows them as unresolved ghost nodes in the graph.

## Naming and frontmatter

- Filenames: lowercase kebab-case ASCII (`attention-mechanism.md`, `2024-03-board-meeting.md`). They must be valid on macOS **and** Windows: no `\ / : * ? " < > |`, no trailing dot or space, no Windows-reserved names (`con`, `nul`, `aux` ...), and no two files whose names differ only by case.
- Put the human-readable title in frontmatter `title:` and variants in `aliases:` so Obsidian's link autocomplete finds the page under any name.
- Every wiki and synthesis page starts with YAML frontmatter (see `templates/`). Common fields: `type`, `title`, `aliases`, `tags`, `created`, `updated`, `status`. Always bump `updated` when you change a page.
- Dates are ISO `YYYY-MM-DD`.
- `status`: `draft` (thin or unverified), `stable`, or `stale` (a newer source contradicts or supersedes it).

## Page types (use the matching file in `templates/`)

- **source** (`wiki/sources/`): one per raw file. Summary, key claims with locators, entities/concepts mentioned, open questions. Frontmatter `raw:` links the original, e.g. `raw: "[[paper.pdf]]"`.
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

### Ingest (user adds a source)

1. Read the source in full (see [[TOOLS]] for PDFs). Tell the user the 3-5 key takeaways and ask what to emphasise, unless they asked for a quiet batch ingest.
2. Create `wiki/sources/<slug>.md` from the source template; link the raw file in `raw:`.
3. Update or create the entity and concept pages the source touches. One source typically touches 5-15 pages. Add cross-links in both directions.
4. Flag contradictions with existing pages (callout above) and mark outdated pages `status: stale`.
5. Add every new page to [[index]]; refresh summaries of changed ones.
6. Revise [[overview]] if the big picture shifted.
7. Append to [[log]].

### Query (user asks a question)

1. Read [[index]], then open the relevant pages (use search tools from [[TOOLS]] once the wiki is big). Answer from the wiki, citing pages with wikilinks.
2. If the wiki can't answer, say so and propose which source to ingest or search for; don't fill gaps from memory without labelling it as such.
3. If the answer is worth keeping, offer to save it as an `analysis` page (then update [[index]] and [[log]]).

### Lint (health check, on request or every ~10 ingests)

Report first, fix on the user's go-ahead. Look for: contradictions; stale claims superseded by newer sources; orphan pages; mentioned-but-missing pages (unresolved links); pages missing frontmatter, `updated` or sources; `(unsourced)` claims; duplicate or near-duplicate pages; index entries that are missing or dead; synthesis artifacts older than the pages they are based on; and gaps a web search or new source could fill. Suggest 3-5 next questions or sources. Log the pass.

### Synthesize (user asks for an artifact)

See the next section.

## Synthesis layer (`synthesis/`)

The wiki answers "what do we know?". The synthesis layer holds **things made from that knowledge**: reports, briefs, decks, FAQs, timelines, comparison tables, study guides, drafts of articles, anything the user asks to be produced.

Rules:

1. **Only on request.** Never generate synthesis artifacts proactively.
2. **Read the wiki, not `raw/`.** Build from wiki pages so the wiki stays the single source of truth. If something needed is missing, tell the user and propose an ingest first.
3. **Cite back with wikilinks.** Every factual statement links to the wiki page it came from. List them in frontmatter `based-on:`.
4. **One-way dependency.** Synthesis depends on the wiki; wiki pages never depend on or link to synthesis. If synthesizing reveals a new insight, save it as an `analysis` page in `wiki/analyses/` and cite that.
5. **Disposable and reproducible.** Record `generated:` and `based-on:`; an artifact is stale when any based-on page has a newer `updated:`. Regenerate instead of hand-patching.
6. **Naming:** `synthesis/<kind>-<topic>.md` (e.g. `brief-board-update.md`); subfolders by kind (`reports/`, `decks/`) are fine once there are many.
7. **Other formats** (`.pptx`, `.xlsx`, `.html`, `.pdf`): save the file in `synthesis/` and add a companion `.md` note with the same stem (e.g. `deck-q3.pptx` + `deck-q3.md`) carrying the frontmatter and backlinks. Slide decks can also be written as Markdown for the Marp plugin.
8. Register it in [[synthesis-index]] and append to [[log]].

## index.md and log.md

**[[index]]** is the content catalog. One line per page: `- [[page-name]] - one-line summary`, grouped under `## Sources`, `## Entities`, `## Concepts`, `## Analyses`. Keep summaries current. Read it first on every query.

**[[log]]** is append-only, newest at the bottom. Every entry starts with a parseable heading so `grep`/`rg` can pull recent history:

```
## [YYYY-MM-DD] <op> | <title>
```

`<op>` is one of `ingest`, `query`, `lint`, `synthesize`, `schema`, `setup`. Beneath it, list pages created and updated as wikilinks and note anything unresolved. Never rewrite old entries.

## Environment: macOS and Windows

This vault is used from both macOS and Windows (and works on Linux). Therefore:

- Assume nothing about the shell. Check the OS before suggesting commands; [[TOOLS]] lists install and usage for both (`zsh`/`bash` vs PowerShell).
- Use forward slashes in links and paths inside notes; never absolute paths or drive letters.
- Keep filenames portable (see "Naming"). Don't create symlinks. Keep paths short.
- Files use LF line endings (`.gitattributes` enforces this). Don't convert them.
- Prefer tools that exist on both platforms. Never make a workflow depend on a Unix-only tool without a Windows alternative.
- Search and PDF tooling is optional but recommended; see [[TOOLS]].

## Evolving these rules

When the user corrects how you work, or a convention proves useful, propose the change to this file and log it as `schema`. Keep this file short enough to be read at the start of every session.
