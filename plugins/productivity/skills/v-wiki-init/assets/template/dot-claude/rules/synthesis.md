---
paths:
  - "synthesis/**"
---

# Synthesis layer rules

Loaded when you work on files in `synthesis/`. The full procedure is the `wiki-synthesize` skill (`.claude/skills/wiki-synthesize/SKILL.md`).

1. **Only on request.** Never create or regenerate artifacts unless the user asked.
2. **Built from the wiki, not `raw/`.** Missing knowledge means an ingest first, or a gap marked in the artifact; never filling from memory unmarked.
3. **Cite back.** Every factual statement links to the wiki page it came from; all of them are listed in `based-on:`.
4. **One-way.** Wiki pages never link to artifacts. New insights become `analysis` pages in `wiki/analyses/`, which the artifact then cites.
5. **Regenerate, don't patch.** An artifact is stale when a `based-on:` page has a newer `updated:` than its `generated:`. Rebuild it and set `generated:` to today.
6. **Non-Markdown files** (`.pptx`, `.xlsx`, `.html`, `.pdf` ...) get a companion `.md` note with the same stem carrying the frontmatter and links.
7. **Register** every artifact in `synthesis/synthesis-index.md` and log it as `synthesize`.
