---
name: wiki-lint
description: Health-check this LLM wiki. A script finds orphan pages, broken or unresolved wikilinks, missing or dead index entries, pages missing frontmatter, updated dates or sources, (unsourced) claims, stale synthesis artifacts and duplicate names; then you review contradictions, near-duplicate pages, stale claims and gaps, report, and fix only on the user's go-ahead. Use whenever the user says "lint the wiki", "health-check the wiki", "check the wiki", "find broken links / orphans", "what's stale or missing", "clean up the wiki", "audit the sources", or about 10 ingests have happened since the last lint.
---

# Wiki lint

A lint pass keeps the wiki trustworthy as it grows: every page reachable from `index`, every claim traceable to a source, contradictions visible rather than silently overwritten. It has two halves. A script checks everything that is mechanical, so those results are exact and cheap. You then do the parts that need reading and judgement.

`${CLAUDE_SKILL_DIR}` below is this skill's folder (`.claude/skills/wiki-lint` in the vault). Agents without skill support can run the same paths directly.

## 1. Run the script

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/lint.py"
```

On Windows use `py` or `python`. It needs Python 3.9+ and only reads files. Exit code 1 means it found something, not that it crashed. Add `--json` if you want to process the findings programmatically.

It reports, under **Findings**: unresolved wikilinks (except those deliberately recorded under "Gaps" in `overview`), orphan pages, dead-end pages, frontmatter problems (missing frontmatter, `type`, `title`, `updated`/`generated`, empty `sources:` / `raw:` / `based-on:`, bad dates, unfilled `{{...}}` template placeholders, a type that doesn't match its folder), `(unsourced)` claims, pages missing from `index` or `synthesis-index` and dead entries in them, stale synthesis artifacts, wiki pages linking to synthesis artifacts, duplicate note names, and non-kebab-case filenames. Under **For review** it lists starting points for your half: open contradiction callouts, pages marked `status: stale`, possible duplicates by name, links recorded under Gaps, files in `raw/` not ingested yet, and the number of ingests since the last lint.

## 2. Do the judgement part

Bound the reading: by default look at pages touched since the last `lint` entry in `log` (the log lists them under each ingest), plus whatever the script flagged. Offer a full pass on a large wiki rather than starting one, since it means reading every page.

- **Contradictions.** For each open callout, check whether a later source settles it. In recently touched pages, look for claims that disagree with other pages without a callout.
- **Stale claims.** Pages whose claims a newer source supersedes, and pages already marked `status: stale` that still need rewriting.
- **Near-duplicates.** Open each "possible duplicates" pair and decide: same thing (merge), related (cross-link), or unrelated (ignore). Also watch for the same idea split across pages under different names.
- **Gaps.** Thin `draft` pages, "Open questions" sections, links recorded under Gaps, and topics many pages mention but no source covers well. Note what a web search or a new source could fill.
- **Next steps.** Suggest 3-5 questions worth asking or sources worth finding.

## 3. Report first

Give the user one compact report: script findings grouped by kind with a proposed fix for each group, your judgement findings, and the next questions or sources. Don't change anything yet: lint fixes can merge, rename or restructure pages, and the user should decide which of those they want.

## 4. Fix on the go-ahead

Apply only what the user approved, following the rules in `CLAUDE.md`:

- **Orphan:** add it to `index` and link it from the most related page. **Dead-end:** link it to related pages.
- **Unresolved link:** create the page, correct the link, or record it under "Gaps" in `overview`.
- **Gaps worth filling:** offer the `wiki-research` skill to find sources for them.
- **`(unsourced)` claim:** find a source page that supports it, or leave the marker.
- **Missing or dead index entry:** add or remove the line, keeping the one-line summary current.
- **Near-duplicate:** merge the content into one page, then let the `wiki-refactor` skill's script redirect every link, add the old names to `aliases:` and retire the other page. Renames go through it too; never `mv` a wiki page.
- **Stale synthesis:** regenerate it rather than hand-patching, and only if the user asks; synthesis is produced on request.
- Never edit, move or delete anything in `raw/`. Bump `updated:` on every page you change.

Re-run the script to confirm the fixes, then append to `log`, even when nothing was fixed, so the "ingests since the last lint" count resets:

```
## [YYYY-MM-DD] lint | <one-line summary>
```

Beneath it, list the pages changed as wikilinks and what was left open.
