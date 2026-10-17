#!/usr/bin/env python3
"""Condense a Claude Code session transcript into a compact, evidence-rich digest.

Usage:
    python3 session_digest.py                 # current session
    python3 session_digest.py <session-id>    # another session (an unambiguous prefix is enough)
    python3 session_digest.py <path.jsonl>    # any transcript file
    python3 session_digest.py --list          # recent sessions of this project
    python3 session_digest.py --recent 10     # friction that recurs across the last 10 sessions

The current session is CLAUDE_CODE_SESSION_ID when set; otherwise the most
recently modified transcript of the project in the working directory (or of
its nearest parent directory that has transcripts).
Stdlib only; runs on macOS, Linux and Windows.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[abp]-[A-Za-z0-9-]{10,}"
    r"|AKIA[0-9A-Z]{16}|(?i:bearer)\s+[A-Za-z0-9._-]{20,}"
    r"|(?i:(?:password|passwd|secret|token|api[_-]?key)\s*[=:]\s*)\S{6,})"
)
RETRO_CMD = re.compile(r"^/(?:[\w-]+:)?v-retro\b")
SESSION_ID = re.compile(r"[0-9a-fA-F-]+")
# Tools whose "duration" or "permission" is the user thinking, not a cost.
USER_WAIT_TOOLS = {"AskUserQuestion", "ExitPlanMode", "EnterPlanMode"}
# Task-list and wrap-up calls are bookkeeping, not work: they are kept out of
# counts and repetition, and shown in the timeline only when they carry content.
BOOKKEEPING_RE = re.compile(r"(?:^|__)(?:update_plan|wrap_up)$|^(?:TodoWrite|Task(?:Create|Update|List|Get))$")
# Output lines that betray a failed shell command even when the call "succeeded"
# (e.g. a failing step early in a `;` chain whose last command exits 0).
# STRONG lines name the failing tool, so they rarely occur in file contents and
# are looked for anywhere. WEAK lines often do occur there (logs, source code),
# so they count only near the end of the output of a command that changes things.
# Indented lines are quoted output, not a shell's own message, so lines must
# start in the first column.
STRONG_FAIL = (r"(?:sed|awk|grep|zsh|bash|sh|\(eval\)|python3?|node|npm|git|cp|mv|rm|mkdir|cat|ls|cd)"
               r"(?::\s?\d+)?:\s.*|\S.*command not found.*")
WEAK_FAIL = (r"fatal: .*|error: .*|Traceback \(most recent call last\):"
             r"|\S.*No such file or directory.*|\S.*Permission denied.*")
STRONG_RE = re.compile(rf"(?m)^(?:{STRONG_FAIL})$")
WEAK_RE = re.compile(rf"(?m)^(?:{WEAK_FAIL})$")
WEAK_TAIL_LINES = 20
# Commands that only print things; their output is often file contents.
READ_ONLY = {"cat", "head", "tail", "grep", "egrep", "rg", "wc", "less", "echo", "printf", "cd",
             "ls", "find", "tree", "jq", "sort", "uniq", "cut", "diff", "stat", "file", "true"}
READ_ONLY_GIT = {"diff", "log", "show", "status", "blame", "grep"}


def redact(text):
    return SECRET_RE.sub("[REDACTED]", text)


def short(text, n):
    text = redact(" ".join(str(text).split()))
    return text if len(text) <= n else text[: n - 1] + "…"


def ends(text, n):
    """Like short(), but keeps the end as well: a shell error is usually the last line."""
    text = redact(" ".join(str(text).split()))
    if len(text) <= n:
        return text
    head = n // 3
    return f"{text[:head]} … {text[-(n - head - 3):]}"


def when(path):
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def newest_first(files):
    return sorted(files, key=lambda h: h.stat().st_mtime, reverse=True)


def project_dir(cwd):
    # Claude Code names a project folder after its path with every
    # non-alphanumeric character replaced by "-". Very long names are
    # shortened and given a hash suffix, so fall back to a prefix match.
    name = re.sub(r"[^A-Za-z0-9]", "-", str(cwd))
    exact = PROJECTS / name
    if exact.is_dir() or len(name) <= 200:
        return exact
    for hit in PROJECTS.glob(name[:100] + "*"):
        if name.startswith(hit.name.rsplit("-", 1)[0]):
            return hit
    return exact


def current_project():
    """This session's project folder, else that of the working directory or its nearest parent."""
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid:
        hits = list(PROJECTS.glob(f"*/{sid}.jsonl"))
        if hits:
            return hits[0].parent
    cwd = Path.cwd()
    for p in (cwd, *cwd.parents):
        d = project_dir(p)
        if any(d.glob("*.jsonl")):
            return d
    return None


