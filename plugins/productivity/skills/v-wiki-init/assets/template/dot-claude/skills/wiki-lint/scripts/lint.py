#!/usr/bin/env python3
"""Deterministic health check for this LLM wiki (run by the wiki-lint skill).

Usage:
  python3 lint.py                   # lint the vault this script lives in
  python3 lint.py --vault PATH      # lint another vault
  python3 lint.py --json            # machine-readable output
  python3 lint.py --names NAME ...  # is a page name free? (used by wiki-ingest)
  python3 lint.py --new-sources     # raw/ files no source page covers yet (used by wiki-ingest)

Reports only what a script can decide. Contradictions between claims, near-duplicate
content and gaps need judgement and are left to the model; the "for review" section
gives it starting points. Never modifies files. Standard library only, Python 3.9+,
macOS, Windows and Linux.

Exit code: 0 = no findings (or every name free), 1 = findings, 2 = usage error.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
LOG_ENTRY_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] (\w+) \|", re.M)
CONTRADICTION_RE = re.compile(r"^>\s*\[!warning\][+-]?\s*contradiction", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDER_RE = re.compile(r"\{\{[^}]*\}\}")

# folder -> the page type that belongs there
FOLDER_TYPES = {"wiki/sources": "source", "wiki/entities": "entity", "wiki/concepts": "concept",
                "wiki/analyses": "analysis", "synthesis": "synthesis"}
NEEDS_SOURCES = {"entity", "concept", "analysis"}
SKIP_LINK_CHECK = ("templates/", "raw/")  # placeholders, and immutable originals that aren't ours to fix
CHECK_TITLES = {
    "unresolved": "Unresolved wikilinks (create the page, fix the link, or record it under Gaps in overview)",
    "orphan": "Orphan pages (nothing links to them)",
    "dead-end": "Dead-end pages (no links to other pages)",
    "frontmatter": "Frontmatter problems",
    "unsourced": "(unsourced) claims",
    "index": "Index entries missing or dead",
    "stale-synthesis": "Synthesis artifacts older than the pages they are based on",
    "one-way": "Wiki pages linking to synthesis artifacts (the dependency is one-way)",
    "duplicate": "Duplicate note names (shortest-path links become ambiguous)",
    "naming": "Filenames that are not lowercase kebab-case",
}


# ---------------------------------------------------------------- parsing helpers

def code_free_lines(text: str):
    """Yield (line number, line) outside fenced code, with inline code removed."""
    fence = None
    for no, line in enumerate(text.splitlines(), 1):
        m = FENCE_OPEN_RE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if m:
            fence = m.group(1)
            continue
        yield no, INLINE_CODE_RE.sub("", line)


def strip_code(text: str) -> str:
    return "\n".join(line for _, line in code_free_lines(text))


def wikilinks(text: str) -> list:
    """[(line number, target)] for every wikilink outside code (frontmatter included)."""
    return [(no, m.group(1).strip()) for no, line in code_free_lines(text) for m in WIKILINK_RE.finditer(line)]


def link_key(target: str) -> str:
    """What Obsidian resolves a link by: the last path segment, case-insensitive."""
    return target.strip().replace("\\", "/").split("/")[-1].lower()


def _scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _value(value: str):
    value = value.strip()
    if value.startswith("[") and value.endswith("]") and not value.startswith("[["):
        inner = value[1:-1]
        items = re.findall(r'"((?:[^"\\]|\\.)*)"|\'([^\']*)\'|([^,\s][^,]*)', inner)
        return [next(g for g in groups if g).strip() if any(groups) else "" for groups in items]
    return _scalar(value)


def frontmatter(text: str):
    """A small YAML subset: `key: value`, `key: [a, "b"]` and `- item` lists. None if absent."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    data, key = {}, None
    for raw in m.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s*-\s+(.*)$", raw)
        if item and key is not None:
            if not isinstance(data[key], list):
                data[key] = []
            data[key].append(_scalar(item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", raw)
        if kv:
            key = kv.group(1)
            data[key] = _value(kv.group(2))
    return data


def as_list(value) -> list:
    if isinstance(value, list):
        return [v for v in value if v]
    return [value] if value else []


def normalise(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


# ---------------------------------------------------------------- vault model

def walk_files(vault: Path) -> list:
    """Vault-relative POSIX paths of every file outside hidden folders (.obsidian, .claude, .git ...)."""
    out = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(files):
            if not name.startswith("."):
                out.append((Path(root) / name).relative_to(vault).as_posix())
    return out


def find_vault(start: Path):
    for p in (start, *start.parents):
        if (p / "wiki").is_dir():
            return p
    return None


class Vault:
    def __init__(self, root: Path):
        self.root = root
        self.files = walk_files(root)
        self.notes = {}  # rel -> dict(text, fm, links, stem)
        for rel in self.files:
            if rel.endswith(".md"):
                text = (root / rel).read_text(encoding="utf-8", errors="replace")
                self.notes[rel] = {"text": text, "fm": frontmatter(text), "links": wikilinks(text),
                                   "stem": Path(rel).stem}
        self.by_key = {}  # link key -> [rel]
        for rel in self.files:
            self.by_key.setdefault(Path(rel).name.lower(), []).append(rel)
        for rel, note in self.notes.items():
            self.by_key.setdefault(note["stem"].lower(), []).append(rel)

    def resolve(self, target: str):
        hits = self.by_key.get(link_key(target))
        return hits[0] if hits else None

    def resolve_notes(self, target: str) -> list:
        """Every note a link may point to. Duplicate names make a link ambiguous; counting it
        for all candidates keeps one duplicate from cascading into orphan/index findings."""
        return [hit for hit in self.by_key.get(link_key(target), []) if hit in self.notes]

    def kind(self, rel: str):
        """Expected page type from the folder, or None for meta/root/other files."""
        if rel in ("wiki/index.md", "wiki/log.md", "wiki/overview.md", "synthesis/synthesis-index.md"):
            return None
        for folder, kind in FOLDER_TYPES.items():
            if rel.startswith(folder + "/"):
                return kind
        return None

    def content_pages(self) -> list:
        return [rel for rel in self.notes if self.kind(rel)]


# ---------------------------------------------------------------- checks

def lint(v: Vault) -> tuple:
    findings, review = [], {}

    def add(check, rel, detail, line=None):
        findings.append({"check": check, "path": rel, "line": line, "detail": detail})

    linkable = [rel for rel in v.notes if not rel.startswith(SKIP_LINK_CHECK)]
    inbound = {rel: set() for rel in v.notes}
    outbound = {rel: set() for rel in v.notes}
    for rel in linkable:
        for _, target in v.notes[rel]["links"]:
            for hit in v.resolve_notes(target):
                if hit != rel:
                    inbound[hit].add(rel)
                    outbound[rel].add(hit)

    # links recorded on purpose under "## Gaps" in overview are a to-do list, not errors
    gaps = set()
    overview = v.notes.get("wiki/overview.md")
    if overview:
        in_gaps = False
        for _, line in code_free_lines(overview["text"]):
            if line.startswith("## "):
                in_gaps = line[3:].strip().lower().startswith("gaps")
            elif in_gaps:
                gaps.update(link_key(m.group(1)) for m in WIKILINK_RE.finditer(line))
    indexes = {"wiki/index.md", "synthesis/synthesis-index.md"}
    recorded = set()
    for rel in linkable:
        for line, target in v.notes[rel]["links"]:
            if v.resolve(target):
                continue
            if link_key(target) in gaps:
                recorded.add(target)
            elif rel not in indexes:
                add("unresolved", rel, f"[[{target}]]", line)

    content = v.content_pages()
    for rel in content:
        if not inbound[rel]:
            add("orphan", rel, "no inbound links")
        if not outbound[rel]:
            add("dead-end", rel, "no links to other pages")

    for rel, note in v.notes.items():
        if not rel.startswith(("wiki/", "synthesis/")):
            continue
        fm, kind = note["fm"], v.kind(rel)
        if fm is None:
            add("frontmatter", rel, "no YAML frontmatter")
            continue
        missing = [k for k in ("type", "title", "generated" if kind == "synthesis" else "updated")
                   if not fm.get(k)]
        if missing:
            add("frontmatter", rel, "missing " + ", ".join(missing))
        if kind and fm.get("type") and fm["type"] != kind:
            add("frontmatter", rel, f"type is '{fm['type']}' but the folder holds {kind} pages")
        for key in ("created", "updated", "generated", "ingested"):
            value = fm.get(key)
            if value and not DATE_RE.match(str(value)) and not PLACEHOLDER_RE.search(str(value)):
                add("frontmatter", rel, f"{key} '{value}' is not a YYYY-MM-DD date")
        page_type = kind or fm.get("type")
        if page_type in NEEDS_SOURCES and not as_list(fm.get("sources")):
            add("frontmatter", rel, "sources: is empty")
        if page_type == "source" and not fm.get("raw"):
            add("frontmatter", rel, "raw: does not link the original file")
        if page_type == "synthesis" and not as_list(fm.get("based-on")):
            add("frontmatter", rel, "based-on: is empty")
        for no, line in code_free_lines(note["text"]):
            if PLACEHOLDER_RE.search(line):
                add("frontmatter", rel, f"unfilled template placeholder {PLACEHOLDER_RE.search(line).group(0)}", no)
            if kind and kind != "synthesis" and "(unsourced)" in line:
                add("unsourced", rel, line.strip()[:120], no)

    # index.md lists every wiki content page; synthesis-index.md every artifact
    for index, prefix in (("wiki/index.md", "wiki/"), ("synthesis/synthesis-index.md", "synthesis/")):
        if index not in v.notes:
            add("index", index, "index page is missing")
            continue
        listed = set()
        for line, target in v.notes[index]["links"]:
            if v.resolve(target):
                listed.update(v.resolve_notes(target))
            elif link_key(target) not in gaps:
                add("index", index, f"dead entry [[{target}]]", line)
        for rel in content:
            if rel.startswith(prefix) and rel not in listed:
                add("index", rel, f"not listed in {Path(index).name}")

    for rel in content:
        if v.kind(rel) != "synthesis":
            continue
        fm = v.notes[rel]["fm"] or {}
        generated = str(fm.get("generated") or "")
        if not DATE_RE.match(generated):
            continue
        newer = []
        for item in as_list(fm.get("based-on")):
            m = WIKILINK_RE.search(item)
            hit = v.resolve(m.group(1) if m else item)
            updated = str(((v.notes.get(hit) or {}).get("fm") or {}).get("updated") or "")
            if DATE_RE.match(updated) and updated > generated:
                newer.append(f"{Path(hit).stem} ({updated})")
        if newer:
            add("stale-synthesis", rel, f"generated {generated}; newer: {', '.join(newer)}")

    # knowledge pages must not depend on artifacts; index and log may point at them for navigation
    for rel in v.notes:
        if (v.kind(rel) and v.kind(rel) != "synthesis") or rel == "wiki/overview.md":
            for target in sorted(t for t in outbound[rel] if v.kind(t) == "synthesis"):
                add("one-way", rel, f"links to {target}")

    stems = {}
    for rel, note in v.notes.items():
        stems.setdefault(note["stem"].lower(), []).append(rel)
    for stem, paths in sorted(stems.items()):
        if len(paths) > 1:
            add("duplicate", paths[0], f"'{stem}' is also {', '.join(paths[1:])}")

    for rel in v.files:
        if rel.startswith(("wiki/", "synthesis/")) and not KEBAB_RE.match(Path(rel).stem):
            add("naming", rel, "use lowercase kebab-case ASCII")

    # ---- for review: starting points for the judgement part of the lint
    contradictions = []
    for rel in content:
        count = sum(1 for _, line in code_free_lines(v.notes[rel]["text"]) if CONTRADICTION_RE.match(line))
        if count:
            contradictions.append(f"{rel} ({count})")
    stale = [rel for rel in content if (v.notes[rel]["fm"] or {}).get("status") == "stale"]
    review["open contradiction callouts"] = contradictions
    review["pages marked status: stale"] = stale
    review["possible duplicates (check content)"] = near_duplicates(v, content)
    review["unresolved links recorded under Gaps"] = sorted(f"[[{t}]]" for t in recorded)
    review["raw files not ingested yet"] = new_sources(v)
    review["ingests since the last lint"] = [str(ingests_since_lint(v))]
    return findings, review


def names_of(v: Vault, rel: str) -> list:
    fm = v.notes[rel]["fm"] or {}
    return [v.notes[rel]["stem"], *as_list(fm.get("title")), *as_list(fm.get("aliases"))]


def near_duplicates(v: Vault, pages: list, limit: int = 20) -> list:
    keyed = [(rel, {normalise(n) for n in names_of(v, rel) if normalise(n)}) for rel in pages]
    out = []
    for i, (a, names_a) in enumerate(keyed):
        for b, names_b in keyed[i + 1:]:
            if names_a & names_b or any(
                    min(len(x), len(y)) >= 5 and difflib.SequenceMatcher(None, x, y).ratio() >= 0.88
                    for x in names_a for y in names_b):
                out.append(f"{a} ~ {b}")
                if len(out) >= limit:
                    return out
    return out


def ingests_since_lint(v: Vault) -> int:
    log = v.notes.get("wiki/log.md")
    count = 0
    for _, op in LOG_ENTRY_RE.findall(log["text"] if log else ""):
        if op == "lint":
            count = 0
        elif op == "ingest":
            count += 1
    return count


def new_sources(v: Vault) -> list:
    """Files in raw/ (outside raw/assets) that no wiki/sources page links in its raw: field."""
    referenced = set()
    for rel, note in v.notes.items():
        if rel.startswith("wiki/sources/"):
            for item in as_list((note["fm"] or {}).get("raw")):
                m = WIKILINK_RE.search(item)
                hit = v.resolve(m.group(1) if m else item)
                if hit:
                    referenced.add(hit)
    return [rel for rel in v.files
            if rel.startswith("raw/") and not rel.startswith("raw/assets/") and rel not in referenced]


def check_names(v: Vault, names: list) -> list:
    """One verdict per proposed page name: free, taken, or similar to an existing page."""
    out = []
    for name in names:
        key, norm = name.lower().removesuffix(".md"), normalise(name)
        taken = [rel for rel in v.notes if v.notes[rel]["stem"].lower() == key]
        similar = []
        for rel in v.notes:
            if rel in taken or rel.startswith("templates/"):
                continue
            for other in names_of(v, rel):
                n = normalise(other)
                if n and (n == norm or (min(len(n), len(norm)) >= 5
                                        and difflib.SequenceMatcher(None, n, norm).ratio() >= 0.88)):
                    similar.append(f"{rel} ('{other}')")
                    break
        if taken:
            out.append((name, "taken", ", ".join(taken)))
        elif similar:
            out.append((name, "similar", ", ".join(similar) + " - reuse that page or add an alias"))
        else:
            out.append((name, "free", "" if KEBAB_RE.match(key) else "but not lowercase kebab-case"))
    return out


# ---------------------------------------------------------------- output

def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", help="vault folder (default: the vault this script lives in)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a report")
    ap.add_argument("--names", nargs="+", metavar="NAME", help="check whether page names are free")
    ap.add_argument("--new-sources", action="store_true",
                    help="list files in raw/ that no source page covers yet")
    args = ap.parse_args()

    here = Path(__file__).resolve()
    root = Path(args.vault).expanduser().resolve() if args.vault else (
        find_vault(here.parent) or find_vault(Path.cwd()))
    if not root or not (root / "wiki").is_dir():
        print(f"no wiki/ folder found at {root or Path.cwd()}; pass --vault", file=sys.stderr)
        return 2
    v = Vault(root)

    if args.names:
        verdicts = check_names(v, args.names)
        if args.json:
            print(json.dumps([{"name": n, "status": s, "detail": d} for n, s, d in verdicts], indent=2))
        else:
            for name, status, detail in verdicts:
                print(f"{name}: {status}" + (f" - {detail}" if detail else ""))
        return 0 if all(s == "free" for _, s, _ in verdicts) else 1

    if args.new_sources:
        pending = new_sources(v)
        print(json.dumps(pending, indent=2) if args.json else ("\n".join(pending) or "none"))
        return 0

    findings, review = lint(v)
    if args.json:
        print(json.dumps({"vault": str(root), "pages": len(v.content_pages()),
                          "findings": findings, "review": review}, indent=2, ensure_ascii=False))
        return 1 if findings else 0

    print(f"Wiki lint: {root} ({len(v.content_pages())} content pages)")
    if findings:
        print(f"\nFindings ({len(findings)}):")
        for check, title in CHECK_TITLES.items():
            group = [f for f in findings if f["check"] == check]
            if group:
                print(f"\n  {title} ({len(group)})")
                for f in group:
                    where = f["path"] + (f":{f['line']}" if f["line"] else "")
                    print(f"    - {where}  {f['detail']}")
    else:
        print("\nNo findings: links, index, frontmatter, provenance markers and synthesis dates are consistent.")
    print("\nFor review (needs judgement):")
    for label, items in review.items():
        print(f"  {label}: " + (", ".join(items) if items else "none"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
