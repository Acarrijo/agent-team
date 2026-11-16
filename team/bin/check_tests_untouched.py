#!/usr/bin/env python3
"""Guard the line between test writer and engineers.

Engineer check (default): fail if any test file or team-rule file changed
since REF (committed or not). Engineers may not touch tests, the team's
scripts and state (team/), the agent and playbook files (.claude/),
CLAUDE.md, or conftest.py.

Test-writer check (--tests-only): fail if anything other than test files
changed since REF.

Usage:
  python3 team/bin/check_tests_untouched.py TESTS_REF
  python3 team/bin/check_tests_untouched.py --tests-only BASE_REF
Exit 0 and print OK when clean; exit 1 and list the files otherwise.
"""
import subprocess
import sys
from pathlib import Path, PurePosixPath


def is_test_path(path: str) -> bool:
    p = PurePosixPath(path)
    name = p.name
    if name == "tests.py" or (name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))):
        return True
    return "tests" in p.parts[:-1]


def is_protected_path(path: str) -> bool:
    p = PurePosixPath(path)
    return (
        is_test_path(path)
        or p.parts[0] in ("team", ".claude")
        or path == "CLAUDE.md"
        or p.name == "conftest.py"
    )


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
    ).stdout


def _changed(base: str, repo: Path) -> set[str]:
    paths = set()
    fields = _git(repo, "diff", "-z", "--name-status", "-M", base).split("\0")
    i = 0
    while i < len(fields) and fields[i]:
        status = fields[i]
        count = 2 if status[0] in "RC" else 1
        paths.update(fields[i + 1:i + 1 + count])
        i += 1 + count
    paths.update(p for p in _git(repo, "ls-files", "-z", "--others", "--exclude-standard").split("\0") if p)
    return paths


def changed_test_files(base: str, repo: Path) -> list[str]:
    """Protected files (tests and team rules) changed since base."""
    return sorted(p for p in _changed(base, repo) if is_protected_path(p))


def changed_non_test_files(base: str, repo: Path) -> list[str]:
    return sorted(p for p in _changed(base, repo) if not is_test_path(p))


def main() -> None:
    args = sys.argv[1:]
    tests_only = args[:1] == ["--tests-only"]
    if tests_only:
        args = args[1:]
    if len(args) != 1:
        sys.exit(__doc__)
    try:
        if tests_only:
            changed, label = changed_non_test_files(args[0], Path.cwd()), "Non-test files changed (test writer may only touch tests):"
        else:
            changed, label = changed_test_files(args[0], Path.cwd()), "Test or team-rule files changed (not allowed for engineers):"
    except subprocess.CalledProcessError as e:
        sys.exit(f"check_tests_untouched.py: git failed for ref {args[0]!r}: {e.stderr.strip()}")
    if changed:
        print(label)
        for path in changed:
            print(f"  {path}")
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
