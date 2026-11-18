# Agent Team — Design

Date: 2026-11-15
Status: draft, awaiting owner approval

## Intent

The owner wants a reusable team of AI agents that takes an idea for a software-as-a-service product (or a change to an existing one) and runs with it: plans it, builds it, tests it, reviews it, and gets it ready for a soft launch, without the owner prompting each step or watching every move. The owner checks in when they choose; the team only interrupts for decisions that are the owner's.

This is also the owner's first serious test of agents in general. If it works, they will add more agents for other kinds of work later, so the pieces should be easy to copy and extend. Keep cost low: everything runs on the owner's existing Claude plan, no per-use API billing.

The first project the team works on is UnitBook (this repository), the owner's personal landlord app.

## Goals

1. Hand the team an idea once; it works through the whole job unattended.
2. Six roles: CEO (leader/planner), frontend engineer, backend engineer, reviewer, launch engineer, data bridge.
3. Code is judged by evidence (tests written before the code, run by someone other than the author), never by the author's opinion of its own work.
4. A repeated failure triggers a hard stop and a rewrite from a clean slate, not endless patching.
5. The team remembers each project between sessions without the owner re-explaining it.
6. The owner is pinged only for: money, product changes, going live, and work that is truly stuck.

## Non-goals

- A custom program built on the Agent SDK, or a server running agents around the clock. (Possible later upgrade if instructions plus automatic checks prove too loose.)
- Selling UnitBook, the accountant portal, tenant portal or tenant payments. Those are future projects for the team, not part of building the team.
- Adapting the installed "10x-Team" plugin. It can be borrowed from for wording only.

## Anti-goals (would be a failure even if it "works")

- The team drifts from the owner's idea for reasons other than the two allowed ones (below).
- Any money is spent without an approved budget, or beyond it.
- Anything reaches the live app or real testers without the owner's yes.
- A loop keeps burning plan usage on the same problem.
- The reviewer rubber-stamps, or an engineer edits the tests to make them pass.
- Real tenant or client data (names, Social Security numbers, bank details) is pasted into chats, task files or commits.

## Constraints

