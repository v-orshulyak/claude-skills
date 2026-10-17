#!/usr/bin/env python3
"""Scaffold an LLM-wiki Obsidian vault from ../assets/template.

Usage:
  scaffold.py --name "Project" --description "What it is" --dest ./project
  scaffold.py ... [--obsidian-from VAULT | --no-profile]   # default: bundled Obsidian profile
  scaffold.py --snapshot-profile VAULT   # maintainer: refresh the bundled profile
  scaffold.py --check ./project        # only run the self-check on a vault

Standard library only, works on macOS, Windows and Linux. Never overwrites files.
"""
import argparse
import datetime
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "template"
PROFILE = SKILL_DIR / "assets" / "obsidian-profile"  # bundled Obsidian settings, plugins and theme
TOKEN_RE = re.compile(r"__[A-Z][A-Z_]*__")
WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if not slug:
        slug = "wiki"
    if slug in WINDOWS_RESERVED:
        slug += "-wiki"
    return slug


def real_name(part: str) -> str:
    return "." + part[4:] if part.startswith("dot-") else part


def scaffold(dest: Path, tokens: dict) -> tuple[list, list]:
    created, skipped = [], []
    for src in sorted(TEMPLATE.rglob("*")):
        if src.is_dir():
            continue
        rel = Path(*[real_name(p) for p in src.relative_to(TEMPLATE).parts])
        target = dest / rel
        if target.exists():
            skipped.append(rel.as_posix())
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8")
        for key, value in tokens.items():
            text = text.replace(key, value)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        created.append(rel.as_posix())
    return created, skipped


# Settings the wiki rules depend on; they win over an imported vault's values.
REQUIRED_APP_KEYS = ("useMarkdownLinks", "newLinkFormat", "alwaysUpdateLinks",
                     "attachmentFolderPath", "newFileLocation", "newFileFolderPath")
REQUIRED_CORE_PLUGINS = ("file-explorer", "global-search", "graph", "backlink", "outgoing-link",
                         "properties", "templates", "bookmarks")
COPY_AS_IS = ("appearance.json", "community-plugins.json", "hotkeys.json", "types.json")
SECRET_KEY_RE = re.compile(r"api[_-]?key|token|secret|passw(or)?d|bearer|credential", re.I)


def has_secret(obj) -> bool:
    """True if any key that looks like a credential holds a non-empty string."""
    if isinstance(obj, dict):
        return any((SECRET_KEY_RE.search(k) and isinstance(v, str) and v.strip()) or has_secret(v)
                   for k, v in obj.items())
    if isinstance(obj, list):
        return any(has_secret(v) for v in obj)
    return False


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


PLUGIN_RUNTIME_FILES = ("main.js", "manifest.json", "styles.css")
# Plugin settings that describe the source vault's contents rather than preferences.
VAULT_DATA = {"obsidian-file-color": {"fileColors": []}, "colored-tags": {"knownTags": {}}}


def sanitize_plugin_data(plugin: str, data):
    """Blank vault-specific entries (path-keyed maps, tag caches) so settings travel without content."""
    if not isinstance(data, dict):
        return data
    data = {k: v for k, v in data.items() if "/" not in k and not k.endswith(".md")}
    data.update(VAULT_DATA.get(plugin, {}))
    return data


def snapshot_profile(source: Path, profile: Path) -> list:
    """Refresh the bundled profile from a vault's .obsidian (maintainer command)."""
    src = source / ".obsidian" if (source / ".obsidian").is_dir() else source
    report = []
    if profile.exists():
        shutil.rmtree(profile)
    profile.mkdir(parents=True)
    for name in ("app.json", "core-plugins.json", "graph.json", *COPY_AS_IS):
        if (src / name).is_file():
            shutil.copyfile(src / name, profile / name)
            report.append(name)
    theme = (read_json(src / "appearance.json") or {}).get("cssTheme")
    if theme and (src / "themes" / theme).is_dir():
        shutil.copytree(src / "themes" / theme, profile / "themes" / theme)
        report.append(f"theme {theme}")
    for plugin in read_json(src / "community-plugins.json") or []:
        pdir = src / "plugins" / plugin
        if not pdir.is_dir():
            report.append(f"plugin {plugin}: MISSING in source, not bundled")
            continue
        out = profile / "plugins" / plugin
        out.mkdir(parents=True)
        for fname in PLUGIN_RUNTIME_FILES:
            if (pdir / fname).is_file():
                shutil.copyfile(pdir / fname, out / fname)
        data = read_json(pdir / "data.json")
        if data is not None and has_secret(data):
            report.append(f"plugin {plugin}: data.json looks like it holds a credential, NOT bundled")
        elif data is not None:
            write_json(out / "data.json", sanitize_plugin_data(plugin, data))
        report.append(f"plugin {plugin}")
    return report


