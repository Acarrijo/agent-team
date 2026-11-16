import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from block_main import is_blocked  # noqa: E402


class BlockMainTests(unittest.TestCase):
    def test_blocks_pushes_to_main(self):
        for cmd in [
            "git push origin main",
            "git push -u origin main",
            "git push origin HEAD:main",
            "git push origin +main",
            "git push --force origin feature:refs/heads/main",
            "cd x && git push origin main",
            "git push --all",
            "git push --mirror origin",
        ]:
            self.assertTrue(is_blocked(cmd), cmd)

    def test_allows_other_pushes(self):
        for cmd in ["git push -u origin claude/gracious-ride-c4j68y", "git push origin team/T1", "git status", "echo main"]:
            self.assertFalse(is_blocked(cmd), cmd)

    def test_hook_exit_codes(self):
        def run(cmd):
            payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
            return subprocess.run([sys.executable, str(HERE / "block_main.py")], input=payload, text=True, capture_output=True).returncode
        self.assertEqual(run("git push origin main"), 2)
        self.assertEqual(run("git push origin team/T1"), 0)

    def test_hook_blocks_pr_merge_tool(self):
        payload = json.dumps({"tool_name": "mcp__github__merge_pull_request", "tool_input": {}})
        r = subprocess.run([sys.executable, str(HERE / "block_main.py")], input=payload, text=True, capture_output=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