- **Where the team runs:** Claude Code cloud sessions (work continues with the owner's computer off). The owner also has a desktop computer with an agent on it, used only for browser/desktop work that has no other route.
- **Helper agents cannot start other helpers.** So the CEO must be the main session, following a playbook; the other five are helper agents the CEO calls.
- **Plan usage limits.** The owner has hit the 5-hour limit before. The loop must survive a limit pause: all state lives in files in the repository, and work resumes from those files.
- **UnitBook deploys from `main`.** Railway rebuilds the live app on every push to `main`. The team works on a branch; merging to `main` is "going live" and needs the owner's yes.
- **Repository scope:** this session can only reach `Acarrijo/UnitBook`, so the team kit lives in this repository for now (see Approaches).

## Approaches considered

1. **Agent files plus a "run the project" playbook, in Claude Code. (Chosen.)** Six agent definitions and a CEO playbook, kept as plain files. Cheap, uses the existing plan, works today. Rules are enforced by the playbook plus small scripts/automatic checks, not by a program.
2. **Adapt the installed 10x-Team plugin.** Less upfront work, but twelve generic roles and none of the owner's rules (strikes, budget, change log).
3. **Custom Agent SDK program.** Every rule enforced in code and runs around the clock, but it is a software project of its own and billed per use through the API.

The owner picked **1**, to keep it simple and cheap.

## The design

### Files

All in this repository:

```
CLAUDE.md                        project memory: read by every session and agent
.claude/agents/                  the helper agents (one file each)
.claude/skills/run-project/      the CEO playbook
team/BRIEF.md                    the idea, in the owner's words, plus the agreed scope
team/BOARD.md                    task board: every task, its status, its acceptance criteria
team/STRIKES.md                  failure log with fingerprints (or a machine-readable equivalent)
team/DECISIONS.md                product changes and tech-stack picks, with reasons
team/SPENDING.md                 approved budget, every charge, running total
team/bin/                        small scripts that enforce the hard rules
```

When the kit proves itself, it is copied into each new project (and later can move to a repository of its own). The `team/` folder is per project; `.claude/` is the reusable kit.

### Project memory (`CLAUDE.md`)

Short notes every session reads automatically: what the app is, where it is hosted and how it deploys, how to run the tests, what is decided, what is pending. The CEO updates it whenever something durable changes. For UnitBook it starts with what is known today: Django; live on Railway with a volume; deploys on push to `main`; tests via `.venv/bin/python manage.py test` (49 passing); the owner is Admin; five recommended security changes not yet built (required two-step, sign-out after inactivity, 12-character passwords, browser security settings, no caching of signed-in pages).

### The roles

| Role | What it does | Can edit code? |
|---|---|---|
| **CEO** (main session + playbook) | Turns the idea into a brief, proposes budget and pricing, breaks work into tasks, calls the others, runs the loop, keeps the files current, reports to the owner. | Only team files |
| **Frontend engineer** | Pages, templates, styling, browser-side code. | Yes |
| **Backend engineer** | Data models, business logic, APIs, migrations, security settings. | Yes |
| **Reviewer** | Two jobs, as two agent files: *test writer* writes tests from the acceptance criteria before any code exists (may only touch test files); *reviewer* starts fresh each time, runs the tests itself, reads the change, passes or fails it with notes. | Test writer: tests only. Reviewer: no. |
| **Launch engineer** | Hosting, domains, environment settings, databases, email, payments setup, preview links. Uses command-line tools and APIs first; browser clicking (from the owner's desktop) only where nothing else works. | Config only |
| **Data bridge** | Moves the owner's data from a spreadsheet, database, browser app or desktop app into another app. Routes in order: direct import/API, then browser, then desktop. | No (writes data, not code) |

For a project where frontend and backend aren't really separate (UnitBook builds its pages on the server), the CEO assigns each task to whichever engineer fits; one engineer may own a task end to end.

### The loop (per task)

1. **Criteria.** The CEO writes the task on the board with plain acceptance criteria drawn only from the brief.
2. **Tests first.** The test writer turns the criteria into tests. They must fail before the work starts (proving they test something).
3. **Build.** An engineer does the work. The engineer may not change those tests. If the engineer changes a test file, that is an automatic fail.
4. **Review.** A fresh reviewer sees only the task, the tests and the change — never the engineer's explanation. It runs the full test suite itself, checks the change against the criteria and the project's standards (including security for anything touching personal data), and returns PASS or FAIL with notes. The CEO confirms the reviewer left the code untouched.
5. **On PASS:** the task is merged into the team's working branch and marked done.
6. **On FAIL:** the failure gets a fingerprint (which test failed plus the essence of the error, or the reviewer's main objection) and is logged in the strikes file. The same engineer gets the notes and tries again.
7. **Three strikes, same fingerprint → hard stop.** The attempt's code is thrown away (reset to the task's starting point). A *brand-new* engineer starts from only the task, the tests and the reviewer's notes — no old code, no old reasoning. Correct beats elegant.
8. **Strike out again on the rewrite → blocked.** The task is marked blocked, the owner is notified with a short summary, and the CEO moves on to other tasks that don't depend on it.
9. **Backstop:** six failed reviews on one task in total, whatever the fingerprints, also counts as blocked. (Stops loops where the error keeps changing.)

The strike counting and the "third strike" decision are done by a script in `team/bin/`, not by the CEO's judgment, so the rule can't be talked around.

### Starting a project

1. The owner gives the idea, in any form.
2. The CEO writes `team/BRIEF.md`: the idea in the owner's words, who it's for, what's in and out.
3. For a product meant to be sold, the CEO researches comparable software and proposes: **a build-and-run budget** (one-time and monthly) and **a price** to charge, with the competitors it compared against.
4. The owner approves the brief and budget (one sitting). After that, the team runs.

For a personal project like UnitBook, step 3 is skipped unless something costs money.

### What needs the owner

| Situation | What happens |
|---|---|
| Spending within the approved budget | Done and logged in `SPENDING.md`; no ask. |
| Spending over budget, or a new recurring charge not in the plan | Stops and asks, with exact cost. Free trials that take a card count as spending. |
| Product change | Allowed only if it makes the product more efficient or matches what has become standard in the industry. Logged in `DECISIONS.md` with the reason and the original idea, and flagged in the next report. The owner can reverse it. |
| Tech-stack pick | The team decides, logs one line of reasoning. Not flagged. |
| Free preview links | The team may create them. |
| Going live (merge to `main` for UnitBook, opening to testers for anything) | Needs the owner's yes. |
| Task blocked after the rewrite | Owner notified; the team continues with other work. |
| Data bridge bulk write | Always a dry run first ("48 tenants, 12 units, 3 problems"); writes nothing until the owner says go. |

### Running unattended

- A run is one cloud session working down the board.
- If the session stops (usage limit, idle timeout), a scheduled check-in resumes it; the CEO re-reads `CLAUDE.md` and `team/` and continues. No memory is held only in chat.
- At the end of each run, and whenever something needs the owner, the CEO sends a short report: done, in progress, blocked, decisions made, money spent. Phone notifications for anything that needs a reply.

### Secrets and personal data

- Keys and passwords are given through the secure credential prompt, never typed into chat or saved in files.
- Real tenant/client data never goes into chats, task files, test fixtures or commits. Tests use made-up data. The data bridge shows counts and problem rows, masking sensitive fields.

### First mission (pilot)

To test the team on something real and small, its first job in UnitBook:

1. **The five security changes** already recommended (well defined, easy to judge).
2. **An Admin-only Import page:** upload a spreadsheet, see a preview with problems listed, confirm, and the rows are saved through the app's normal rules and recorded in History as added by import. This is the data bridge's "direct route" for UnitBook.

Both go to the team's branch; the owner decides when they go live.

**Security change details (my calls, so nobody gets locked out):**

- Two-step sign-in becomes required for every login. Anyone without it is walked through setting it up at their next sign-in, not locked out.
- Sign-out after 2 hours without use.
- The 12-character minimum applies to new and changed passwords; existing passwords keep working.
- Browser security settings include HSTS with a short lifetime (one day) and no preload list, so it can be undone; it can be lengthened once things are stable.
- Signed-in pages and files are sent with "never store" cache headers.

**Import page details:**

- The owner uploads the real file through the Admin page, so real data stays inside UnitBook and never enters a chat. The data bridge's pilot job is building the importer around the owner's column layout, using a made-up sample file with the same headers. The dry run ("48 tenants, 12 units, 3 problems") is shown by the Import page itself.
- Records that already exist (matched on property address + unit, tenant name + unit) are flagged in the preview, never silently overwritten or duplicated.
- Which kinds of record it covers follows the owner's spreadsheet (see open question).

### How the owner is reached

Pings and reports arrive in the Claude app (phone notification); the owner replies in the session. A pending yes/no is written to `team/BOARD.md` under "Waiting on owner" so a resumed session picks up the answer or keeps waiting on just that item.

## Decided by the owner

- Six roles as above; CEO leads, reviewer only reviews.
- Option 1 (agent files + playbook) to keep it simple and cheap.
- Three strikes on the same error → hard stop, rewrite in a fresh context.
- Money only within an owner-approved budget; the CEO proposes budget and price from industry rates.
- Team picks the tech stack within what the product needs.
- Product changes only for efficiency or industry-standard reasons, and the owner is told.
- Data bridge is a personal helper; first use is the owner's UnitBook spreadsheet.

- Model mix: Fable for the CEO, the reviewer and writing the team's rules; Opus for the engineers; Sonnet or Haiku for routine jobs (board updates, data moving). Each agent file names its model.
- The reusable kit moves to its own repository, `Acarrijo/agent-team`, once it has worked on UnitBook. Each new project copies from it.
- New products use a default stack, left only for a logged reason: Django + Postgres + Stripe, hosted on Railway.
- The team pauses at about 80% of the owner's weekly plan usage.
- Reporting: a daily summary, plus an end-of-run report when the run was eventful (something finished, blocked, decided or spent). Decisions are pinged immediately. Every ping, report and scheduled task starts with the project's name (its folder name), and task worktrees are named `../<project>-work-T<n>`, so the team can run on several projects at once without mixing them up.
- Browser/desktop work runs through the Claude desktop app on the owner's computer.

## My calls (owner can override)

- CEO = main session (forced by how helper agents work).
- Tests written before code, by the reviewer role, as the main defense against bias.
- Reviewer split into a test-writer file and a read-only reviewer file.
- Backstop of six total failures per task.
- Going live needs the owner's yes; free preview links don't.
- Team kit lives in this repository until it proves itself.
- Pilot = security changes + Import page.

## Left to the builder

- Exact wording of each agent file and the playbook.
- Format of the board and strikes files, and how the scripts enforce strikes.
- How fingerprints are normalized (e.g., stripping line numbers and timestamps).
- Which automatic checks (hooks) back up the rules.
- Branch naming per task.