def import_obsidian(source: Path, dest: Path, created: set) -> list:
    """Reuse another vault's .obsidian settings, then re-assert what the wiki needs.

    Only files this run created are rewritten, so scaffolding into an existing vault never
    clobbers its settings. Workspace state, bookmarks and cache are never copied.
    """
    report = []
    src = source / ".obsidian" if (source / ".obsidian").is_dir() else source
    if not (src / "app.json").exists() and not (src / "community-plugins.json").exists():
        return [f"no Obsidian settings found at {src}; kept built-in defaults"]
    dst = dest / ".obsidian"
    dst.mkdir(parents=True, exist_ok=True)

    def ours(name):
        return f".obsidian/{name}" in created

    # app.json: user's values, except the keys the wiki rules need
    base, mine = read_json(dst / "app.json") or {}, read_json(src / "app.json") or {}
    if ours("app.json"):
        merged = {**base, **mine}
        for key in REQUIRED_APP_KEYS:
            if key in base:
                merged[key] = base[key]
        merged["userIgnoreFilters"] = sorted(set(mine.get("userIgnoreFilters", [])) | set(base.get("userIgnoreFilters", [])))
        write_json(dst / "app.json", merged)
        report.append("app.json merged (wiki-required keys forced)")

    # core-plugins.json: keep the user's choices, force the plugins the rules rely on
    mine_core = read_json(src / "core-plugins.json")
    if ours("core-plugins.json") and mine_core is not None:
        if isinstance(mine_core, dict):
            mine_core.update({name: True for name in REQUIRED_CORE_PLUGINS})
        else:
            mine_core = sorted(set(mine_core) | set(REQUIRED_CORE_PLUGINS))
        write_json(dst / "core-plugins.json", mine_core)
        report.append("core-plugins.json imported (required core plugins forced on)")

    # templates.json: keep user's formats, point at this vault's templates folder
    base_t, mine_t = read_json(dst / "templates.json") or {}, read_json(src / "templates.json") or {}
    if ours("templates.json"):
        write_json(dst / "templates.json", {**base_t, **mine_t, "folder": base_t.get("folder", "templates")})
        report.append("templates.json merged (folder stays 'templates')")

    # graph.json: user's physics and display, but this vault's filter and colour groups
    base_g, mine_g = read_json(dst / "graph.json") or {}, read_json(src / "graph.json")
    if ours("graph.json") and mine_g is not None:
        merged = {**base_g, **mine_g}
        merged["search"], merged["colorGroups"] = base_g.get("search", ""), base_g.get("colorGroups", [])
        write_json(dst / "graph.json", merged)
        report.append("graph.json imported (colour groups and filter stay wiki-specific)")

    for name in COPY_AS_IS:
        if (src / name).is_file() and not (dst / name).exists():
            shutil.copyfile(src / name, dst / name)
            report.append(f"{name} copied")

    # active theme only (themes are large)
    theme = (read_json(src / "appearance.json") or {}).get("cssTheme")
    if theme and (src / "themes" / theme).is_dir() and not (dst / "themes" / theme).exists():
        shutil.copytree(src / "themes" / theme, dst / "themes" / theme)
        report.append(f"theme '{theme}' copied")

    # enabled community plugins: code always, data.json only if it holds no credentials
    for plugin in read_json(src / "community-plugins.json") or []:
        pdir = src / "plugins" / plugin
        if not pdir.is_dir():
            report.append(f"plugin '{plugin}' is enabled but not installed in the source; skipped")
            continue
        if (dst / "plugins" / plugin).exists():
            continue
        data = read_json(pdir / "data.json")
        skip_data = data is not None and has_secret(data)
        out = dst / "plugins" / plugin
        out.mkdir(parents=True)
        for fname in PLUGIN_RUNTIME_FILES:
            if (pdir / fname).is_file():
                shutil.copyfile(pdir / fname, out / fname)
        if data is not None and not skip_data:
            write_json(out / "data.json", sanitize_plugin_data(plugin, data))
        report.append(f"plugin '{plugin}' copied" + (" WITHOUT data.json (looks like it holds a credential)" if skip_data else ""))
    return report


