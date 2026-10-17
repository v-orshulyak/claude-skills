---
name: wiki-refactor
description: Rename, merge or split pages of this LLM wiki without breaking links. A script renames the file and rewrites every wikilink to it (as Obsidian does on rename), or merges a duplicate into another page, adds its names as aliases and moves it to .trash. Use whenever the user says "rename this page", "merge X into Y", "these two pages are the same thing", "split this page", "reorganise the concepts", when a lint pass finds near-duplicates the user wants merged, or whenever you are about to rename or delete a wiki page yourself. Never use mv or delete for wiki pages.
---

# Wiki refactor

Links in this vault resolve by note name alone, so a page's filename is its identity. Obsidian rewrites links when a note is renamed inside the app; a plain `mv`, a delete or a Write under a new name does not, and every `[[old-name` link breaks. This skill does renames and merges through a script that rewrites the links the way Obsidian would.

`${CLAUDE_SKILL_DIR}` below is this skill's folder (`.claude/skills/wiki-refactor`). On Windows use `py` or `python` instead of `python3`.

## Rename

1. Pick the new name: lowercase kebab-case, and free:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/../wiki-lint/scripts/lint.py" --names new-name
   ```
   If it is `taken` or `similar`, it is probably a merge instead.
2. Preview, then run:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/refactor.py" rename old-name new-name --dry-run
   python3 "${CLAUDE_SKILL_DIR}/scripts/refactor.py" rename old-name new-name
   ```
   The file stays in its folder; links (including `#heading`, `^block`, `|display` and embeds, in frontmatter too) are rewritten in every note outside `raw/` and `templates/`. Links inside code are examples and stay.
3. If the name changed because the meaning did, update `title:` and `aliases:` on the page and the summary on its `index` line, and bump `updated:`. A pure rename needs no `updated:` bump on the pages whose links were rewritten: their content did not change.

## Merge (two pages about the same thing)

1. Decide which page survives (usually the better name or the richer page) and tell the user before merging.
2. Merge the content by hand first: move every claim with its citation into the surviving page, keep both sides of any contradiction, union the `sources:` lists, and bump `updated:`.
3. Then let the script redirect the links and retire the old page:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/refactor.py" merge old-name surviving-name --dry-run
   python3 "${CLAUDE_SKILL_DIR}/scripts/refactor.py" merge old-name surviving-name
   ```
   It adds the old name, title and aliases to the survivor's `aliases:`, removes the old page's line from `index` / `synthesis-index`, rewrites all other links, and moves the old file to `.trash/` (recoverable, ignored by git and Obsidian).
4. Reword sentences that now link to the page itself, or say the same link twice (the script reports self-links).

## Split (one page covers two things)

There is no script for this; it needs judgement. Create the new page from its template (check the name first), move the claims that belong there with their citations, link the two pages to each other, and add the new page to `index`. Then search for links to the original that mean the split-off part (`rg -n "\[\[original-name" wiki synthesis`) and point them at the new page by hand.

## Finish

- Append to `wiki/log.md`: `## [YYYY-MM-DD] refactor | <what was renamed or merged>`, listing the pages touched. (Inside a lint pass, record it in the lint entry instead.)
- Run lint on the result: `python3 "${CLAUDE_SKILL_DIR}/../wiki-lint/scripts/lint.py"`.
- Never rename, move or merge anything in `raw/`; source pages link to those files by name.