def no_project():
    sys.exit(f"No transcripts for {Path.cwd()} or its parents under {PROJECTS}; "
             "pass a session id or a .jsonl path.")


def resolve(target):
    proj = current_project()
    if target:
        p = Path(target).expanduser()
        if p.is_file():
            return p
        if not SESSION_ID.fullmatch(target):
            sys.exit(f"{target!r} is neither a file nor a session id.")
        exact = list(PROJECTS.glob(f"*/{target}.jsonl"))
        if exact:
            return exact[0]
        # A prefix is looked up in this project first; across all projects a
        # short one easily matches several sessions, so never pick one silently.
        scopes = ([proj.glob(f"{target}*.jsonl")] if proj else []) + [PROJECTS.glob(f"*/{target}*.jsonl")]
        for hits in map(list, scopes):
            if len(hits) == 1:
                return hits[0]
            if hits:
                lines = "\n".join(f"  {h.stem}  {when(h)}  {h.parent.name}" for h in newest_first(hits)[:10])
                sys.exit(f"{target!r} matches {len(hits)} sessions; pass more of the id:\n{lines}")
        sys.exit(f"No transcript found for {target!r} under {PROJECTS}")
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid:
        hits = list(PROJECTS.glob(f"*/{sid}.jsonl"))
        if hits:
            return hits[0]
    if not proj:
        no_project()
    return newest_first(proj.glob("*.jsonl"))[0]


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone()
    except (AttributeError, ValueError):
        return None


def fmt_dur(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m"


def fmt_tok(n):
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.1f}k" if n >= 1e3 else str(n)


def plan_items(inp):
    return inp.get("items") or inp.get("todos") or []


def tool_arg(name, inp):
    """One short, human-meaningful argument for a tool call."""
    if not isinstance(inp, dict):
        return ""
    if name.endswith("wrap_up"):
        labels = [a.get("label") or a.get("action") or "" for a in inp.get("actions") or []]
        ask = inp.get("ask")
        return (f"ASK {ask} [{' | '.join(labels)}]" if ask else f"recap: {inp.get('recap', '')}")
    if plan_items(inp) and BOOKKEEPING_RE.search(name):
        return "plan: " + " → ".join(str(i.get("content", "")) for i in plan_items(inp) if isinstance(i, dict))
    if name == "AskUserQuestion":
        return " / ".join(
            f"{q.get('question')} [{' | '.join(o.get('label', '') for o in q.get('options') or [])}]"
            for q in inp.get("questions") or [])
    for key in ("command", "file_path", "path", "pattern", "url", "query",
                "skill", "description", "prompt", "notebook_path"):
        if inp.get(key):
            return str(inp[key])
    return json.dumps(inp, ensure_ascii=False)[:200]


def offered_answers(name, inp):
    """Button labels/messages a tool call offered, so a click can be told from typing."""
    out = set()
    if not isinstance(inp, dict):
        return out
    if name.endswith("wrap_up"):
        for a in inp.get("actions") or []:
            out.update(x for x in (a.get("label"), a.get("message")) if x)
    elif name == "AskUserQuestion":
        for q in inp.get("questions") or []:
            out.update(o.get("label") for o in q.get("options") or [] if o.get("label"))
    return {norm(x) for x in out}


