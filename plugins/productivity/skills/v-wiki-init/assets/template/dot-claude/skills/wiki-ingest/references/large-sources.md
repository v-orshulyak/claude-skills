# Large sources: survey, then chunked ingest with a reading map

For sources `source_info.py` rates **large** (about 100+ PDF pages or 50,000+ words: books, long reports, theses, multi-hour transcripts). Such a source does not fit in one read, deserves more than one summary, and takes more than one session. So it is ingested in chapter-sized chunks, and the progress lives in the wiki itself: a book page with a reading map that any later session can resume from.

On Windows use `py` or `python` instead of `python3`.

## Pages it produces

- **Book page** `wiki/sources/<slug>.md`: the whole source at a glance (metadata, thesis, structure) and the **reading map**. Created in the survey, kept current after every chunk.
- **Chunk pages** `wiki/sources/<slug>-<part>.md` (e.g. `ai-engineering-ch03`, `ai-engineering-ch07-09`): one per ingested chunk, written like a normal source page (summary, key claims with locators, entities and concepts, open questions). Entity and concept pages cite the **chunk page**, which pins each claim to a chapter.
- In `wiki/index.md` list the book page under `## Sources` and its chunk pages as indented lines beneath it.

Book page frontmatter: the usual source fields plus

```yaml
type: source
raw: "[[book.pdf]]"
pages: 712
page-offset: 18          # PDF page index = printed page + offset
ingest-status: partial   # partial until every chunk is ingested or skipped, then complete
```

Chunk page frontmatter: the usual source fields, the same `raw:`, plus `part-of: "[[<slug>]]"` and `pages: "112-160"` (PDF indices).

The reading map is a section of the book page, one line per chunk, PDF page indices:

```
## Reading map

- [x] Ch 1-2: Foundations (pp. 19-75) -> [[ai-engineering-ch01-02]]
- [ ] Ch 3: Evaluation (pp. 76-131)
- [-] Ch 4: Case studies (pp. 132-160) - skipped: tangential to this wiki
- [ ] Appendix A (pp. 690-712)
```

`[x]` ingested, `[ ]` pending, `[-]` skipped (with a reason). Lint and the session brief count these markers, so keep the format.

## 1. Survey

Goal: understand the shape of the source and agree on a plan before reading most of it.

1. Find the structure: the outline from `source_info.py` if it printed one, otherwise read the table-of-contents pages (usually within the first 15 PDF pages; Read the PDF with a page range).
2. Work out `page-offset`: find one chapter's printed start page in the TOC, then the PDF page where it actually starts. All locators and ranges use PDF page indices, because Obsidian's `[[book.pdf#page=N]]` does.
3. Delegate the survey reading to the `wiki-source-reader` subagent in **survey mode**: the introduction, the conclusion and the first page or two of each chapter. It returns metadata, the thesis, and a chunk plan.
4. Plan chunks along chapter boundaries, about 30-80 pages each: split a huge chapter at its sections, merge tiny adjacent ones. Front matter, index and bibliography are usually skipped.
5. Write the book page from `templates/tpl-source.md` with the extra frontmatter above, the thesis as its summary, and the reading map with every chunk `[ ]`. Add it to `wiki/index.md`, record the source in `wiki/overview.md` if it shifts the big picture, and log it: `## [YYYY-MM-DD] ingest | <title> (survey)`.
6. Show the user the map and ask which chunks to ingest, which to skip, in what order, and what to emphasise. Mark the skips `[-]` with their reason. Not every chapter of a 700-page book deserves pages in this wiki.

## 2. Ingest chunks in small batches

Work through 2-3 chunks per batch (fewer if they are dense), then stop, report progress, and ask whether to continue. After each batch the user can `/clear` or start a new session: everything needed to resume is on the book page.

For each chunk, in order:

1. Have a `wiki-source-reader` read it in **range mode**: the file, the PDF page range, the page offset, the book title, the book page's summary plus the summaries of chunks already ingested (for continuity), and the instruction to report locators as PDF page indices. Readers for the next few chunks can run in parallel; writing stays one chunk at a time.
2. Spot-check the claims you will cite against the cited pages.
3. Write the chunk page and update the entity and concept pages exactly as in the main skill (steps 4-7): name checks, cited claims, two-way links, contradictions. `lint.py --names` reports sibling chunk pages (`<slug>-ch03` vs `<slug>-ch04`) as `similar`; that is expected, they are different pages.
4. On the book page: tick the line `[x]` and link the chunk page, refresh the summary if the chunk changed the picture, bump `updated:`.
5. Update `wiki/index.md` (the chunk line under the book) and append one log entry: `## [YYYY-MM-DD] ingest | <title>, <part> (pp. A-B)`.
6. Run `lint.py --files` on the pages you touched and fix what it reports.

Each finished chunk leaves the wiki consistent, so an interrupted session loses at most the chunk in progress. Do not cache reader reports or converted text between sessions: re-reading one chunk is cheap, and a cache becomes a second copy of the truth.

## 3. Resume

A book page with `ingest-status: partial` means work in progress. The session brief and lint list these with their progress. To resume: open the book page, read its summary and reading map, and continue with the next `[ ]` chunk (ask if the user wants a different order). Re-ingesting a finished chunk means updating its chunk page, not creating a second one.

## 4. Finish

When no `[ ]` lines remain: set `ingest-status: complete`, rewrite the book page summary as a synthesis of the chunk pages (linking them), update `wiki/overview.md`, and log `## [YYYY-MM-DD] ingest | <title> (complete)`. Suggest a lint pass: a whole book touches many pages.
