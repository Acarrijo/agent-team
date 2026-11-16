import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_tests_untouched import changed_non_test_files, changed_test_files, is_protected_path, is_test_path  # noqa: E402


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        self.write("core/views.py", "a = 1\n")
        self.write("core/tests.py", "t = 1\n")
        self.write("app/tests/test_a.py", "x = 1\n")
        self.commit()
        self.base = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def commit(self):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "c")

    def test_clean_change_passes(self):
        self.write("core/views.py", "a = 2\n")
        self.commit()
        self.assertEqual(changed_test_files(self.base, self.repo), [])

    def test_edited_test_fails(self):
        self.write("core/tests.py", "t = 2\n")
        self.commit()
        self.assertEqual(changed_test_files(self.base, self.repo), ["core/tests.py"])

    def test_uncommitted_test_edit_fails(self):
        self.write("core/tests.py", "t = 3\n")
        self.assertEqual(changed_test_files(self.base, self.repo), ["core/tests.py"])

    def test_new_untracked_test_file_fails(self):
        self.write("core/test_new.py", "n = 1\n")
        self.assertEqual(changed_test_files(self.base, self.repo), ["core/test_new.py"])

    def test_deleted_and_renamed_tests_count(self):
        (self.repo / "core/tests.py").unlink()
        git(self.repo, "mv", "app/tests/test_a.py", "app/tests/test_b.py")
        self.commit()
        self.assertEqual(
            changed_test_files(self.base, self.repo),
            ["app/tests/test_a.py", "app/tests/test_b.py", "core/tests.py"],
        )

    def test_is_test_path(self):
        for p in ["core/tests.py", "x/test_y.py", "x/y_test.py", "a/tests/helpers.py"]:
            self.assertTrue(is_test_path(p), p)
        for p in ["core/views.py", "team/bin/strike.py", "contests.py"]:
            self.assertFalse(is_test_path(p), p)

    def test_rule_files_are_protected(self):
        for p in ["team/strikes.json", "team/bin/strike.py", ".claude/agents/reviewer.md", "CLAUDE.md", "conftest.py", "core/conftest.py"]:
            self.assertTrue(is_protected_path(p), p)
        self.assertFalse(is_protected_path("core/views.py"))

    def test_engineer_editing_team_rules_fails(self):
        self.write("team/strikes.json", "{}")
        self.commit()
        self.assertEqual(changed_test_files(self.base, self.repo), ["team/strikes.json"])

    def test_non_ascii_test_name_caught(self):
        self.write("core/test_\u00e9.py", "e = 1\n")
        self.commit()
        self.assertEqual(changed_test_files(self.base, self.repo), ["core/test_\u00e9.py"])

    def test_test_writer_touching_code_caught(self):
        self.write("core/tests.py", "t = 9\n")
        self.write("core/views.py", "a = 9\n")
        self.commit()
        self.assertEqual(changed_non_test_files(self.base, self.repo), ["core/views.py"])


if __name__ == "__main__":
    unittest.main()
