#!/usr/bin/env bash
# Install or update the agent team in a project.
#   ./install.sh /path/to/project
# Always refreshes the agents, the playbook and the scripts (this repo is their source).
# Never overwrites a project's own state: team/*.md, CLAUDE.md, or an existing .claude/settings.json.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:?usage: ./install.sh /path/to/project}"
[ -d "$DEST/.git" ] || { echo "$DEST is not a git repository"; exit 1; }

mkdir -p "$DEST/.claude/agents" "$DEST/.claude/skills/run-project" "$DEST/team/bin"
cp "$KIT"/.claude/agents/*.md "$DEST/.claude/agents/"
cp "$KIT/.claude/skills/run-project/SKILL.md" "$DEST/.claude/skills/run-project/"
cp "$KIT"/team/bin/*.py "$DEST/team/bin/"
chmod +x "$DEST"/team/bin/strike.py "$DEST"/team/bin/check_tests_untouched.py "$DEST"/team/bin/block_main.py

mkdir -p "$DEST/team/plans"
[ -e "$DEST/team/plans/README.md" ] || cp "$KIT/team/plans/README.md" "$DEST/team/plans/README.md"
for f in BRIEF.md BOARD.md DECISIONS.md SPENDING.md README.md; do
  [ -e "$DEST/team/$f" ] || cp "$KIT/team/$f" "$DEST/team/$f"
done

if [ -e "$DEST/.claude/settings.json" ]; then
  if ! grep -q block_main.py "$DEST/.claude/settings.json"; then
    echo "NOTE: $DEST/.claude/settings.json exists; add the PreToolUse hook from $KIT/.claude/settings.json to it by hand."
  fi
else
  cp "$KIT/.claude/settings.json" "$DEST/.claude/settings.json"
fi

if [ -e "$DEST/CLAUDE.md" ]; then
  grep -q "team/BOARD.md" "$DEST/CLAUDE.md" || echo "NOTE: add the 'The agent team' section from $KIT/templates/CLAUDE.md to $DEST/CLAUDE.md."
else
  cp "$KIT/templates/CLAUDE.md" "$DEST/CLAUDE.md"
  echo "Created CLAUDE.md from the template; fill in the project details."
fi

(cd "$DEST" && python3 -m unittest discover -s team/bin -p "test_*.py" 2>&1 | tail -1)
echo "Installed. In a new Claude Code session in $DEST, say: run the team"
