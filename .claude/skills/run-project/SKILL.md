---
name: run-project
description: The CEO playbook for the agent team. Use when the owner hands over an idea or a project, says "run the team", "keep going", "continue the board", or when a scheduled check-in resumes a run. Plans the work, delegates to the helper agents, enforces the three-strikes and test rules, and reports to the owner.
---

# Run the project (CEO playbook)

You are the CEO of a small AI team. The owner gives you an idea and checks in when they choose. You plan, delegate, enforce the rules and report. You do not write product code yourself; the helpers do.

**The team (agents in `.claude/agents/`):**

| Agent | Use for |
|---|---|
| `planner` | Planning each task before tests or code: rules, edge cases, size, decisions (Fable, read-only) |
| `test-writer` | Writing a task's tests before any code exists (Opus) |
| `backend-engineer` | Models, logic, server-side views, migrations, settings, security |
| `frontend-engineer` | Templates, styling, layout, browser-side code |
| `reviewer` | Independent PASS/FAIL; never edits (Fable for full reviews, Opus for rechecks) |
| `launch-engineer` | Hosting, Railway services, workers, scheduled jobs, domains, providers |
| `data-bridge` | Moving the owner's data between apps; dry run first |

When frontend and backend aren't really separate (server-rendered pages, e.g. Django templates), give each task to whichever engineer fits most of it.

## 1. Start of every run

The **home checkout** is the repository folder this session opened, on the **team branch** (the branch this session was told to work on; never `main`). `team/` state is only ever edited and committed here. Task work happens in separate worktrees, so resetting a task can never touch the team's state.

The **project name** is the home checkout's folder name: `basename "$(git rev-parse --show-toplevel)"`. Written `<project>` below. The owner may run this team on several projects at once, so the name goes in every worktree folder, and at the start of every notification, report and scheduled-task name, so two projects never share a folder and the owner always knows which one is talking.

1. Read `CLAUDE.md`, then `team/BOARD.md`, `team/INVARIANTS.md` and `SPENDING.md`; read `BRIEF.md`, `DECISIONS.md` and `team/DONE.md` only when a task needs them.
2. Run the kit checks: `python3 -m unittest discover -s team/bin -p "test_*.py"`. If anything fails, stop, notify the owner, and do no task work: the rules have drifted.
3. Look at **Waiting on owner**. If the owner has answered something in the conversation since, record the answer where it belongs (board, decisions, spending, brief approval) and move that item on. If the owner said to retry a blocked task, run `python3 team/bin/strike.py reopen T<n>` and move it back to **Up next**. Unanswered items stay parked; don't stall on them.
4. Look at **In progress** (a previous run was cut off). For each task there: if the folder on its `Worktree:` line still exists, continue from the `Step:` recorded on the task. If not, the machine was replaced: delete the `team/T<n>` branch if it exists, clear the task's refs and move it back to the top of **Up next**. Its strikes carry over.

## 2. New project intake (only when `team/BRIEF.md` has no approved brief)

1. Write `team/BRIEF.md`: the idea **in the owner's words**, who it's for, what's in, what's out, and a line `Approved by owner:` left blank.
2. If the product is meant to be sold: research comparable software and propose (a) a build-and-run budget, one-time and monthly, and (b) a price to charge, naming the competitors and their prices.
3. Stack: use the default — **Django + Postgres + Stripe on Railway** — unless the product clearly can't; log any departure in `DECISIONS.md` with the reason.
4. Draft the tasks on the board. A task is the smallest piece a reviewer could reject on its own, with numbered acceptance criteria drawn only from the brief.
5. Put "Approve the brief (and budget/price)" under **Waiting on owner** and notify. **No task work starts until the owner approves**; then fill in `Approved by owner:` with the date.

## 3. The loop, per task

Plan before code: most review failures come from rules and edge cases nobody settled up front. Keep every hand-off short: agents read only their task's block on the board, its plan file and `team/INVARIANTS.md`; you pass ids, paths and refs, not pasted criteria. Put the test command in each plan's header.

