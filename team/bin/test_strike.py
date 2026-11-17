import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strike  # noqa: E402


class StrikeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "strikes.json"

    def tearDown(self):
        self.tmp.cleanup()

    def rec(self, failure, task="T1"):
        return strike.record(self.path, task, failure)

    def status(self, task="T1"):
        return json.loads(self.path.read_text())[task]

    def test_first_failure_retries(self):
        self.assertEqual(self.rec("boom"), "RETRY")

    def test_third_same_failure_rewrites(self):
        self.assertEqual([self.rec("boom") for _ in range(3)], ["RETRY", "RETRY", "REWRITE"])
        self.assertEqual(self.status()["cycle"], 2)
        self.assertEqual(self.status()["counts"], {})

    def test_rewrite_then_three_more_blocks(self):
        for _ in range(3):
            self.rec("boom")
        self.assertEqual([self.rec("boom") for _ in range(3)], ["RETRY", "RETRY", "BLOCKED"])

    def test_different_failures_do_not_strike(self):
        self.assertEqual([self.rec(f"error {c}") for c in "abcde"], ["RETRY"] * 5)

    def test_six_total_blocks(self):
        results = [self.rec(f"error {c}") for c in "abcdef"]
        self.assertEqual(results[-1], "BLOCKED")

    def test_normalizes_volatile_parts(self):
        a = strike.normalize("AssertionError at core/views.py:120 0x7f3a 2026-11-16 10:01:02")
        b = strike.normalize("assertionerror at core/views.py:98 0x11ab 2026-11-17 09:00:00")
        self.assertEqual(a, b)

    def test_blocked_is_terminal(self):
        for c in "abcdef":
            self.rec(f"error {c}")
        self.assertEqual(self.rec("anything new"), "BLOCKED")

    def test_tasks_are_counted_separately(self):
        self.rec("boom", "T1")
        self.rec("boom", "T1")
        self.assertEqual(self.rec("boom", "T2"), "RETRY")

    def test_missing_file_starts_fresh(self):
        self.assertFalse(self.path.exists())
        self.assertEqual(self.rec("boom"), "RETRY")
        self.assertEqual(self.status()["total"], 1)

    def test_corrupt_file_refuses(self):
        self.path.write_text("{not json")
        with self.assertRaises(SystemExit) as ctx:
            self.rec("boom")
        self.assertNotEqual(ctx.exception.code, 0)
        self.assertEqual(self.path.read_text(), "{not json")

    def test_normalizes_durations_ids_and_temp_dirs(self):
        a = strike.normalize("test_x (core.tests.T) AssertionError pk=41 in 3.214s /var/folders/ab/c1/x")
        b = strike.normalize("test_x (core.tests.T) AssertionError pk=7 in 0.5s /var/folders/zz/q9/y")
        self.assertEqual(a, b)

    def test_reopen_clears_block(self):
        for c in "abcdef":
            self.rec(f"error {c}")
        strike.reopen(self.path, "T1")
        self.assertEqual(self.status()["state"], "open")
        self.assertEqual(self.rec("boom"), "RETRY")
        self.assertEqual(len(self.status()["history"]), 7)

    # --- failure classes (2026-11-17 audit) ---
    def test_second_failure_of_the_same_class_asks_for_a_replan(self):
        self.assertEqual(strike.record(self.path, "T1", "objection: 3 masking a", "privacy"), "RETRY")
        self.assertEqual(strike.record(self.path, "T1", "objection: 3 something else", "privacy"), "REPLAN")

    def test_replan_happens_once_per_class_per_cycle(self):
        strike.record(self.path, "T1", "a", "privacy")
        strike.record(self.path, "T1", "b", "privacy")
        self.assertEqual(strike.record(self.path, "T1", "c", "privacy"), "RETRY")

    def test_different_classes_do_not_replan(self):
        strike.record(self.path, "T1", "a", "privacy")
        self.assertEqual(strike.record(self.path, "T1", "b", "money"), "RETRY")

    def test_same_fingerprint_three_times_still_rewrites_even_with_a_class(self):
        out = [strike.record(self.path, "T1", "same", "money") for _ in range(3)]
        self.assertEqual(out[-1], "REWRITE")

    def test_test_defects_do_not_count_toward_the_engineers_limits(self):
        for c in "abcde":
            strike.record(self.path, "T1", f"engineer {c}", c)  # 5 distinct classes
        self.assertEqual(strike.record(self.path, "T1", "TESTS: 1 wrong"), "TESTFIX")
        self.assertEqual(self.status()["total"], 5)

    def test_tests_prefix_sets_the_tests_class(self):
        self.assertEqual(strike.record(self.path, "T1", "TESTS: 2 missing"), "TESTFIX")
        self.assertEqual(self.status()["tests_total"], 1)

    def test_three_test_defects_ask_for_a_replan(self):
        self.assertEqual([strike.record(self.path, "T1", f"TESTS: {n} wrong") for n in "abc"], ["TESTFIX", "TESTFIX", "REPLAN"])

    def test_old_records_without_classes_still_load(self):
        self.path.write_text('{"T1": {"cycle": 1, "total": 1, "state": "open", "counts": {"x": 1}, "history": []}}')
        self.assertEqual(strike.record(self.path, "T1", "y"), "RETRY")


if __name__ == "__main__":
    unittest.main()