def norm(text):
    return " ".join(str(text).lower().split()).rstrip(".!")


def result_text(content):
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    return str(content or "")


def user_text(content):
    """Visible text of a user message, or None when it is only tool results."""
    if isinstance(content, str):
        return content
    parts = [b.get("text", "") for b in content
             if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(parts) if parts else None


def clean_prompt(text):
    m = re.search(r"<command-name>(.*?)</command-name>", text, re.S)
    if m:
        args = re.search(r"<command-args>(.*?)</command-args>", text, re.S)
        return f"{m.group(1).strip()} {args.group(1).strip() if args else ''}".strip()
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    return text.strip()


def load(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def read_only(cmd):
    """True when every command of a shell line only prints, so its output may be file contents."""
    for seg in re.split(r"&&|\|\||[;|\n]", cmd):
        words = [w for w in seg.split() if not re.match(r"^\w+=", w)]
        if not words:
            continue
        w0 = os.path.basename(words[0])
        if (w0 in READ_ONLY or (w0 == "sed" and "-n" in words)
                or (w0 == "git" and len(words) > 1 and words[1] in READ_ONLY_GIT)):
            continue
        return False
    return True


def soft_failure(name, cmd, text):
    """The failure line of a Bash result that reports success, or None."""
    if name != "Bash" or not text:
        return None
    m = STRONG_RE.search(text)
    if not m and not read_only(cmd):
        m = WEAK_RE.search("\n".join(text.splitlines()[-WEAK_TAIL_LINES:]))
    return m.group(0) if m else None


def analyse(rows):
    s = {
        "models": Counter(), "tokens": defaultdict(Counter), "tools": Counter(), "book": 0,
        "errors": [], "soft": [], "calls": {}, "durations": [], "repeats": Counter(),
        "reads": Counter(), "changes": defaultdict(lambda: {"Write": 0, "Edit": 0, "turns": set()}),
        "permissions": [], "turns": [], "compactions": 0, "interrupts": 0,
        "skills": Counter(), "first": None, "last": None,
    }
    seen_msg = set()
    turn = None
    offered = set()
    for d in rows:
        ts = parse_ts(d.get("timestamp"))
        kind = d.get("type")
        if ts:
            s["first"] = s["first"] or ts
            s["last"] = ts
        if kind == "system" and d.get("subtype") == "compact_boundary":
            s["compactions"] += 1
        if kind == "assistant":
            if turn is not None and ts:
                turn["work_end"] = ts
            msg = d.get("message", {})
            mid = msg.get("id")
            model = msg.get("model", "?")
            if mid and mid not in seen_msg and model != "<synthetic>":
                seen_msg.add(mid)
                s["models"][model] += 1
                u = msg.get("usage") or {}
                t = s["tokens"][model]
                for k in ("input_tokens", "cache_creation_input_tokens",
                          "cache_read_input_tokens", "output_tokens"):
                    t[k] += u.get(k) or 0
            for b in msg.get("content") or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and b.get("text", "").strip():
                    if turn is not None:
                        turn["steps"].append({"kind": "say", "arg": b["text"]})
                    continue
                if b.get("type") != "tool_use":
                    continue
                name, inp = b.get("name", "?"), b.get("input") or {}
                arg = tool_arg(name, inp)
                offered |= offered_answers(name, inp)
                book = bool(BOOKKEEPING_RE.search(name))
                step = {"kind": "tool", "name": name, "arg": arg, "status": "ok", "book": book}
                s["calls"][b.get("id")] = (name, arg, ts, step)
                if book:
                    s["book"] += 1
                    # A plan or a question is context; a bare "advance" is not.
                    if turn is not None and (name.endswith("wrap_up") or plan_items(inp)):
                        turn["steps"].append(step)
                    continue
                s["tools"][name] += 1
                s["repeats"][(name, short(arg, 120), name + json.dumps(inp, sort_keys=True))] += 1
                if name == "Read":
                    s["reads"][inp.get("file_path", "?")] += 1
                if name in ("Write", "Edit", "NotebookEdit") and inp.get("file_path"):
                    c = s["changes"][inp["file_path"]]
                    c["Write" if name == "Write" else "Edit"] += 1
                    c["turns"].add(len(s["turns"]))
                if name == "Skill":
                    s["skills"][inp.get("skill", "?")] += 1
                if turn is not None:
                    turn["steps"].append(step)
        elif kind == "user":
            msg = d.get("message", {})
            content = msg.get("content")
            if d.get("isCompactSummary"):
                s["compactions"] += 1
                continue
            if d.get("isMeta"):
                continue
            prompted = False
            if "permissionDecision" in d:
                pdn = d["permissionDecision"] or {}
                src = str(pdn.get("source", ""))
                # The decision sits on the tool-result row, so the call's whole
                # duration includes the time the user took to answer the prompt.
                prompted = src.startswith("user") or src == "prompt"
                if pdn.get("decision") != "accept" or prompted:
                    s["permissions"].append((pdn.get("decision"), src, d.get("sourceToolAssistantUUID")))
            if isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict) or b.get("type") != "tool_result":
                        continue
                    if turn is not None and ts:
                        turn["work_end"] = ts
                    name, arg, called, step = s["calls"].get(b.get("tool_use_id"), ("?", "", None, None))
                    if called and ts:
                        secs = (ts - called).total_seconds()
                        waited = name in USER_WAIT_TOOLS or prompted
                        s["durations"].append((secs, name, arg, waited))
                        if waited and turn is not None:
                            turn["user_wait"] += secs
                    text = result_text(b.get("content"))
                    soft = None if b.get("is_error") else soft_failure(name, arg, text)
                    if b.get("is_error"):
                        s["errors"].append((name, arg, text))
                        if step:
                            step["status"] = "fail"
                    elif soft:
                        s["soft"].append((name, arg, soft))
                        if step:
                            step["status"] = "soft"
            text = user_text(content) if content is not None else None
            if text is None:
                continue
            if "[Request interrupted by user" in text:
                s["interrupts"] += 1
                if turn is not None:
                    turn["steps"].append({"kind": "interrupt", "arg": ""})
                continue
            cmd = re.search(r"<bash-input>(.*?)</bash-input>", text, re.S)
            if cmd:
                # A command the user ran themselves with "!": part of the
                # current turn, and often a sign Claude could not do it.
                if turn is not None:
                    turn["steps"].append({"kind": "user_cmd", "arg": cmd.group(1)})
                continue
            text = clean_prompt(text)
            if not text or text.startswith("<") and text.endswith(">"):
                continue
            turn = {"ts": ts, "work_end": ts, "user_wait": 0.0, "prompt": text,
                    "steps": [], "button": norm(text) in offered}
            offered = set()
            s["turns"].append(turn)
    # Permission rows point at the assistant message, not the tool id;
    # resolve them to the tool calls of that message for readability.
    by_uuid = {d.get("uuid"): d for d in rows if d.get("type") == "assistant"}
    perms = []
    for decision, src, auuid in s["permissions"]:
        a = by_uuid.get(auuid) or {}
        uses = [b for b in (a.get("message", {}).get("content") or [])
                if isinstance(b, dict) and b.get("type") == "tool_use"]
        if uses and all(u.get("name") in USER_WAIT_TOOLS for u in uses):
            continue
        what = ", ".join(f"{u.get('name')}: {short(tool_arg(u.get('name'), u.get('input')), 90)}"
                         for u in uses) or "?"
        perms.append((decision, src, what))
    s["permissions"] = perms
    s["working"] = sum(max((t["work_end"] - t["ts"]).total_seconds() - t["user_wait"], 0)
                       for t in s["turns"] if t["ts"] and t["work_end"])
    return s


def subagents(path):
    out = []
    folder = path.with_suffix("") / "subagents"
    for f in sorted(folder.glob("agent-*.jsonl")):
        meta = {}
        mf = f.with_name(f.stem + ".meta.json")
        if mf.exists():
            try:
                meta = json.loads(mf.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        a = analyse(load(f))
        tok = Counter()
        for c in a["tokens"].values():
            tok.update(c)
        dur = (a["last"] - a["first"]).total_seconds() if a["first"] and a["last"] else 0
        out.append((meta.get("description") or f.stem, meta.get("agentType", "?"),
                    ",".join(a["models"]) or "?", tok, sum(a["tools"].values()),
                    len(a["errors"]), dur))
    return out


def is_retro_turn(turn):
    return bool(RETRO_CMD.match(turn["prompt"]))


def report(path, s, subs, max_turns, max_tools, with_text):
    p = print
    first, last = s["first"], s["last"]
    dur = (last - first).total_seconds() if first and last else 0
    p(f"# Session digest: {path.stem}")
    p(f"file: {path}")
    p(f"span: {first:%Y-%m-%d %H:%M} → {last:%H:%M} local · {fmt_dur(dur)} wall clock · "
      f"~{fmt_dur(s['working'])} Claude working (prompt → last step, minus waits on questions "
      f"and permission prompts)" if first else "span: ?")
    buttons = sum(1 for t in s["turns"] if t["button"])
    p(f"user prompts: {len(s['turns'])} ({buttons} were button clicks) · tool calls: "
      f"{sum(s['tools'].values())} (+{s['book']} task-list/wrap-up) · errors: {len(s['errors'])} · "
      f"possible silent failures: {len(s['soft'])} · interrupts: {s['interrupts']} · "
      f"compactions: {s['compactions']}")
    p("\n## Tokens by model (main thread, deduplicated per API message; subagents listed separately)")
    for model, t in s["tokens"].items():
        p(f"- {model}: {s['models'][model]} msgs · in {fmt_tok(t['input_tokens'])} · "
          f"cache write {fmt_tok(t['cache_creation_input_tokens'])} · "
          f"cache read {fmt_tok(t['cache_read_input_tokens'])} · out {fmt_tok(t['output_tokens'])}")
    if subs:
        # Subagent transcripts log output tokens per streamed chunk, so their
        # "out" is far too low; cache reads and writes are logged correctly.
        p("\n## Subagents (out as logged, usually under-counted)")
        for desc, typ, model, tok, ntools, nerr, sdur in subs:
            p(f"- {short(desc, 70)} [{typ}, {model}] · out {fmt_tok(tok['output_tokens'])} · "
              f"cache read {fmt_tok(tok['cache_read_input_tokens'])} · in+cache write "
              f"{fmt_tok(tok['input_tokens'] + tok['cache_creation_input_tokens'])} · "
              f"{ntools} tools · {nerr} errors · {fmt_dur(sdur)}")
    p("\n## Tool usage")
    p(", ".join(f"{n}×{c}" for n, c in s["tools"].most_common()) or "none")
    if s["skills"]:
        p("skills invoked: " + ", ".join(f"{n}×{c}" for n, c in s["skills"].items()))
    if s["errors"]:
        p("\n## Failed tool calls (output start … end)")
        for name, arg, text in s["errors"][:25]:
            p(f"- {name}: {short(arg, 100)}\n    → {ends(text, 260)}")
        if len(s["errors"]) > 25:
            p(f"- … {len(s['errors']) - 25} more")
    if s["soft"]:
        p("\n## Possible silent failures (call succeeded, output shows an error)")
        for name, arg, line in s["soft"][:15]:
            p(f"- {name}: {short(arg, 100)}\n    → {short(line, 200)}")
    rework = [(f, c) for f, c in s["changes"].items() if c["Write"] > 1 or len(c["turns"]) > 1]
    if rework:
        p("\n## Files changed repeatedly (rework signal)")
        for f, c in sorted(rework, key=lambda x: -(x[1]["Write"] + x[1]["Edit"]))[:15]:
            p(f"- {f}: Write×{c['Write']} Edit×{c['Edit']} across {len(c['turns'])} prompt(s)")
    reps = [(k, c) for k, c in s["repeats"].items() if c > 1]
    rereads = [(f, c) for f, c in s["reads"].items() if c > 1]
    if reps or rereads:
        p("\n## Repetition")
        for (name, arg, _), c in sorted(reps, key=lambda x: -x[1])[:15]:
            p(f"- identical {name} ×{c}: {arg}")
        for f, c in sorted(rereads, key=lambda x: -x[1])[:10]:
            p(f"- Read ×{c}: {f}")
    if s["permissions"]:
        p("\n## Permission prompts / denials")
        for decision, src, what in s["permissions"][:20]:
            p(f"- {decision} ({src}): {what}")
    slow = sorted((x for x in s["durations"] if not x[3] and x[0] >= 20), key=lambda x: -x[0])[:8]
    if slow:
        p("\n## Slowest tool calls (call → result, waits on the user excluded)")
        for sec, name, arg, _ in slow:
            p(f"- {fmt_dur(sec)} {name}: {short(arg, 110)}")
    legend = ("· tool, ✗ failed, ? possible silent failure, ☰ plan or wrap-up, $ command you ran, "
              "⏸ you interrupted" + (", » Claude's text" if with_text else ""))
    p(f"\n## Timeline (user prompt → what followed; {legend})")
    turns = s["turns"]
    last_turn = turns[-1] if turns else None
    if len(turns) > max_turns:
        p(f"(showing first {max_turns // 2} and last {max_turns - max_turns // 2} of {len(turns)} "
          "prompts; rerun with a higher --max-turns, or grep the file above, for the rest)")
        turns = turns[: max_turns // 2] + [None] + turns[-(max_turns - max_turns // 2):]
    for t in turns:
        if t is None:
            p("\n…")
            continue
        flags = ("  [retro request]" if is_retro_turn(t) else "") + ("  [button click]" if t["button"] else "")
        stamp = f"{t['ts']:%H:%M}" if t["ts"] else "--:--"
        tools = [x for x in t["steps"] if x["kind"] == "tool" and not x["book"]]
        work = (t["work_end"] - t["ts"]).total_seconds() - t["user_wait"] if t["ts"] and t["work_end"] else 0
        # The opening prompt usually states the goal, so it gets more room.
        limit = 1500 if t is s["turns"][0] else 600
        p(f"\n[{stamp}] USER: {short(t['prompt'], limit)}{flags}")
        p(f"   ({len(tools)} tool calls, Claude worked {fmt_dur(max(work, 0))}"
          f"{', session ended' if t is last_turn else ''})")
        # Collapse only runs of successful tool calls; failures, plans and
        # Claude's text are the evidence a retro needs, so they are always shown.
        keep = set(range(len(tools))) if len(tools) <= max_tools else \
            set(range(max_tools - 5)) | set(range(len(tools) - 5, len(tools)))
        hidden, i = 0, 0
        for step in t["steps"]:
            if step["kind"] == "say":
                if not with_text:
                    continue
                visible, line = True, f"   » {short(step['arg'], 400)}"
            elif step["kind"] == "user_cmd":
                visible, line = True, f"   $ you ran: {short(step['arg'], 110)}"
            elif step["kind"] == "interrupt":
                visible, line = True, "   ⏸ you interrupted Claude here"
            elif step["book"]:
                mark = "✗" if step["status"] == "fail" else "☰"
                visible, line = True, f"   {mark} {short(step['arg'], 200)}"
            else:
                visible = i in keep or step["status"] != "ok"
                mark = {"ok": "·", "fail": "✗", "soft": "?"}[step["status"]]
                line = f"   {mark} {step['name']}: {short(step['arg'], 110)}"
                i += 1
            if not visible:
                hidden += 1
                continue
            if hidden:
                p(f"   … {hidden} more tool calls")
                hidden = 0
            p(line)
        if hidden:
            p(f"   … {hidden} more tool calls")


def first_prompt(rows):
    for d in rows:
        if d.get("type") == "user" and not d.get("isMeta"):
            t = user_text(d.get("message", {}).get("content") or "")
            if t and clean_prompt(t):
                return clean_prompt(t)
    return ""


def list_sessions():
    proj = current_project() or no_project()
    print(f"project: {proj}")
    for f in newest_first(proj.glob("*.jsonl"))[:15]:
        print(f"{f.stem}  {when(f)}  {short(first_prompt(load(f)), 90)}")


def last_line(text):
    lines = [x.strip() for x in re.sub(r"</?[\w-]+>", "", str(text)).splitlines() if x.strip()]
    return lines[-1] if lines else ""


def signature(name, line):
    """A failure line with paths and numbers blanked, so the same failure groups across sessions."""
    line = re.sub(r"(?:~|\.{0,2}/)[\w./@-]+", "<path>", redact(line))
    return f"{name}: {short(re.sub(r'[0-9a-f]{8,}|\d+', 'N', line), 120)}"


def recent(n):
    """Friction seen in more than one of the last n sessions: the evidence for 'will this recur?'."""
    proj = current_project() or no_project()
    files = newest_first(proj.glob("*.jsonl"))[:n]
    groups = {"Failed tool calls": defaultdict(list), "Possible silent failures": defaultdict(list),
              "Permission prompts / denials": defaultdict(list)}
    print(f"# Recurring friction across the last {len(files)} sessions\nproject: {proj}\n\n## Sessions")
    for f in files:
        s = analyse(load(f))
        sid = f.stem[:8]
        out = sum(c["output_tokens"] for c in s["tokens"].values())
        prompt = s["turns"][0]["prompt"] if s["turns"] else ""
        print(f"- {sid} {when(f)} · {len(s['turns'])} prompts · {sum(s['tools'].values())} tools · "
              f"{len(s['errors'])} failed (+{len(s['soft'])} silent) · ~{fmt_dur(s['working'])} working · "
              f"out {fmt_tok(out)} · {short(prompt, 70)}")
        for name, arg, text in s["errors"]:
            groups["Failed tool calls"][signature(name, last_line(text))].append((sid, arg))
        for name, arg, line in s["soft"]:
            groups["Possible silent failures"][signature(name, line)].append((sid, arg))
        for decision, src, what in s["permissions"]:
            name, _, arg = what.split(", ")[0].partition(": ")
            key = f"{decision} ({src}): {name}: {' '.join(arg.split()[:2])}"
            groups["Permission prompts / denials"][key].append((sid, arg))
    for title, group in groups.items():
        rec = sorted(((k, v) for k, v in group.items() if len({x for x, _ in v}) > 1),
                     key=lambda kv: -len(kv[1]))
        print(f"\n## {title} seen in 2+ sessions")
        for key, hits in rec[:15]:
            sids = sorted({x for x, _ in hits})
            print(f"- {len(hits)}× in {len(sids)} sessions ({', '.join(sids)}): {key}\n"
                  f"    e.g. {short(hits[0][1], 110)}")
        once = len(group) - len(rec)
        print(("none" if not rec else "") + (f" ({once} more seen in one session only)" if once else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="session id (unambiguous prefix ok) or transcript path")
    ap.add_argument("--list", action="store_true", help="list recent sessions of this project")
    ap.add_argument("--recent", type=int, metavar="N",
                    help="show friction that recurs across the last N sessions of this project")
    ap.add_argument("--max-turns", type=int, default=40, help="user prompts shown in the timeline")
    ap.add_argument("--max-tools", type=int, default=25,
                    help="tool calls shown per prompt (failures are always shown)")
    ap.add_argument("--with-text", action="store_true",
                    help="include assistant text in the timeline (useful for past sessions)")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.list:
        list_sessions()
        return
    if args.recent:
        recent(args.recent)
        return
    path = resolve(args.target)
    report(path, analyse(load(path)), subagents(path), args.max_turns, args.max_tools, args.with_text)


if __name__ == "__main__":
    main()
