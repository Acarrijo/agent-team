# The agent team

To start or continue work, open a Claude Code session in this repository and say **"run the team"** (it uses the `run-project` skill).

| File | What it holds |
|---|---|
| `BRIEF.md` | The idea in the owner's words, and what's in and out |
| `BOARD.md` | Every task and where it stands, including what's waiting on the owner |
| `DECISIONS.md` | Product changes and tech-stack picks, with reasons |
| `SPENDING.md` | The approved budget and every charge |
| `strikes.json` | Failure counts per task (written only by `bin/strike.py`) |
| `bin/` | Scripts that enforce the hard rules, and their tests |

Check the scripts and team files: `python3 -m unittest discover -s team/bin -p "test_*.py"`
