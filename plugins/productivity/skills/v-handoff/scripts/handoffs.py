#!/usr/bin/env python3
"""List, find and place v-handoff files.

Usage:
    python3 handoffs.py list [--all] [--limit N]   # handoffs of this project (--all: every project)
    python3 handoffs.py find <id>                  # resolve an id, prefix or slug part to one path
    python3 handoffs.py path <slug> [--repo]       # path for a new handoff (creates the folder)

Handoffs live in ~/.claude/handoffs/<project>/ and, for the current repository,
in <repo root>/handoffs/. <project> is the basename of the main repository
(shared by all its worktrees), or of the working directory outside git.
An id is a file name without ".md", such as 2026-10-17-2226-v-retro-skill.
Stdlib only; runs on macOS, Linux and Windows.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

GLOBAL_ROOT = os.path.join(os.path.expanduser("~"), ".claude", "handoffs")


def git(*args):
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def repo_root():
    return git("rev-parse", "--show-toplevel")


def project_name():
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir")
    if common:
        return os.path.basename(os.path.dirname(os.path.normpath(common)))
    return os.path.basename(os.path.normpath(os.getcwd()))


def read_handoff(path):
    """Return the frontmatter dict plus 'goal', or None if the file is not a handoff."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read(8192)
    except OSError:
        return None
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return None
    meta = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    if meta.get("type") != "handoff":
        return None
    g = re.search(r"^# Handoff:\s*(.+)$", text, re.M)
    meta["goal"] = g.group(1).strip() if g else ""
    meta["id"] = os.path.splitext(os.path.basename(path))[0]
    meta["path"] = path
    return meta


def scan_dir(folder, project):
    found = []
    if not os.path.isdir(folder):
        return found
    for name in os.listdir(folder):
        if name.endswith(".md"):
            meta = read_handoff(os.path.join(folder, name))
            if meta:
                # The folder is the truth for where a handoff is listed; the
                # frontmatter may have been copied from another project.
                meta["project"] = project
                meta["where"] = "global" if os.path.normpath(folder).startswith(os.path.normpath(GLOBAL_ROOT)) else "repo"
                found.append(meta)
    return found


def collect(all_projects):
    project = project_name()
    handoffs = []
    if all_projects and os.path.isdir(GLOBAL_ROOT):
        for name in sorted(os.listdir(GLOBAL_ROOT)):
            handoffs += scan_dir(os.path.join(GLOBAL_ROOT, name), name)
    else:
        handoffs += scan_dir(os.path.join(GLOBAL_ROOT, project), project)
    root = repo_root()
    if root:
        handoffs += scan_dir(os.path.join(root, "handoffs"), project)
    # Ids start with a timestamp, so sorting by id is sorting by time.
    return sorted(handoffs, key=lambda h: h["id"], reverse=True)


def cmd_list(args):
    handoffs = collect(args.all)
    if not handoffs:
        scope = "any project" if args.all else f"project '{project_name()}'"
        print(f"No handoffs for {scope}. Looked in {GLOBAL_ROOT}" + ("" if args.all else f"{os.sep}{project_name()}") + " and <repo>/handoffs/.")
        return 0
    shown = handoffs[: args.limit]
    for h in shown:
        cols = [h["id"]]
        if args.all:
            cols.append(h.get("project", ""))
        cols += [h.get("status", "?"), h.get("branch", "-"), h["where"], h["goal"]]
        print("  ".join(cols))
    if len(handoffs) > len(shown):
        print(f"... {len(handoffs) - len(shown)} older not shown (--limit)")
    return 0


def match(handoffs, query):
    q = query.lower().removesuffix(".md")
    for test in (
        lambda h: h["id"].lower() == q,
        lambda h: h["id"].lower().startswith(q),
        lambda h: q in h["id"].lower() or q in h["goal"].lower(),
    ):
        hits = [h for h in handoffs if test(h)]
        if hits:
            return hits
    return []


def cmd_find(args):
    if os.path.isfile(args.id):
        meta = read_handoff(args.id)
        if meta:
            print(os.path.abspath(args.id))
            return 0
    hits = match(collect(False), args.id) or match(collect(True), args.id)
    if len(hits) == 1:
        print(hits[0]["path"])
        return 0
    if not hits:
        print(f"No handoff matches '{args.id}'. Run 'list --all' to see them.", file=sys.stderr)
        return 1
    print(f"'{args.id}' matches {len(hits)} handoffs; give more of the id:", file=sys.stderr)
    for h in hits[:20]:
        print(f"  {h['id']}  {h.get('project', '')}  {h['goal']}", file=sys.stderr)
    return 2


def cmd_path(args):
    if args.repo:
        root = repo_root()
        if not root:
            print("--repo needs a git repository; not inside one.", file=sys.stderr)
            return 1
        folder = os.path.join(root, "handoffs")
    else:
        folder = os.path.join(GLOBAL_ROOT, project_name())
    slug = re.sub(r"[^a-z0-9]+", "-", args.slug.lower()).strip("-") or "handoff"
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{stamp}-{slug}.md")
    n = 2
    while os.path.exists(path):
        path = os.path.join(folder, f"{stamp}-{slug}-{n}.md")
        n += 1
    print(path)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("list", help="list handoffs, newest first")
    pl.add_argument("--all", action="store_true", help="every project, not just this one")
    pl.add_argument("--limit", type=int, default=20)
    pf = sub.add_parser("find", help="resolve an id, prefix or slug part to a path")
    pf.add_argument("id")
    pp = sub.add_parser("path", help="print the path for a new handoff and create its folder")
    pp.add_argument("slug")
    pp.add_argument("--repo", action="store_true", help="<repo root>/handoffs/ instead of the global folder")
    args = p.parse_args()
    return {"list": cmd_list, "find": cmd_find, "path": cmd_path}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