def strip_code(text: str) -> str:
    return INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))


def check(dest: Path) -> list:
    """Return a list of problems; empty means the vault is consistent."""
    problems = []
    md_files = [p for p in dest.rglob("*.md") if ".obsidian" not in p.parts and ".git" not in p.parts]
    stems = {}
    for p in md_files:
        stems.setdefault(p.stem.lower(), []).append(p.relative_to(dest).as_posix())
    for stem, paths in stems.items():
        if len(paths) > 1:
            problems.append(f"duplicate note name '{stem}': {', '.join(paths)}")
    def vault_file(p: Path) -> bool:
        return p.is_file() and ".obsidian" not in p.parts and ".git" not in p.parts

    all_names = {p.name.lower() for p in dest.rglob("*") if vault_file(p)} | set(stems)
    for p in [*dest.glob(".obsidian/*.json"), *(q for q in dest.rglob("*.json") if vault_file(q))]:
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except ValueError as exc:
            problems.append(f"invalid JSON {p.relative_to(dest).as_posix()}: {exc}")
    for p in md_files:
        rel = p.relative_to(dest).as_posix()
        text = p.read_text(encoding="utf-8")
        for token in sorted(set(TOKEN_RE.findall(text))):
            problems.append(f"unfilled token {token} in {rel}")
        if rel.startswith("templates/"):
            continue
        for target in sorted(set(WIKILINK_RE.findall(strip_code(text)))):
            name = target.strip().split("/")[-1].lower()
            if name not in all_names:
                problems.append(f"unresolved wikilink [[{target}]] in {rel}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", help="Project name")
    ap.add_argument("--description", default="", help="Short project description")
    ap.add_argument("--dest", help="Destination folder (default ./<slug>)")
    ap.add_argument("--obsidian-from", metavar="PATH",
                    help="Use this vault's .obsidian instead of the bundled profile")
    ap.add_argument("--no-profile", action="store_true",
                    help="Skip the bundled Obsidian profile; use the minimal built-in settings")
    ap.add_argument("--snapshot-profile", metavar="VAULT",
                    help="Maintainer: refresh the bundled profile from a vault's .obsidian")
    ap.add_argument("--check", metavar="VAULT", help="Only self-check an existing vault")
    args = ap.parse_args()

    if args.snapshot_profile:
        for line in snapshot_profile(Path(args.snapshot_profile).expanduser().resolve(), PROFILE):
            print(f"  - {line}")
        print(f"Bundled profile written to {PROFILE}")
        return 0

    if args.check:
        dest = Path(args.check).expanduser().resolve()
        problems = check(dest)
        print("\n".join(problems) if problems else f"OK: {dest} is consistent")
        return 1 if problems else 0

    if not args.name:
        ap.error("--name is required")
    if not TEMPLATE.is_dir():
        print(f"template not found at {TEMPLATE}", file=sys.stderr)
        return 2

    slug = slugify(args.name)
    dest = Path(args.dest).expanduser().resolve() if args.dest else (Path.cwd() / slug)
    dest.mkdir(parents=True, exist_ok=True)
    tokens = {
        "__PROJECT_NAME__": args.name.strip(),
        "__DESCRIPTION__": args.description.strip() or "(add a one-line description)",
        "__SLUG__": slug,
        "__DATE__": datetime.date.today().isoformat(),
    }
    created, skipped = scaffold(dest, tokens)
    print(f"Vault: {dest}")
    print(f"Created {len(created)} files" + (f", skipped {len(skipped)} existing" if skipped else ""))
    for rel in created:
        print(f"  created: {rel}")
    for rel in skipped:
        print(f"  skipped (exists): {rel}")
    source = Path(args.obsidian_from).expanduser().resolve() if args.obsidian_from else (
        PROFILE if PROFILE.is_dir() and not args.no_profile else None)
    if source:
        print(f"Obsidian settings from {'bundled profile' if source == PROFILE else source}:")
        for line in import_obsidian(source, dest, set(created)):
            print(f"  - {line}")
    problems = check(dest)
    if problems:
        print("Self-check found problems:")
        for prob in problems:
            print(f"  - {prob}")
        return 1
    print("Self-check OK: JSON valid, no unfilled tokens, all wikilinks resolve, note names unique")
    return 0


if __name__ == "__main__":
    sys.exit(main())
