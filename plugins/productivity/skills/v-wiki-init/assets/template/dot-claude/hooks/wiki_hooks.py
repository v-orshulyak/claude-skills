#!/usr/bin/env python3
"""Claude Code hooks for this LLM wiki (wired up in .claude/settings.json).

  wiki_hooks.py session-start  # SessionStart: recent log entries and pending work as context
  wiki_hooks.py prompt         # UserPromptSubmit: remember the state of wiki/ and synthesis/
  wiki_hooks.py guard          # PreToolUse: keep raw/ immutable, pre-approve the wiki scripts
  wiki_hooks.py stop           # Stop: wiki changed this turn -> log, updated: and lint are current

Started through run.sh, which finds a Python 3.9+. Reads the hook event as JSON on stdin and answers in the JSON Claude Code expects. The hooks
back up the rules in CLAUDE.md; agents without hooks still follow the rules from there.
Any crash exits 1 (a non-blocking hook error), so a bug here never locks the user out.
Standard library only, Python 3.9+, macOS, Windows (Git Bash) and Linux.
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VAULT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or HERE.parent.parent).resolve()
RAW = VAULT / "raw"
LINT_PY = HERE.parent / "skills" / "wiki-lint" / "scripts" / "lint.py"
TRACKED = ("wiki", "synthesis")
LOG = "wiki/log.md"
# lint checks that are not about the page just edited, or are allowed to stay
NOT_BLOCKING = {"unsourced", "stale-synthesis"}


def load_lint():
    spec = importlib.util.spec_from_file_location("wiki_lint", LINT_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def emit(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False))


# ---------------------------------------------------------------- session start

def session_start(event: dict) -> int:
    lint = load_lint()
    if not (VAULT / "wiki").is_dir():
        return 0
    v = lint.Vault(VAULT)
    log = v.notes.get(LOG, {}).get("text", "")
    heads = [line[3:].strip() for line in log.splitlines() if lint.LOG_ENTRY_RE.match(line)]
    pending = lint.new_sources(v)
    since = lint.ingests_since_lint(v)
    lines = [f"Wiki status ({len(v.content_pages())} content pages). Read wiki/index.md before answering "
             "questions about the domain."]
    if heads:
        lines.append("Recent log entries: " + "; ".join(heads[-5:]))
    if pending:
        shown = ", ".join(pending[:5]) + (f" and {len(pending) - 5} more" if len(pending) > 5 else "")
        lines.append(f"Raw files not ingested yet ({len(pending)}): {shown}. Mention them if relevant.")
    partial = lint.partial_sources(v)
    if partial:
        lines.append("Large sources ingested in part (resume with wiki-ingest): " + ", ".join(
            f"{Path(rel).stem} ({done} done, {skipped} skipped, {total - done - skipped} left)" for rel, done, skipped, total in partial))
    if since >= 10:
        lines.append(f"{since} ingests since the last lint: suggest a health check (wiki-lint).")
    snapshot(event)
    emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(lines)}})
    return 0


# ---------------------------------------------------------------- change tracking

LINK_TARGET_RE = re.compile(r"(\[\[)[^\]\|#]*")
UPDATED_RE = re.compile(r"^(updated|generated)\s*:.*$", re.M)


def content_hash(text: str) -> str:
    """Hash that ignores link targets and the date fields, so a pure rename or link rewrite
    (wiki-refactor) doesn't count as a content change that needs an `updated:` bump."""
    text = UPDATED_RE.sub("", LINK_TARGET_RE.sub(r"\1", text))
    return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()


def scan() -> dict:
    out = {}
    for top in TRACKED:
        for root, dirs, files in os.walk(VAULT / top):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in files:
                if name.startswith("."):
                    continue
                p = Path(root) / name
                rel = p.relative_to(VAULT).as_posix()
                st = p.stat()
                entry = {"m": st.st_mtime_ns, "s": st.st_size}
                if name.endswith(".md"):
                    entry["h"] = content_hash(p.read_text(encoding="utf-8", errors="replace"))
                out[rel] = entry
    return out


def log_entries() -> int:
    try:
        text = (VAULT / LOG).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return len(re.findall(r"^## \[\d{4}-\d{2}-\d{2}\] \w+ \|", text, re.M))


def state_file(event: dict) -> Path:
    """Per machine and session, in the temp folder: never inside the vault, which OneDrive,
    iCloud or Dropbox would sync (and turn into conflict copies)."""
    vault = hashlib.sha1(str(VAULT).encode("utf-8")).hexdigest()[:12]
    session = re.sub(r"[^A-Za-z0-9-]", "", str(event.get("session_id") or "default"))[:64]
    return Path(tempfile.gettempdir()) / f"claude-wiki-{vault}-{session}.json"


def snapshot(event: dict) -> None:
    try:
        state_file(event).write_text(json.dumps({"files": scan(), "log_entries": log_entries()}), encoding="utf-8")
    except OSError:
        pass


