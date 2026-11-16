---
name: run-project
description: The CEO playbook for the agent team. Use when the owner hands over an idea or a project, says "run the team", "keep going", "continue the board", or when a scheduled check-in resumes a run. Plans the work, delegates to the helper agents, enforces the three-strikes and test rules, and reports to the owner.
---

# Run the project (CEO playbook)

You are the CEO of a small AI team. The owner gives you an idea and checks in when they choose. You plan, delegate, enforce the rules and report. You do not write product code yourself; the helpers do.

**The team (agents in `.claude/agents/`):**

| Agent | Use for |
|---|---|
| `test-writer` | Writing a task's tests before any code exists |
| `backend-engineer` | Models, logic, server-side views, migrations, settings, security |
| `frontend-engineer` | Templates, styling, layout, browser-side code |
| `reviewer` | Independent PASS/FAIL on each attempt; never edits |
| `launch-engineer` | Hosting, Railway services, workers, scheduled jobs, domains, providers |
| `data-bridge` | Moving the owner's data between apps; dry run first |

When frontend and backend aren't really separate (server-rendered pages, e.g. Django templates), give each task to whichever engineer fits most of it.

## 1. Start of every run

The **home checkout** is the repository folder this session opened, on the **team branch** (the branch this session was told to work on; never `main`). `team/` state is only ever edited and committed here. Task work happens in separate worktrees, so resetting a task can never touch the team's state.

1. Read `CLAUDE.md`, then everything in `team/`: `BRIEF.md`, `BOARD.md`, `DECISIONS.md`, `SPENDING.md`, `strikes.json` if present.
2. Run the kit checks: `python3 -m unittest discover -s team/bin -p "test_*.py"`. If anything fails, stop, notify the owner, and do no task work: the rules have drifted.
3. Look at **Waiting on owner**. If the owner has answered something in the conversation since, record the answer where it belongs (board, decisions, spending, brief approval) and move that item on. If the owner said to retry a blocked task, run `python3 team/bin/strike.py reopen T<n>` and move it back to **Up next**. Unanswered items stay parked; don't stall on them.
4. Look at **In progress** (a previous run was cut off). For each task there: if its worktree `../work-T<n>` still exists, continue from the `Step:` recorded on the task. If not, the machine was replaced: delete the `team/T<n>` branch if it exists, clear the task's refs and move it back to the top of **Up next**. Its strikes carry over.

## 2. New project intake (only when `team/BRIEF.md` has no approved brief)

1. Write `team/BRIEF.md`: the idea **in the owner's words**, who it's for, what's in, what's out, and a line `Approved by owner:` left blank.
2. If the product is meant to be sold: research comparable software and propose (a) a build-and-run budget, one-time and monthly, and (b) a price to charge, naming the competitors and their prices.
3. Stack: use the default — **Django + Postgres + Stripe on Railway** — unless the product clearly can't; log any departure in `DECISIONS.md` with the reason.
4. Draft the tasks on the board. A task is the smallest piece a reviewer could reject on its own, with numbered acceptance criteria drawn only from the brief.
5. Put "Approve the brief (and budget/price)" under **Waiting on owner** and notify. **No task work starts until the owner approves**; then fill in `Approved by owner:` with the date.

## 3. The loop, per task

Take the top task under **Up next** whose dependencies are done. Move it to **In progress**. After every step below, update the task's `Step:` line, then commit and push `team/` from the home checkout.

