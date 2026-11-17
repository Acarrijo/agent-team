# Agent team

A reusable team of Claude Code agents that takes an idea for a software product (or a change to one) and runs with it: plans, writes tests first, builds, reviews, and gets it ready for launch — checking in with the owner only for money, product changes, going live and stuck work.

## The team

| Role | Where | Model | Job |
|---|---|---|---|
| CEO | `.claude/skills/run-project/SKILL.md` (the main session follows it) | Fable | Delegates, settles decisions, enforces the rules, reports |
| Planner | `.claude/agents/planner.md` | Fable | Plans each task before any test or code: rules, edge cases, size, decisions (read-only) |
| Test writer | `.claude/agents/test-writer.md` | Opus | Writes a task's tests from the plan before any code exists |
| Backend engineer | `.claude/agents/backend-engineer.md` | Opus | Models, logic, migrations, settings, security |
| Frontend engineer | `.claude/agents/frontend-engineer.md` | Opus | Templates, styling, browser-side code |
| Reviewer | `.claude/agents/reviewer.md` | Fable (rechecks on Opus) | Fresh, read-only, runs the tests itself, PASS/FAIL |
| Launch engineer | `.claude/agents/launch-engineer.md` | Opus | Hosting, workers, scheduled jobs, domains, providers |
| Data bridge | `.claude/agents/data-bridge.md` | Sonnet | Moves data between apps; always a dry run first |

## The rules, and what enforces them

- **Plan before code.** A planner pins down each task's rules and edge cases and sizes it (Small or Full track) before any test is written; the plan is saved in `team/plans/`. Small tasks skip the separate test writer; retries get a narrow recheck on Opus; the full test suite runs once per step.

- **Tests first, judged by someone else.** The test writer writes tests from the acceptance criteria; a fresh reviewer who never sees the engineer's explanation runs them and decides.
- **Engineers can't touch tests or team rules.** `team/bin/check_tests_untouched.py` fails any attempt that changes tests, `team/`, `.claude/`, `CLAUDE.md` or `conftest.py`.
- **Three strikes.** `team/bin/strike.py` decides after every failed review: the same failure 3 times → throw the attempt away and start a brand-new engineer; 3 more → blocked and the owner is told; 6 failures in total → blocked.
- **Nothing goes live without the owner.** `team/bin/block_main.py` is a hook that blocks every agent from pushing to `main` or merging pull requests. Going live = the team opens a pull request, the owner merges it.
- **Money only within an approved budget** (`team/SPENDING.md`). **Product changes only for efficiency or industry standard**, always logged in `team/DECISIONS.md` and flagged.
- **Memory lives in files**: `CLAUDE.md` and `team/`, so a run survives pauses and new sessions.

Full design: `docs/design.md`.

## Install into a project

```bash
git clone https://github.com/Acarrijo/agent-team
./agent-team/install.sh /path/to/your/project
```

The installer refreshes the agents, playbook and scripts every time (this repository is their source) and never overwrites a project's own `team/*.md`, `CLAUDE.md` or `.claude/settings.json`. Commit the result in the project, open a new Claude Code session there and say **"run the team"**.

## Changing the team

Edit here, then run the checks and reinstall into each project:

```bash
python3 -m unittest discover -s team/bin -p "test_*.py"
```

The checks catch drift: a missing agent, a wrong model, a reviewer that gained an edit tool, a playbook that lost a rule.
