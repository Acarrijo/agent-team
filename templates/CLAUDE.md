# <Project name> — project notes

Read this first in every session. Keep it current; it is the project's memory.

## The app

- What it is and who it's for.
- How to run the tests: `<command>`. Keep them all passing. Tests use made-up data only.

## Hosting

- Where it runs and how it deploys (e.g. Railway builds from `main`).
- Where the data lives, so deploys don't lose it.
- **Nothing reaches `main` without the owner.** A hook (`team/bin/block_main.py`, wired in `.claude/settings.json`) blocks pushes to `main` and pull-request merges. To go live, open a pull request; the owner merges it on GitHub.

## The agent team

- Playbook: `.claude/skills/run-project/SKILL.md`. Agents: `.claude/agents/`.
- State: `team/BOARD.md` (tasks and what's waiting on the owner), `team/BRIEF.md`, `team/DECISIONS.md`, `team/SPENDING.md`, `team/strikes.json`.
- Owner is on Claude Max 5x. Runs stop after 5 tasks or at the first usage warning.
- Default stack for new products: Django + Postgres + Stripe on Railway.

## Pending

-
