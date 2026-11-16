#!/usr/bin/env python3
"""Claude Code PreToolUse hook: no agent may push to main or merge a pull request.

Pushing to main deploys the live app (e.g. Railway builds from main). Going live is the owner's
decision: the team opens a pull request and the owner merges it on GitHub.
Exit 2 blocks the tool call and tells Claude why.
"""
import json
import re
import sys

BLOCKED_TOOLS = {"mcp__github__merge_pull_request", "mcp__github__enable_pr_auto_merge"}


def is_blocked(command: str) -> bool:
    for part in re.split(r"&&|\|\||;|\n", command):
        words = part.split()
        if "git" not in words or "push" not in words[words.index("git"):]:
            continue
        args = words[words.index("push", words.index("git")) + 1:]
        if "--all" in args or "--mirror" in args:
            return True
        for arg in args:
            if arg.startswith("-"):
                continue
            target = arg.lstrip("+").split(":")[-1]
            if target in ("main", "refs/heads/main"):
                return True
    return False


def main() -> None:
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    command = event.get("tool_input", {}).get("command", "")
    if tool in BLOCKED_TOOLS or (tool == "Bash" and is_blocked(command)):
        print("Blocked: going live is the owner's decision. Open a pull request and park it "
              "under 'Waiting on owner'; the owner merges it on GitHub.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
