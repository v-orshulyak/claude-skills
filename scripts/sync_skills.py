#!/usr/bin/env python3
"""Copy every skill in this repo into the user's personal Claude skills folder.

The plugin marketplace caches plugins and refreshes them rarely, so this is the fast way to
get the current checkout into ~/.claude/skills (personal skills load in every project, no
install step). Stdlib only, Python 3.9+, runs on macOS, Linux and Windows.

  python3 scripts/sync_skills.py              # sync all plugins' skills
  python3 scripts/sync_skills.py --dry-run    # show what would change, touch nothing
  python3 scripts/sync_skills.py --prune      # also remove v-* skills no longer in the repo
  python3 scripts/sync_skills.py --dest DIR   # another target (default ~/.claude/skills)

Each skill folder is mirrored: new and changed files are copied, files the repo no longer has
are removed from that skill's folder. Other folders in the target (skills not from this repo)
are never touched; --prune only considers folders whose name starts with "v-".
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IGNORED = {"__pycache__", ".gitkeep", ".DS_Store"}


def source_skills() -> dict[str, Path]:
    skills: dict[str, Path] = {}
    for skill_md in sorted(REPO.glob("plugins/*/skills/*/SKILL.md")):
        folder = skill_md.parent
        if folder.name in skills:
            sys.exit(f"Duplicate skill name {folder.name!r}: {skills[folder.name]} and {folder}")
        skills[folder.name] = folder
    return skills


def files_of(root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if any(part in IGNORED for part in rel.parts) or p.suffix == ".pyc":
            continue
        if p.is_file():
            out[rel.as_posix()] = p
    return out


def sync_one(src: Path, dst: Path, dry: bool) -> tuple[int, int, int]:
    """Mirror src into dst. Returns (added, updated, removed)."""
    src_files, dst_files = files_of(src), files_of(dst) if dst.exists() else {}
    added = updated = removed = 0
    for rel, sp in src_files.items():
        dp = dst / rel
        if rel not in dst_files:
            added += 1
        elif not filecmp.cmp(sp, dp, shallow=False):
            updated += 1
        else:
            continue
        if not dry:
            dp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sp, dp)
    for rel in dst_files.keys() - src_files.keys():
        removed += 1
        if not dry:
            dst_files[rel].unlink()
    if not dry and dst.exists():  # drop folders left empty by removals
        for d in sorted((p for p in dst.rglob("*") if p.is_dir()), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()
    return added, updated, removed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dest", type=Path, default=Path.home() / ".claude" / "skills")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prune", action="store_true", help="remove v-* folders not in the repo")
    args = ap.parse_args()

    dest: Path = args.dest.expanduser()
    skills = source_skills()
    if not skills:
        sys.exit("No skills found under plugins/*/skills/*/SKILL.md")
    bad = [n for n in skills if not n.startswith("v-")]
    if bad:
        sys.exit(f"Skills without the v- prefix: {', '.join(bad)}")

    tag = "[dry run] " if args.dry_run else ""
    print(f"{tag}Syncing {len(skills)} skills from {REPO / 'plugins'} to {dest}")
    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    for name, src in skills.items():
        a, u, r = sync_one(src, dest / name, args.dry_run)
        status = "up to date" if not (a or u or r) else f"{a} added, {u} updated, {r} removed"
        print(f"  {name}: {status}")

    stale = sorted(p for p in dest.glob("v-*") if p.is_dir() and p.name not in skills) if dest.exists() else []
    for p in stale:
        if args.prune:
            print(f"  {p.name}: {'would remove' if args.dry_run else 'removed'} (not in the repo)")
            if not args.dry_run:
                shutil.rmtree(p)
        else:
            print(f"  {p.name}: not in the repo (use --prune to remove)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
