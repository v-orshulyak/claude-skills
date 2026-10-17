#!/bin/sh
# Launcher for wiki_hooks.py, called from .claude/settings.json as `sh .../run.sh <action>`.
# Finds a real Python 3.9+ (py, python3, python; skipping the Windows Store stub) and runs the
# hook with it. Without one the hooks stay quiet, except that the session start tells Claude,
# so the user hears about it once instead of seeing an error on every tool call.
# Runs under sh on macOS/Linux and Git Bash on Windows; uses no external commands.

here=${0%/*}
for name in py python3 python; do
  p=$(command -v "$name" 2>/dev/null) || continue
  case "$p" in *WindowsApps*) continue ;; esac
  if "$p" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
    exec "$p" "$here/wiki_hooks.py" "$@"
  fi
done

if [ "$1" = "session-start" ]; then
  echo "Wiki hooks are inactive: no Python 3.9+ found (tried py, python3, python). Tell the user once: install Python (TOOLS.md, Required) and restart Claude Code to get the raw/ guard, the session brief and the end-of-turn bookkeeping check. The lint, refactor and size scripts need it too."
fi
exit 0
