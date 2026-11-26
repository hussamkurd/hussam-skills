---
name: senior-review
description: "Read-only senior review of a branch or PR before it ships. Parallel reviewers find what must change, the senior engineer decides on each finding, and the accepted ones become a spec any implementation skill can run."
disable-model-invocation: true
license: MIT
metadata:
  version: 2.3.0
---

# Senior Review

You review a change that ships to production today. The goal is one list: what must change before it is safe and clean to ship. The senior engineer decides on each item, and what they accept becomes a spec.

Run the review on whatever the user points at: a GitHub PR, a Bitbucket PR, or a plain branch. Start the review straight away, whatever state the change is in.

## Rules for the whole run

- **Read-only.** The user's working tree stays as you found it. Code runs in a separate worktree. Every change you want is a finding, not an edit.
- **Review folder.** Everything goes in `~/.agents/reviews/<repo>/<pr-or-branch>/` (for example `~/.agents/reviews/billing-api/pr-412/`, or `.../billing-api/feature-ABC-12-export/` for branch `feature/ABC-12-export`): `review.md`, `spec.md`, screenshots, and the worktree. It is outside the repo.
- **Findings.** Every finding follows [finding.md](finding.md), and every claim follows its evidence rule.

## 1. Set up

1. **Base branch.** The one the user names. Else the PR base (`gh pr view --json baseRefName,number`). Else `develop`, when `origin/develop` exists and the branch forks from it (its merge-base with `develop` is newer than with the default branch). Else the remote default branch (`git symbolic-ref refs/remotes/origin/HEAD`).
2. **Change set.** `git diff $(git merge-base origin/<base> <head-sha>)..<head-sha>`. For a named GitHub PR, `gh pr diff <n>` is the same view. Other hosts need no API. Pass this exact command, SHAs filled in, to every lane.
3. **Committed changes only.** If `git status --porcelain` shows anything, review the commits anyway and note at the top of the report: `uncommitted files not reviewed: <paths>`.
4. **Worktree.** If `<review-folder>/worktree` exists, remove it first with `git worktree remove --force`. Then `git worktree add <review-folder>/worktree <head-sha>`. For a PR not checked out, `git fetch origin pull/<n>/head:review-<n>` first.
5. **Requirement.** The PR description. Else the issue whose key (like `ABC-123`) is in the branch name or commits, fetched with an issue-tracker tool when one is connected. Also any spec those link to. If none is found, carry on and note `no requirement found`.
6. **Component map.** Put every changed file in at least one component: Database (migrations, queries, models, indexes), Infrastructure (IaC, Docker, CI/CD, deploy config, env vars, secrets, cron), I/O (HTTP clients, queues, cache, storage), API contract (routes, request and response shapes, events, public types), Security (auth, permissions, input validation), Core logic (other code), Docs/files (everything else). Every component except Docs/files is a risky component.

Done when you can say in two sentences what the change does and what was asked, and you have `Base: <branch> @ <sha>`, `Head: <branch> @ <sha>`, the worktree path, and the component map.

## 2. Review in parallel