def prompt(event: dict) -> int:
    snapshot(event)
    return 0


def stop(event: dict) -> int:
    if event.get("stop_hook_active"):
        return 0  # already sent back once this turn; don't loop
    try:
        state = json.loads(state_file(event).read_text(encoding="utf-8"))
        before, entries_before = state["files"], state.get("log_entries", 0)
    except (OSError, ValueError, KeyError):
        return 0
    now = scan()
    changed = sorted(rel for rel, e in now.items() if before.get(rel, {}).get("m") != e["m"]
                     or before.get(rel, {}).get("s") != e["s"])
    deleted = sorted(set(before) - set(now))
    if not [rel for rel in changed + deleted if rel != LOG]:
        return 0

    issues = []
    if log_entries() <= entries_before:
        issues.append(f"wiki/ or synthesis/ changed but {LOG} has no new entry: append "
                      "`## [YYYY-MM-DD] <op> | <title>` listing the pages created and updated.")

    lint = load_lint()
    today = datetime.date.today().isoformat()
    gone_hashes = {before[rel].get("h") for rel in deleted}
    stale_dates = []
    for rel in changed:
        if not rel.endswith(".md") or rel == LOG:
            continue
        old_hash, new_hash = before.get(rel, {}).get("h"), now[rel].get("h")
        if old_hash == new_hash or (old_hash is None and new_hash in gone_hashes):
            continue  # only link targets changed, or a renamed page
        fm = lint.frontmatter((VAULT / rel).read_text(encoding="utf-8", errors="replace")) or {}
        key = "generated" if "generated" in fm else "updated"
        if key in fm and str(fm.get(key)) != today:
            stale_dates.append(f"{rel} ({key}: {fm.get(key) or 'empty'})")
    if stale_dates:
        issues.append(f"Content changed but the date was not set to {today}: " + ", ".join(stale_dates))

    v = lint.Vault(VAULT)
    findings, _ = lint.lint(v)
    scope = set(changed)
    gone = {Path(rel).stem.lower() for rel in deleted}
    findings = [f for f in findings if f["check"] not in NOT_BLOCKING and (
        f in lint.scoped([f], scope)
        or (f["check"] == "unresolved" and lint.link_key(f["detail"].strip("[]")) in gone))]
    for f in findings[:15]:
        where = f["path"] + (f":{f['line']}" if f["line"] else "")
        issues.append(f"lint {f['check']}: {where} {f['detail']}")
    if len(findings) > 15:
        issues.append(f"... and {len(findings) - 15} more (run lint.py --files on the changed pages)")
    if not issues:
        return 0
    emit({"decision": "block", "reason":
          "Wiki bookkeeping check (Stop hook) on the pages changed this turn:\n- " + "\n- ".join(issues)
          + "\nFix these before finishing. If you are pausing mid-workflow to ask the user something, "
            "say so briefly and stop again; this check runs once per turn."})
    return 0


# ---------------------------------------------------------------- guard

DESTRUCTIVE = {"rm", "rmdir", "unlink", "shred", "truncate", "rename", "srm",
               "remove-item", "rename-item", "del", "erase", "ren", "ri"}
MOVERS = {"mv", "move-item", "move", "mi"}  # moving a file *into* raw/ adds a source, which is fine
IN_PLACE = {"sed", "gsed", "perl", "ruby"}
COPIERS = {"cp", "rsync", "install", "ln", "ditto", "copy-item", "copy"}
WRAPPERS = {"sudo", "command", "builtin", "nohup", "time", "nice", "env", "exec", "doas"}
SEPARATORS = {"&&", "||", ";", "|", "&", "\n", "(", ")", "|&", ";;"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}


def under_raw(token: str, cwd: Path) -> Path | None:
    token = token.strip().strip("'\"")
    if not token or token.startswith("-") or "://" in token:
        return None
    p = Path(os.path.expanduser(token))
    p = (p if p.is_absolute() else cwd / p).resolve()
    try:
        p.relative_to(RAW.resolve())
    except ValueError:
        return None
    return p


def exists_or_glob(p: Path) -> bool:
    return p.exists() or any(ch in p.name for ch in "*?[")