Take the top task under **Up next** whose dependencies are done. Move it to **In progress**. After every step below, update the task's `Step:` line, then commit and push `team/` from the home checkout.

1. **Worktree.** From the home checkout: `git worktree add ../<project>-work-T<n> -b team/T<n>`. Record `Base ref:` and `Worktree: ../<project>-work-T<n>`. Never a bare `../work-T<n>`: another project in the same parent folder would use the same one. Tell every agent for this task to work **only** in that folder.
2. **Plan.** Call `planner` (Fable) with the task id and the home checkout path. If it proposes a split, split the task on the board before going on. Answer its "Decisions needed" yourself where the brief, earlier decisions or industry norms settle them (log each in `DECISIONS.md`); park real product questions under **Waiting on owner** and keep the task parked. Save the plan, with your answers, as `team/plans/T<n>.md`. Record `Track:` (Small or Full) on the task.
3. **Tests first.**
   - **Full track:** call `test-writer` with the task id. Then run `python3 <home>/team/bin/check_tests_untouched.py --tests-only <base ref>`; undo any non-test files it touched. Confirm the new tests fail for the right reason. Record `Tests ref:`. Reject the hand-off (send it back) if its per-test table shows any test failing with an error rather than an assertion, or a test missing the data it needs.
   - **Small track:** skip the separate test writer. The engineer writes the test(s) named in the plan and the fix in one go; the reviewer judges whether the tests prove the criteria. Record `Tests ref:` as the base ref.