Start the four lanes at the same time, as subagents in one message (the Agent tool in Claude Code, or your harness's equivalent). Each lane has its own brief in `lanes/`.

| Lane | Brief | Looks at |
|---|---|---|
| Risk | [lanes/risk.md](lanes/risk.md) | each risky component, the four safety answers |
| Design | [lanes/design.md](lanes/design.md) | the project's principles, simpler shapes |
| Scope | [lanes/scope.md](lanes/scope.md) | requirement coverage, what should not ship |
| Verify | [lanes/verify.md](lanes/verify.md) | typecheck, lint, tests, throwaway checks |

Give each subagent the same packet: the absolute paths of its brief and of finding.md, the base and head SHAs, the worktree path, the review folder, the diff command, the requirement text, and the component map. Tell Risk, Design and Scope to stay read-only. Tell Verify it may run commands only in the worktree and in containers it starts. No lane connects to a database or service outside this session.

When the change is big (about 800 changed lines or more, or three or more risky components), split the Risk lane: one subagent per risky component, each told which component it owns.

With no subagents available, run the lanes yourself one after another. The output is the same.

If a lane fails or returns nothing in the shape, run it once more, then run it yourself. If neither works, mark its sections unverified and set Confidence to Low.

Done when every lane has returned.

## 3. Merge

1. **Check every critical yourself.** Open the `file:line` and read the evidence. Drop or downgrade what does not hold up.
2. **Merge duplicates.** Two lanes often find the same thing from two sides. Keep one finding with both pieces of evidence.
3. **Match risky paths.** Each path the Risk lane says needs a real run must have a passing row in Verify's checks table. Add every path with no passing row to the table as unverified, with the check that would settle it.
4. **Combine split Risk lanes.** Write one row per safety answer. The weakest rollback and the widest blast radius win, each with its evidence.
5. **Write a recommendation** for each finding: accept, reject, or defer, with one plain reason. Critical with evidence: accept. Code: accept when the fix is small next to the harm, defer when it is a real but separate piece of work. Trivial: accept. Unverified: name the check that settles it, then recommend based on how likely the harm is.
6. **Number the findings** in order: critical, then code, then trivial.
7. **Verdict.** Do not ship with any critical. Ship after changes with only code or trivial. Ship with none.
8. **Confidence**, from evidence only. High: every risky path ran and passed, the requirement is covered, rollback is clear. Medium: core paths ran, but some risk is only reasoned about, or no requirement was found. Low: key paths unverified. Say what would raise it one level.

Write `review.md` in the review folder from [templates/review.md](templates/review.md). Keep its headings and `- Field:` lines exactly as the template has them: the HTML view is built from them.

Then render the visual summary: `python3 <skill-dir>/scripts/render_html.py <review-folder>`. It writes `review.html` beside `review.md`. The page has a verdict card, a confidence meter, finding counts, one card per component, the safety answers, filterable finding cards (each shows its Where, the first sentence of Today, the recommendation and the decision, with a Details panel and a coloured diff), requirement coverage as a checklist, and the verification results. If the script says no findings were parsed and the review has some, the template shape was broken: fix `review.md`, not the script.

Then clean up: stop any containers and processes, `git worktree remove --force` the worktree, and `git branch -D review-<n>` if you created it.

Done when every section of the template is filled from the lane outputs, and every finding has a Where, evidence or an unverified note, a concrete Change, and a recommendation.

## 4. Ask the senior engineer

Each finding becomes one decision. First show the user the summary: verdict, confidence, and the findings grouped by component. Each group starts with one recommendation line (for example `I/O: apply #1 and #4`), then the numbered finding titles with their recommendation. Then offer a shortcut: take all recommendations, or go one by one.

Going one by one, ask in batches of up to four, critical first (with AskUserQuestion in Claude Code, or as a plain numbered list elsewhere). Each question must stand on its own, because the user may see only the question:

- **Question:** title, Where, and Today, then "Apply it?" For example: `#3 Add a 5 second timeout to the payment call (src/payments/client.ts:42). Today a slow provider holds the worker forever. Apply it?` A diff longer than one line goes here too.
- **Header:** `#<n> <severity>`, 12 characters at most.
- **Options:** the recommended one first, marked `(Recommended)`, with its one-line reason. Accept shows the change as a short before/after. Reject shows the finding's If skipped line. Defer says "listed as a follow-up in spec.md".

The user can always type their own answer ("accept, but use 10 seconds"). Record it as accepted with their change.

After the findings, ask two last questions in one batch:

- **Ship:** "Ship after the accepted changes, or hold?"
- **Codex gate:** "Run the Codex gate review (the codex-gate skill) after the spec is implemented?" Header `Codex gate`. Options: `No (Recommended)`, "the implementer finishes on the spec's own checks", first; then `Yes`, "the implementer runs codex-gate before it commits or reports done". The user can type their own answer instead, for example "yes, only for tasks #1 and #3" or a change to how the gate runs. Record it as they wrote it.

Ask the Codex gate question on every review, even when the user answered it on an earlier one. If the user does not answer it, the decision is No.

Stop until the user answers every question.

Write each answer into that finding's `Decision` line in `review.md`, with any note the user gave, and fill the `Decision` and `Codex gate` lines under the verdict. Run the render script again so `review.html` shows the decisions.

Done when every finding, the ship question, and the Codex gate question have a decision.

## 5. Write the spec

Write `spec.md` in the review folder from [templates/spec.md](templates/spec.md). It is the hand-off: another session or any implementation skill (tdd, a plain coding agent) must be able to run it without reading `review.md` or the diff.

- Each accepted finding is one task, with the change as the user accepted it. When they changed the fix, rewrite Change to their version and keep their words as the note. Its "Done when" is the finding's Check.
- Rejected findings go under "Do not change", with the user's reason, so the implementer leaves them alone.
- Deferred findings go under "Follow-ups", one line each.
- Fill "Codex gate" with the user's answer. When it is No, write "Do not run codex-gate for this spec." When it is Yes, write "Run codex-gate after the tasks, before you commit or report done", plus any scope or change the user gave.

Give the user the paths of `review.html`, `review.md` and `spec.md`. Lead with `review.html`: it is the one to open.

Done when every finding appears in exactly one section of `spec.md`.

## Re-review

When the user asks for a re-review after the spec was applied, first rename `review.md` and `spec.md` to `review-<old-head-sha>.md` and `spec-<old-head-sha>.md`. Run the whole review on the new head, and give every lane the old "Do not change" and "Follow-ups" lists to leave alone. In the new `review.md`, fill "Previous spec": each old task fixed (with fresh evidence that its Check passes), still open, or skipped. New findings go through step 4 again, and so does the Codex gate question.

## HTML only

When the user asks only for the visual of a review that already ran (for example `/senior-review html`, or "make the HTML for the last review"), do not run the review again. Find the review folder (the one the user names, else the one for the current repo and branch under `~/.agents/reviews/`), run `python3 <skill-dir>/scripts/render_html.py <review-folder>`, and give the user the path of `review.html`. It reads `review.md` as it is now, so it also shows any decisions filled in since.
