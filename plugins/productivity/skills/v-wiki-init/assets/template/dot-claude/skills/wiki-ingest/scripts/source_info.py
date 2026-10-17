#!/usr/bin/env python3
"""Estimate how big a source is before ingesting it (run by the wiki-ingest skill).

Usage:
  python3 source_info.py raw/book.pdf          # size, verdict, outline if a tool can read it
  python3 source_info.py raw/book.pdf --json

Verdict:
  small   read it directly in the main conversation
  medium  one wiki-source-reader subagent reads the whole file
  large   survey first, then ingest in chapter-sized chunks with a reading map
          (.claude/skills/wiki-ingest/references/large-sources.md)

Page counts come from `pdfinfo` when installed, otherwise from the PDF's own page tree
(plain or inside compressed object streams). Word counts cover .md/.txt/.html/.docx/.epub.
Token figures are rough: about 600 per PDF page of text, 1.4 per word.
Reads only. Standard library only, Python 3.9+, macOS, Windows and Linux.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

SMALL_PAGES, LARGE_PAGES = 30, 100
SMALL_WORDS, LARGE_WORDS = 12_000, 50_000
TOKENS_PER_PAGE, TOKENS_PER_WORD = 600, 1.4
TEXT_EXT = {".md", ".markdown", ".txt", ".text", ".csv", ".srt", ".vtt", ".json"}
HTML_EXT = {".html", ".htm", ".xhtml"}

PAGES_COUNT_RE = re.compile(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)|/Count\s+(\d+)[^>]*?/Type\s*/Pages\b", re.S)
PAGE_RE = re.compile(rb"/Type\s*/Page\b(?!s)")
OBJSTM_RE = re.compile(rb"/Type\s*/ObjStm\b")
STREAM_RE = re.compile(rb"stream\r?\n")


def run(cmd: list) -> str | None:
    if not shutil.which(cmd[0]):
        return None
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60, errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def object_streams(data: bytes):
    """Decompressed contents of the PDF's object streams (where PDF 1.5+ hides the page tree)."""
    for m in OBJSTM_RE.finditer(data):
        start = STREAM_RE.search(data, m.end())
        if not start or start.start() - m.end() > 2000:
            continue
        end = data.find(b"endstream", start.end())
        if end < 0:
            continue
        try:
            yield zlib.decompress(data[start.end():end].rstrip(b"\r\n"))
        except zlib.error:
            continue


def pdf_pages(path: Path) -> tuple:
    """(page count or None, how it was found)."""
    info = run(["pdfinfo", str(path)])
    if info:
        m = re.search(r"^Pages:\s+(\d+)", info, re.M)
        if m:
            return int(m.group(1)), "pdfinfo"
    data = path.read_bytes()
    chunks = [data, *object_streams(data)]
    counts = [int(a or b) for chunk in chunks for a, b in PAGES_COUNT_RE.findall(chunk)]
    if counts:
        return max(counts), "page tree"
    pages = sum(len(PAGE_RE.findall(chunk)) for chunk in chunks)
    return (pages, "page objects") if pages else (None, "unreadable")


def pdf_outline(path: Path) -> list:
    """Bookmark outline via mutool, if installed (titles with their pages)."""
    out = run(["mutool", "show", str(path), "outline"])
    return [line.rstrip() for line in out.splitlines() if line.strip()][:200] if out else []


def strip_tags(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def words_of(path: Path) -> int | None:
    ext = path.suffix.lower()
    try:
        if ext in TEXT_EXT:
            return len(path.read_text(encoding="utf-8", errors="replace").split())
        if ext in HTML_EXT:
            return len(strip_tags(path.read_text(encoding="utf-8", errors="replace")).split())
        if ext in (".docx", ".epub"):
            with zipfile.ZipFile(path) as z:
                names = (["word/document.xml"] if ext == ".docx" else
                         [n for n in z.namelist() if n.lower().endswith((".xhtml", ".html", ".htm"))])
                return sum(len(strip_tags(z.read(n).decode("utf-8", "replace")).split())
                           for n in names if n in z.namelist())
    except (OSError, zipfile.BadZipFile, KeyError):
        return None
    return None


def verdict(pages, words) -> str:
    if pages is not None:
        return "small" if pages <= SMALL_PAGES else "large" if pages >= LARGE_PAGES else "medium"
    if words is not None:
        return "small" if words <= SMALL_WORDS else "large" if words >= LARGE_WORDS else "medium"
    return "unknown"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    path = Path(args.file).expanduser()
    if not path.is_file():
        print(f"not a file: {path}", file=sys.stderr)
        return 2

    pages = words = None
    how, outline = "", []
    if path.suffix.lower() == ".pdf":
        pages, how = pdf_pages(path)
        outline = pdf_outline(path)
    else:
        words = words_of(path)
        how = "word count" if words is not None else "unsupported format"
    tokens = (pages * TOKENS_PER_PAGE if pages is not None else
              int(words * TOKENS_PER_WORD) if words is not None else None)
    result = {"file": path.as_posix(), "bytes": path.stat().st_size, "pages": pages, "words": words,
              "estimated_tokens": tokens, "counted_by": how, "verdict": verdict(pages, words),
              "outline": outline}

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    size = f"{pages} pages" if pages is not None else f"{words} words" if words is not None else "size unknown"
    print(f"{path.name}: {size}, ~{tokens or '?'} tokens ({how}), {result['bytes'] // 1024} KB")
    print(f"verdict: {result['verdict']}")
    if result["verdict"] == "unknown":
        print("  could not measure it; open the first pages to judge, or convert it (TOOLS.md)")
    if path.suffix.lower() == ".pdf":
        if outline:
            print("outline (mutool):")
            for line in outline:
                print(f"  {line}")
        else:
            print("outline: none read (no bookmarks, or mutool not installed); use the table of contents pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