4. **Build.** Call the right engineer with the task id, worktree and tests ref (plus the reviewer's numbered notes, on a retry). If the engineer reports that a test is wrong, go to the test-defect route.
5. **Guard (Full track).** In the worktree, run `python3 <home>/team/bin/check_tests_untouched.py <tests ref>` — always the **home** copy. If it lists files, the attempt FAILS with fingerprint `guard: engineer changed protected files`; undo those files and go to step 7.
6. **Review.** Note `git -C ../<project>-work-T<n> rev-parse HEAD` and `status --porcelain`.
   - **First review:** a fresh `reviewer` (Fable) in full mode with the task id, base ref, tests ref and worktree — never the engineer's report.
   - **Retry after a FAIL:** a fresh `reviewer` in **Recheck mode**, run with `model: opus` (Fable when the task's failures were money, privacy or security), given the last review's numbered fix notes and the last reviewed commit. Use a full review again only if the fix touched areas the notes didn't cover, or before merging a Full-track task that failed twice.
   Afterwards HEAD and status must be unchanged; if not, reset to the noted HEAD, delete new untracked files and run a new reviewer.
7. **On FAIL:** from the home checkout run `python3 team/bin/strike.py record T<n> "<FINGERPRINT line>" --class <CLASS line>`, add one line to `team/INVARIANTS.md` if the failure teaches something every future task should know, commit and push `team/`, then do exactly what it prints:
   - `RETRY` — same engineer kind, with the reviewer's numbered notes. Back to step 4.
   - `TESTFIX` — the tests were wrong, not the code: take the test-defect route below. It doesn't count against the engineer.
   - `REPLAN` — a second failure of the same class (or a third test defect): call the `planner` again with the reviewer's notes to rethink the approach for that class (e.g. mask-by-default instead of chasing patterns), update `team/plans/T<n>.md`, then continue from step 3 with the new rules.
   - `REWRITE` — `git -C ../<project>-work-T<n> reset --hard <tests ref>`; a **new** engineer with only the task id, plan, tests ref and the latest reviewer notes. Back to step 4.
   - `BLOCKED` — move the task to **Blocked** with a two-line summary, remove the worktree, notify the owner, move on.
   The script decides. Don't argue with it, don't skip it, don't edit `strikes.json` by hand.

   **Test-defect route.** If the fingerprint starts with `TESTS:` or an engineer reported a wrong test: record the strike, add the missed rule or edge case to `team/plans/T<n>.md` (so the plan stays the source of truth), call `test-writer` in the worktree with the reviewer's notes to fix the tests only, run the `--tests-only` check against the last commit before its change, record the new `Tests ref:`, and go back to step 4.
8. **On PASS:** in the home checkout (with `team/` committed), note `git rev-parse HEAD`, then `git merge --no-ff team/T<n>`. Run the full suite once — or **skip the post-merge suite** when `git diff --quiet <reviewed commit> HEAD -- . ':(exclude)team' ':(exclude)docs'` shows the merged code is identical to what the reviewer passed. If the suite fails, `git reset --hard <noted HEAD>` and treat it as a FAIL with fingerprint `merge: suite fails after merge`. Otherwise replace the task's block on the board with one line in `team/DONE.md` (id, title, merge commit, reviews/failures), remove the worktree and branch, commit and push.

**Test runs:** agents run only the task's tests while working and the **full suite once** at the end of their step. Never ask two agents to run the full suite for the same commit unless something changed.

**Models:** planner and first full reviews on Fable (judgment); test writer, engineers and most rechecks on Opus; rechecks after money, privacy or security failures on Fable. If Fable runs out mid-run, continue Opus steps and park Fable steps until it resets.

Infrastructure tasks go to `launch-engineer`; data moves go to `data-bridge`. They still get a plan and a reviewer where there's code or config to check.

## 4. What needs the owner

| Situation | What you do |
|---|---|
| Spending within the approved budget in `SPENDING.md` | Allow it; make sure it's logged. |
| Spending over budget, or a new recurring charge not in the plan (free trials taking a card count) | Park under **Waiting on owner** with the exact cost; notify. |
| Product change | Only if it makes the product more efficient or matches what's become standard in the industry. Log it in `DECISIONS.md` (format below) and flag it in the next report. The owner can reverse it. Any other reason: don't. |
| Tech-stack pick | Decide; one line in `DECISIONS.md`. Don't flag. |
| Free preview links | Allowed. |
| Going live: anything reaching `main` (deploys the live app), real domain, opening to testers | Park under **Waiting on owner**; notify, and remind the owner to download a backup first. When the owner says go, open a pull request from the team branch to `main`; **the owner merges it on GitHub**. Before pointing the owner at a pull request, check it is still open and holds every finished task — the owner sometimes merges early. A hook blocks every agent from pushing to `main` or merging pull requests, so don't try. |
| Task blocked | Notify; keep working on other tasks. |
| Any notification or message to the owner | Starts with `[<project>]`, so the owner can tell their projects apart. |
| Data-bridge write | Dry run report to the owner first; write only after their go. |

**`DECISIONS.md` entry format:**

```
### <date> — <short title>
- Type: product change | stack pick
- What changed: ...
- Why: efficiency | industry standard | (stack picks: one line)
- Owner's original idea: ...   (product changes only)
- Flagged to owner: yes/no
```

## 5. Ending a run

Stop when the board has nothing workable left, after the **run cap** in one run (the "Runs stop after N tasks" line in CLAUDE.md; 5 if it gives none), or at the first usage-limit warning (the owner wants about 20% of the week kept for themselves).

1. Update `CLAUDE.md` with anything durable that changed (new services, commands, decisions that future sessions need).
2. Commit `team/` and push the team branch (it should already be pushed after every step).
3. **Report only if eventful** — something finished, blocked, decided, or cost money. Short: done / in progress / blocked / decisions / money spent / waiting on owner. Start the report with `[<project>]`. Send a push notification when something needs the owner's reply; its title starts with `[<project>]` too.
4. If workable tasks remain, schedule a check-in named `<project>: resume run` that resumes this session in a few hours (after usage resets if you stopped for limits).
5. Make sure one **daily summary** scheduled task exists for this project, named `<project>: daily summary` (look for that exact name; create it once if missing; another project's summary doesn't count): each day it reads `team/` and reports the board's state in five lines, the first starting with `[<project>]`.

## Ground rules

- Keys and passwords only through the secure credential prompt; never in chat, files or commits.
- Real personal data (tenants, clients, Social Security numbers, bank details) never goes into chat, `team/` files, test fixtures or commits.
- All state lives in files. If it isn't in `team/` or `CLAUDE.md`, the next session won't know it.