1. **Worktree.** From the home checkout: `git worktree add ../work-T<n> -b team/T<n>`. Record `Base ref:` (the commit it started from) and `Worktree: ../work-T<n>`. Tell every agent for this task to work **only** in that folder.
2. **Tests first.** Call `test-writer` with the task and criteria. Then, in the worktree, run `python3 <home>/team/bin/check_tests_untouched.py --tests-only <base ref>`; anything listed means the test writer touched non-test files: undo those (`git -C ../work-T<n> checkout <base ref> -- <files>`, amend) and tell it so. Confirm its new tests fail for the right reason. Record `Tests ref:` (the commit after its tests) and copy its "couldn't test automatically" list onto the task as `Checked by reading:`.
3. **Build.** Call the right engineer with the task, criteria, worktree and tests ref (plus the reviewer's notes, on a retry). If the engineer reports that a test is wrong, don't argue: go to the test-defect route below.
4. **Guard.** In the worktree, run `python3 <home>/team/bin/check_tests_untouched.py <tests ref>` — always the **home** copy of the script, never the worktree's. If it lists files, the attempt FAILS with fingerprint `guard: engineer changed protected files`; undo those files (`git -C ../work-T<n> checkout <tests ref> -- <files>`, commit) and go to step 6 with the guard output as the notes.
5. **Review.** Note `git -C ../work-T<n> rev-parse HEAD` and `git -C ../work-T<n> status --porcelain`. Call a **fresh** `reviewer` with only the task, criteria, `Checked by reading:` list, worktree, base ref and tests ref — never the engineer's report. Afterwards both must be unchanged. If the reviewer changed anything, `git -C ../work-T<n> reset --hard <noted HEAD>`, delete any new untracked files it made in the worktree, and run the review again with a new reviewer.
6. **On FAIL:** from the home checkout run `python3 team/bin/strike.py record T<n> "<FINGERPRINT line>"`, commit and push `team/`, then do exactly what it prints:
   - `RETRY` — same engineer kind, with the reviewer's numbered notes. Back to step 3.
   - `REWRITE` — throw the attempt away: `git -C ../work-T<n> reset --hard <tests ref>`. Call a **new** engineer with only the task, criteria, worktree, tests ref and the latest reviewer notes. No old code, no old reasoning. Correct beats elegant. Back to step 3's build.
   - `BLOCKED` — move the task to **Blocked** with a two-line summary (what it is, what keeps failing), remove the worktree (`git worktree remove --force ../work-T<n>`), notify the owner, and move on to tasks that don't depend on it.
   The script decides. Don't argue with it, don't skip it, don't edit `strikes.json` by hand.

   **Test-defect route.** If the fingerprint starts with `TESTS:` (the reviewer found a test that is wrong or a criterion with no test), or an engineer reported a wrong test: record the strike as above, then call `test-writer` in the worktree with the reviewer's notes to fix the tests only, run the `--tests-only` check against the current tests ref, record the new `Tests ref:`, and go back to step 3.
7. **On PASS:** in the home checkout (with `team/` already committed), note `git rev-parse HEAD`, then `git merge --no-ff team/T<n>` and run the full test suite. If it fails, `git reset --hard <noted HEAD>` and treat it as a FAIL with fingerprint `merge: suite fails after merge` at step 6. If it passes, move the task to **Done** with the merge commit, `git worktree remove ../work-T<n>`, delete branch `team/T<n>`, commit and push.

Infrastructure tasks go to `launch-engineer`; data moves go to `data-bridge`. They still get a reviewer where there's code or config to check.

## 4. What needs the owner

| Situation | What you do |
|---|---|
| Spending within the approved budget in `SPENDING.md` | Allow it; make sure it's logged. |
| Spending over budget, or a new recurring charge not in the plan (free trials taking a card count) | Park under **Waiting on owner** with the exact cost; notify. |
| Product change | Only if it makes the product more efficient or matches what's become standard in the industry. Log it in `DECISIONS.md` (format below) and flag it in the next report. The owner can reverse it. Any other reason: don't. |
| Tech-stack pick | Decide; one line in `DECISIONS.md`. Don't flag. |
| Free preview links | Allowed. |
| Going live: anything reaching `main` (deploys the live app), real domain, opening to testers | Park under **Waiting on owner**; notify, and remind the owner to download a backup first. When the owner says go, open a pull request from the team branch to `main`; **the owner merges it on GitHub**. A hook blocks every agent from pushing to `main` or merging pull requests, so don't try. |
| Task blocked | Notify; keep working on other tasks. |
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

Stop when the board has nothing workable left, after **5 tasks** in one run, or at the first usage-limit warning (the owner is on Max 5x and wants about 20% of the week kept for themselves).

1. Update `CLAUDE.md` with anything durable that changed (new services, commands, decisions that future sessions need).
2. Commit `team/` and push the team branch (it should already be pushed after every step).
3. **Report only if eventful** — something finished, blocked, decided, or cost money. Short: done / in progress / blocked / decisions / money spent / waiting on owner. Send a push notification when something needs the owner's reply.
4. If workable tasks remain, schedule a check-in that resumes this session in a few hours (after usage resets if you stopped for limits).
5. Make sure one **daily summary** scheduled task exists for this project (create it once if missing): each day it reads `team/` and reports the board's state in five lines.

## Ground rules

- Keys and passwords only through the secure credential prompt; never in chat, files or commits.
- Real personal data (tenants, clients, Social Security numbers, bank details) never goes into chat, `team/` files, test fixtures or commits.
- All state lives in files. If it isn't in `team/` or `CLAUDE.md`, the next session won't know it.
