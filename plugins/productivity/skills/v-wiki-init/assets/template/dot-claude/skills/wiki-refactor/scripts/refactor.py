#!/usr/bin/env python3
"""Rename or merge wiki pages and rewrite every wikilink to them (run by the wiki-refactor skill).

Usage:
  python3 refactor.py rename OLD NEW [--dry-run]   # wiki/x/OLD.md -> wiki/x/NEW.md, links follow
  python3 refactor.py merge OLD NEW [--dry-run]    # links to OLD point at NEW; OLD goes to .trash/
  python3 refactor.py ... --vault PATH             # another vault (default: the one this lives in)

Obsidian rewrites links when a note is renamed inside the app; a plain `mv` does not, and
every `[[old-name` link breaks. This script does what Obsidian would: it renames the file and
rewrites the target of every wikilink and embed to it (with #heading, ^block and |display
parts kept) in all notes outside raw/, templates/ and hidden folders, frontmatter included.
Links inside code are examples and are left alone.

merge expects the content of OLD to be merged into NEW already (that needs judgement); it then
adds OLD's name, title and aliases to NEW's aliases, removes OLD's line from index and
synthesis-index (NEW has its own), rewrites the remaining links and moves OLD to .trash/.

Standard library only, Python 3.9+, macOS, Windows and Linux.
Exit code: 0 = done (or dry run), 1 = refused (nothing changed), 2 = usage error.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import sys
from pathlib import Path

LINT_PY = Path(__file__).resolve().parents[2] / "wiki-lint" / "scripts" / "lint.py"
_spec = importlib.util.spec_from_file_location("wiki_lint", LINT_PY)
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)

LINK_RE = re.compile(r"(!?\[\[)([^\]\|#]+)((?:#[^\]\|]*)?(?:\|[^\]]*)?\]\])")
INDEXES = ("wiki/index.md", "synthesis/synthesis-index.md")
MOVABLE = ("wiki/", "synthesis/")


def rewrite_line(line: str, old: str, new: str) -> tuple:
    """Rewrite links to `old` outside inline code. Returns (line, count)."""
    parts = re.split(r"(`[^`\n]*`)", line)
    count = 0

    def sub(m):
        nonlocal count
        if lint.link_key(m.group(2)) != old.lower():
            return m.group(0)
        count += 1
        return f"{m.group(1)}{new}{m.group(3)}"

    for i in range(0, len(parts), 2):
        parts[i] = LINK_RE.sub(sub, parts[i])
    return "".join(parts), count


def rewrite_text(text: str, old: str, new: str, drop_lines: bool) -> tuple:
    """Rewrite links outside fenced code. With drop_lines, list lines linking to `old` are removed."""
    out, fence, total = [], None, 0
    for line in text.splitlines(keepends=True):
        m = lint.FENCE_OPEN_RE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            out.append(line)
            continue
        if m:
            fence = m.group(1)
            out.append(line)
            continue
        new_line, count = rewrite_line(line, old, new)
        if count and drop_lines and line.lstrip().startswith("- "):
            total += count
            continue
        total += count
        out.append(new_line)
    return "".join(out), total


def add_aliases(text: str, names: list) -> str:
    """Add names to the frontmatter `aliases:` (inline list or block list), creating it if absent."""
    m = lint.FRONTMATTER_RE.match(text)
    if not m:
        return text
    fm = lint.frontmatter(text) or {}
    have = {a.lower() for a in lint.as_list(fm.get("aliases"))}
    want = [n for n in dict.fromkeys(names) if n and n.lower() not in have]
    if not want:
        return text
    lines = m.group(1).splitlines()
    for i, line in enumerate(lines):
        kv = re.match(r"^aliases\s*:\s*(.*)$", line)
        if not kv:
            continue
        current = lint.as_list(lint._value(kv.group(1))) if kv.group(1).strip() else []
        if kv.group(1).strip() and not kv.group(1).strip().startswith("["):
            current = [lint._scalar(kv.group(1))]
        if not kv.group(1).strip():  # block list follows
            j = i + 1
            while j < len(lines) and re.match(r"^\s*-\s+", lines[j]):
                j += 1
            lines[j:j] = [f'  - "{n}"' for n in want]
        else:
            items = [*current, *want]
            lines[i] = "aliases: [" + ", ".join(f'"{a}"' for a in items) + "]"
        break
    else:
        lines.append("aliases: [" + ", ".join(f'"{n}"' for n in want) + "]")
    return text[:m.start(1)] + "\n".join(lines) + text[m.end(1):]


def find_page(v, name: str) -> list:
    return [rel for rel, note in v.notes.items() if note["stem"].lower() == name.lower()]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=("rename", "merge"))
    ap.add_argument("old", help="note name of the page to rename or merge away (no .md)")
    ap.add_argument("new", help="new note name (rename) or the page to merge into (merge)")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, change nothing")
    ap.add_argument("--vault", help="vault folder (default: the vault this script lives in)")
    args = ap.parse_args()

    here = Path(__file__).resolve()
    root = Path(args.vault).expanduser().resolve() if args.vault else (
        lint.find_vault(here.parent) or lint.find_vault(Path.cwd()))
    if not root or not (root / "wiki").is_dir():
        print(f"no wiki/ folder found at {root or Path.cwd()}; pass --vault", file=sys.stderr)
        return 2
    v = lint.Vault(root)
    old, new = args.old.removesuffix(".md"), args.new.removesuffix(".md")

    def refuse(msg):
        print(f"refused: {msg}", file=sys.stderr)
        return 1

    olds = find_page(v, old)
    if len(olds) != 1:
        return refuse(f"'{old}' matches {len(olds)} notes ({', '.join(olds) or 'none'}); need exactly one")
    src = olds[0]
    if not src.startswith(MOVABLE) or src in INDEXES or src in ("wiki/log.md", "wiki/overview.md"):
        return refuse(f"{src} is not a content page under wiki/ or synthesis/")
    news = find_page(v, new)
    if args.action == "rename":
        if old.lower() == new.lower():
            return refuse("old and new names are the same (a case-only rename breaks on macOS and Windows)")
        if not lint.KEBAB_RE.match(new):
            return refuse(f"'{new}' is not lowercase kebab-case ASCII")
        if news or new.lower() in v.by_key:
            return refuse(f"'{new}' is taken ({', '.join(news) or new}); merge instead?")
        dest = (Path(src).parent / f"{new}.md").as_posix()
    else:
        if len(news) != 1:
            return refuse(f"merge target '{new}' matches {len(news)} notes; need exactly one")
        dest = news[0]
        if dest == src:
            return refuse("cannot merge a page into itself")

    changes = []  # (rel, links rewritten, lines dropped?)
    plan = {}
    for rel, note in v.notes.items():
        if rel.startswith(lint.SKIP_LINK_CHECK) or (args.action == "merge" and rel == src):
            continue
        drop = args.action == "merge" and rel in INDEXES
        text, count = rewrite_text(note["text"], old, new, drop)
        if count:
            plan[rel] = text
            changes.append((rel, count, drop))

    if args.action == "merge":
        fm = v.notes[src]["fm"] or {}
        names = [old, *lint.as_list(fm.get("title")), *lint.as_list(fm.get("aliases"))]
        base = plan.get(dest, v.notes[dest]["text"])
        merged = add_aliases(base, names)
        if merged != base:
            plan[dest] = merged

    verb = "would" if args.dry_run else "did"
    if args.action == "rename":
        print(f"{verb} rename {src} -> {dest}")
    else:
        print(f"{verb} merge {src} into {dest} (aliases added: {old} and its title/aliases); "
              f"{src} {verb} move to .trash/")
    for rel, count, drop in changes:
        print(f"  {rel}: {count} link(s) " + ("removed with their index line" if drop else "rewritten"))
    if not changes:
        print("  no links pointed at it")
    if args.dry_run:
        return 0

    for rel, text in plan.items():
        with open(root / rel, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    if args.action == "rename":
        (root / src).rename(root / dest)
    else:
        trash = root / ".trash" / Path(src).name
        trash.parent.mkdir(exist_ok=True)
        if trash.exists():
            trash.unlink()
        shutil.move(str(root / src), str(trash))
    if args.action == "merge":
        self_links = sum(1 for _, t in lint.wikilinks(plan.get(dest, v.notes[dest]["text"]))
                         if lint.link_key(t) == new.lower())
        if self_links:
            print(f"  {dest} now links to itself {self_links} time(s): reword those sentences")
    print("Next: update title/aliases if the name changed meaning, bump `updated:` on pages whose "
          "content you changed, check the index line, append a refactor entry to log, run lint.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