def bash_violation(command: str, cwd: Path) -> str | None:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None
    segments, cur = [], []
    for t in tokens:
        if t in SEPARATORS:
            segments.append(cur)
            cur = []
        else:
            cur.append(t)
    segments.append(cur)

    for seg in segments:
        words = []
        i = 0
        while i < len(seg):
            t = seg[i]
            if t in REDIRECTS or re.fullmatch(r"\d?>>?", t):
                target = seg[i + 1] if i + 1 < len(seg) else ""
                p = under_raw(target, cwd)
                if p and exists_or_glob(p):
                    return f"redirects output into existing {p.relative_to(VAULT).as_posix()}"
                i += 2
                continue
            words.append(t)
            i += 1
        while words and (words[0].lower() in WRAPPERS or re.fullmatch(r"\w+=.*", words[0])):
            words = words[1:]
        if not words:
            continue
        verb = Path(words[0]).name.lower()
        args = words[1:]
        raw_args = [p for p in (under_raw(a, cwd) for a in args) if p]
        if not raw_args:
            continue
        if verb in DESTRUCTIVE:
            return f"`{verb}` on a path in raw/"
        if verb == "git" and args and args[0] in {"rm", "mv", "clean", "checkout", "restore", "reset"}:
            return f"`git {args[0]}` on a path in raw/"
        if verb in IN_PLACE and any(a == "-i" or a.startswith(("-i", "--in-place")) or
                                    (a.startswith("-") and not a.startswith("--") and "i" in a)
                                    for a in args):
            return f"in-place `{verb}` on a file in raw/"
        if verb == "find" and ("-delete" in args or "rm" in args or "mv" in args):
            return "`find` that deletes or moves files in raw/"
        if verb in ("tee", "touch") and any(exists_or_glob(p) for p in raw_args):
            return f"`{verb}` on an existing file in raw/"
        if verb in ("curl", "wget"):
            for flag in ("-o", "--output", "-O", "--output-document"):
                if flag in args and args.index(flag) + 1 < len(args):
                    p = under_raw(args[args.index(flag) + 1], cwd)
                    if p and exists_or_glob(p):
                        return f"download overwrites existing {p.relative_to(VAULT).as_posix()}"
        if verb in MOVERS:
            positional = [a for a in args if not a.startswith("-")]
            if any(under_raw(a, cwd) for a in positional[:-1]):
                return f"`{verb}` of a file out of raw/"
        if verb in COPIERS or verb in MOVERS:
            positional = [a for a in args if not a.startswith("-")]
            if len(positional) >= 2:
                dest = under_raw(positional[-1], cwd)
                if dest:
                    if dest.is_dir():
                        hits = [dest / Path(s).name for s in positional[:-1] if (dest / Path(s).name).exists()]
                    else:
                        hits = [dest] if exists_or_glob(dest) else []
                    if hits:
                        return f"`{verb}` overwrites existing {hits[0].relative_to(VAULT).as_posix()}"
    return None


SCRIPT_RE = re.compile(r"""^\s*(?:py(?:\s+-3)?|python3?|python)\s+("[^"]+"|'[^']+'|\S+)(\s+[^;&|<>`$()]*)?\s*$""")


def is_wiki_script(command: str, cwd: Path) -> bool:
    """`python3 <vault>/.claude/skills/wiki-*/scripts/<x>.py ...` with no shell operators."""
    m = SCRIPT_RE.match(command)
    if not m:
        return False
    script = Path(os.path.expanduser(m.group(1).strip("'\"")))
    script = (script if script.is_absolute() else cwd / script).resolve()
    skills = (VAULT / ".claude" / "skills").resolve()
    try:
        rel = script.relative_to(skills)
    except ValueError:
        return False
    return (len(rel.parts) == 3 and rel.parts[0].startswith("wiki-") and rel.parts[1] == "scripts"
            and rel.suffix == ".py" and script.is_file())


def deny(reason: str) -> int:
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                 "permissionDecisionReason": reason}})
    return 0


RAW_RULE = ("raw/ is the human's immutable source layer: new files may be added (wiki-capture), "
            "but existing ones are never edited, overwritten, moved or deleted. Keep derived files "
            "in a scratch folder outside the vault. If a raw file really must change, ask the user to do it.")


def guard(event: dict) -> int:
    tool = event.get("tool_name", "")
    data = event.get("tool_input") or {}
    cwd = Path(event.get("cwd") or VAULT)
    if tool == "Bash":
        command = data.get("command", "")
        problem = bash_violation(command, cwd)
        if problem:
            return deny(f"Blocked: {problem}. {RAW_RULE}")
        if is_wiki_script(command, cwd):
            emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                         "permissionDecisionReason": "wiki skill script"}})
        return 0
    path = data.get("file_path") or data.get("notebook_path")
    if not path:
        return 0
    p = under_raw(path, cwd)
    if not p:
        return 0
    if tool == "Write" and not p.exists():
        return 0  # adding a new source is fine
    return deny(f"Blocked: {tool} on {p.relative_to(VAULT).as_posix()}. {RAW_RULE}")


def main() -> int:
    actions = {"session-start": session_start, "prompt": prompt, "guard": guard, "stop": stop}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        print(f"usage: wiki_hooks.py {{{'|'.join(actions)}}}", file=sys.stderr)
        return 1
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        event = {}
    try:
        return actions[sys.argv[1]](event)
    except Exception as exc:  # never block the session because of a bug here
        print(f"wiki_hooks {sys.argv[1]}: {exc!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
