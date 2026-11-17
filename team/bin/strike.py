#!/usr/bin/env python3
"""Three-strikes counter for the agent team.

The CEO calls this after every failed review. It decides, so the rule
cannot be argued around:

  RETRY    same engineer tries again with the reviewer's notes
  REPLAN   a second failure of the same class (privacy, money, ...) in this
           cycle, or a third test defect: back to the planner to rethink
           the approach before more patching
  REWRITE  throw the attempt away; a brand-new engineer starts clean
  TESTFIX  a defect in the tests (fingerprint starts with "TESTS:"): the
           test writer fixes it; it doesn't count against the engineer
  BLOCKED  stop work on this task and tell the owner

Rules: the same failure 3 times in a cycle ends the cycle. The first
cycle ends in REWRITE, the second in BLOCKED. 6 engineer failures in total
on one task is BLOCKED whatever they were. Test defects are counted
separately; the third one asks for a replan.

Usage:
  python3 team/bin/strike.py record T3 "failing test + error" --class privacy
  python3 team/bin/strike.py record T3 "TESTS: 2 missing"
  python3 team/bin/strike.py status T3
  python3 team/bin/strike.py reopen T3   (only when the owner says so)
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "strikes.json"
SAME_FAILURE_LIMIT = 3
TOTAL_LIMIT = 6


def normalize(failure: str) -> str:
    """Reduce a failure to its essence so trivial differences don't hide a repeat."""
    text = failure.lower()
    text = re.sub(r"0x[0-9a-f]+", "0x#", text)
    text = re.sub(r"\d{4}-\d{2}-\d{2}([t ]\d{2}:\d{2}(:\d{2})?(\.\d+)?)?", "<time>", text)
    text = re.sub(r"\b\d{2}:\d{2}(:\d{2})?(\.\d+)?\b", "<time>", text)
    text = re.sub(r"(\.\w+):\d+", r"\1:#", text)
    text = re.sub(r"line \d+", "line #", text)
    text = re.sub(r"(/tmp|/var/folders)/\S+", "<tmp>", text)
    text = re.sub(r"\d+(\.\d+)?", "#", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:300]


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        sys.exit(f"strike.py: {path} is not valid JSON; fix or restore it before continuing.")


def _save(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def record(path: Path, task_id: str, failure: str, failure_class: str | None = None) -> str:
    data = _load(path)
    task = data.setdefault(
        task_id, {"cycle": 1, "total": 0, "state": "open", "counts": {}, "history": []}
    )
    task.setdefault("tests_total", 0)
    task.setdefault("classes", {})
    task.setdefault("replanned", [])
    if task["state"] == "blocked":
        return "BLOCKED"

    fingerprint = normalize(failure)
    is_test_defect = failure.strip().upper().startswith("TESTS:")
    cls = "tests" if is_test_defect else ((failure_class or "").strip().lower() or None)
    task["history"].append({"cycle": task["cycle"], "fingerprint": fingerprint, "class": cls})

    if is_test_defect:
        task["tests_total"] += 1
        verdict = "REPLAN" if task["tests_total"] == 3 else "TESTFIX"
        _save(path, data)
        return verdict

    task["total"] += 1
    task["counts"][fingerprint] = task["counts"].get(fingerprint, 0) + 1
    if cls:
        task["classes"][cls] = task["classes"].get(cls, 0) + 1

    if task["total"] >= TOTAL_LIMIT:
        verdict = "BLOCKED"
    elif task["counts"][fingerprint] >= SAME_FAILURE_LIMIT:
        verdict = "REWRITE" if task["cycle"] == 1 else "BLOCKED"
    elif cls and task["classes"][cls] == 2 and cls not in task["replanned"]:
        verdict = "REPLAN"
        task["replanned"].append(cls)
    else:
        verdict = "RETRY"

    if verdict == "REWRITE":
        task["cycle"] = 2
        task["counts"] = {}
        task["classes"] = {}
        task["replanned"] = []
    elif verdict == "BLOCKED":
        task["state"] = "blocked"

    _save(path, data)
    return verdict


def reopen(path: Path, task_id: str) -> None:
    """Owner unblocked the task: fresh counts, history kept."""
    data = _load(path)
    task = data.get(task_id)
    if task is None:
        sys.exit(f"strike.py: no record for {task_id}")
    task.update({"state": "open", "cycle": 1, "total": 0, "counts": {}, "classes": {}, "replanned": [], "tests_total": 0})
    _save(path, data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record")
    rec.add_argument("task_id")
    rec.add_argument("failure")
    rec.add_argument("--class", dest="failure_class", default=None,
                     help="privacy, money, tests, a11y, wording, data, security, layout or other")
    st = sub.add_parser("status")
    st.add_argument("task_id")
    ro = sub.add_parser("reopen", help="only after the owner says to retry a blocked task")
    ro.add_argument("task_id")
    args = parser.parse_args()

    if args.command == "record":
        print(record(args.file, args.task_id, args.failure, args.failure_class))
    elif args.command == "reopen":
        reopen(args.file, args.task_id)
        print("REOPENED")
    else:
        print(json.dumps(_load(args.file).get(args.task_id, {}), indent=2))


if __name__ == "__main__":
    main()
