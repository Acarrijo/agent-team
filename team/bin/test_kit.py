"""Checks that the agent team's files haven't drifted from the rules."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / ".claude" / "agents"
NAMES = {"frontend-engineer", "backend-engineer", "test-writer", "reviewer", "launch-engineer", "data-bridge"}
MODEL_IDS = {"fable": "claude-fable-5-2", "opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
EXPECTED_MODEL = {
    "reviewer": "fable",
    "test-writer": "fable",
    "frontend-engineer": "opus",
    "backend-engineer": "opus",
    "launch-engineer": "opus",
    "data-bridge": "sonnet",
}


def parse(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    _, front, body = text.split("---\n", 2)
    meta = {}
    for line in front.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, body


class AgentFileTests(unittest.TestCase):
    def agents(self):
        return {p.stem: parse(p) for p in AGENTS.glob("*.md")}

    def test_all_agents_present(self):
        self.assertEqual(set(self.agents()), NAMES)

    def test_frontmatter_complete(self):
        for name, (meta, _) in self.agents().items():
            self.assertEqual(meta.get("name"), name)
            for key in ("description", "tools", "model"):
                self.assertTrue(meta.get(key), f"{name} is missing {key}")

    def test_models(self):
        for name, (meta, _) in self.agents().items():
            want = EXPECTED_MODEL[name]
            self.assertIn(meta["model"], {want, MODEL_IDS[want]}, name)

    def test_reviewer_cannot_edit(self):
        meta, _ = self.agents()["reviewer"]
        tools = {t.strip() for t in meta["tools"].split(",")}
        self.assertFalse(tools & {"Edit", "Write", "NotebookEdit"})

    def test_bodies_carry_rules(self):
        agents = self.agents()
        for name in ("frontend-engineer", "backend-engineer"):
            self.assertIn("Do not modify test files", agents[name][1])
        self.assertIn("VERDICT: PASS", agents["reviewer"][1])
        self.assertIn("VERDICT: FAIL", agents["reviewer"][1])
        self.assertIn("SPENDING.md", agents["launch-engineer"][1])
        self.assertIn("dry run", agents["data-bridge"][1])


if __name__ == "__main__":
    unittest.main()


TEAM = ROOT / "team"
BOARD_SECTIONS = ["## Waiting on owner", "## Up next", "## In progress", "## Blocked", "## Done"]


class PlaybookAndFilesTests(unittest.TestCase):
    def test_playbook_present(self):
        meta, body = parse(ROOT / ".claude" / "skills" / "run-project" / "SKILL.md")
        self.assertEqual(meta.get("name"), "run-project")
        for needle in ("strike.py", "check_tests_untouched.py", "Waiting on owner", "SPENDING.md", "DECISIONS.md", "main"):
            self.assertIn(needle, body)

    def test_playbook_names_every_agent(self):
        _, body = parse(ROOT / ".claude" / "skills" / "run-project" / "SKILL.md")
        for name in NAMES:
            self.assertIn(name, body)

    def test_board_sections(self):
        text = (TEAM / "BOARD.md").read_text()
        positions = [text.find(s) for s in BOARD_SECTIONS]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))

    def test_team_files_exist(self):
        for name in ("BRIEF.md", "DECISIONS.md", "SPENDING.md", "README.md"):
            self.assertTrue((TEAM / name).exists(), name)

    def test_claude_md_facts(self):
        # A project has its own CLAUDE.md; the kit repository ships a template.
        path = ROOT / "CLAUDE.md"
        if not path.exists():
            path = ROOT / "templates" / "CLAUDE.md"
        text = path.read_text()
        for needle in ("team/BOARD.md", "main"):
            self.assertIn(needle, text)


class ReviewFixTests(unittest.TestCase):
    def playbook(self):
        return parse(ROOT / ".claude" / "skills" / "run-project" / "SKILL.md")[1]

    def test_task_work_happens_in_a_worktree(self):
        body = self.playbook()
        self.assertIn("git worktree add", body)
        self.assertNotIn("git clean", body)

    def test_playbook_runs_kit_checks_and_test_writer_guard(self):
        body = self.playbook()
        self.assertIn('unittest discover -s team/bin', body)
        self.assertIn("check_tests_untouched.py --tests-only", body)
        self.assertIn("strike.py reopen", body)
        self.assertIn("**In progress**", body)
        self.assertIn("Step:", body)

    def test_main_is_hook_protected(self):
        import json
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
        hooks = settings["hooks"]["PreToolUse"]
        commands = [h["command"] for entry in hooks for h in entry["hooks"]]
        self.assertTrue(any("block_main.py" in c for c in commands))
        matchers = " ".join(entry["matcher"] for entry in hooks)
        self.assertIn("Bash", matchers)
        self.assertIn("merge_pull_request", matchers)

    def test_reviewer_fingerprint_is_structured(self):
        _, body = parse(AGENTS / "reviewer.md")
        self.assertIn("FINGERPRINT: <test id> <exception class>", body)
        self.assertIn("TESTS:", body)
