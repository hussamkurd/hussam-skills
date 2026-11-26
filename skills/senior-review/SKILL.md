---
name: senior-review
description: "Read-only senior review of a branch or PR before it ships. Parallel reviewers find what must change, the senior engineer decides on each finding, and the accepted ones become a spec any implementation skill can run."
disable-model-invocation: true
license: MIT
metadata:
  version: 2.0.0
---

# Senior Review

You review a change that ships to production today. The goal is one list: what must change before it is safe and clean to ship. The senior engineer decides on each item, and what they accept becomes a spec.

Run the review on whatever the user points at: a GitHub PR, a Bitbucket PR, or a plain branch. Do not ask whether it is ready for review.

## Rules for the whole run

- **Read-only.** The user's working tree stays as you found it. Code runs in a separate worktree. Every change you want is a finding, not an edit.
- **Review folder.** Everything goes in `~/.agents/reviews/<repo>/<pr-or-branch>/` (for example `~/.agents/reviews/billing-api/pr-412/`): `review.md`, `spec.md`, screenshots, and the worktree. It is outside the repo.
- **Evidence.** A claim that something works or breaks needs proof from this session: a command and its output lines, a `file:line` quote, or a screenshot path. Without proof the claim is **unverified**: say why, and name the check that would settle it. Unverified never counts as working.

## The finding

Every lane returns findings in this shape, and the decision step reads them as they are. Write the title as the change itself, verb first, so the reader knows what will happen from the title alone.

```
Title:      Add a 5 second timeout to the payment call
Severity:   critical | code | trivial
Where:      src/payments/client.ts:42
Today:      fetch() has no timeout, so a slow provider holds the worker forever.
Change:     - const res = await fetch(url)
            + const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
Why:        Stops one slow provider from blocking every checkout.
Evidence:   client.ts:42 quote, and the stub test: request still open after 60s.
If skipped: Checkout hangs during any provider slowdown.
```

Severity:

- **critical**: production breaks, loses data, hangs, leaks, is insecure, misses the requirement, cannot be rolled back, or fails wide.
- **code**: a principle the project follows is broken, the code is over-built, duplicated, or split up for no reason, or tests or logs are missing. A weak safety answer with a small blast radius lands here too.
- **trivial**: churn, dead code, ticket keys or narration in comments, agent and working files added to the change.

Keep a finding only when it fits one of these. Taste-level style and naming are not findings. A clean change with no findings is a fine result.

## 1. Set up

1. **Base branch.** The one the user names. Else the PR base (`gh pr view --json baseRefName,number`). Else `develop`, when `origin/develop` exists and the branch forks from it (its merge-base with `develop` is newer than with the default branch). Else the remote default branch (`git symbolic-ref refs/remotes/origin/HEAD`).
2. **Change set.** `git diff $(git merge-base <base> HEAD)..HEAD`. For a named GitHub PR, `gh pr diff <n>` is the same view. Other hosts need no API.
3. **Committed changes only.** If `git status --porcelain` shows anything, review the commits anyway and note at the top of the report: `uncommitted files not reviewed: <paths>`.
4. **Worktree.** `git worktree add <review-folder>/worktree <head-sha>`. For a PR not checked out, `git fetch origin pull/<n>/head:review-<n>` first.
5. **Requirement.** The PR description. Else the issue whose key (like `ABC-123`) is in the branch name or commits, fetched with an issue-tracker tool when one is connected. Also any spec those link to. If none is found, carry on and note `no requirement found`.
6. **Component map.** Put every changed file in at least one component: Database, Infrastructure, I/O (HTTP, queues, cache, storage), API contract, Security, Core logic, Docs/files.

Done when you can say in two sentences what the change does and what was asked, and you have `Base: <branch> @ <sha>`, `Head: <branch> @ <sha>`, the worktree path, and the component map.

## 2. Review in parallel

Start the four lanes at the same time, as subagents in one message (the Agent tool in Claude Code, or your harness's equivalent). Each lane has its own brief in `lanes/`. The lanes do not depend on each other.

| Lane | Brief | Looks at |
|---|---|---|
| Risk | [lanes/risk.md](lanes/risk.md) | each risky component, the four safety answers |
| Design | [lanes/design.md](lanes/design.md) | the project's principles, simpler shapes |
| Scope | [lanes/scope.md](lanes/scope.md) | requirement coverage, what should not ship |
| Verify | [lanes/verify.md](lanes/verify.md) | typecheck, lint, tests, throwaway checks |

Give each subagent the same packet: the absolute path of its brief and of this file (for the finding shape), the base and head SHAs, the worktree path, the review folder, the diff command, the requirement text, and the component map. Tell it to stay read-only, quote its evidence, and return findings in the shape above.

When the change is big (about 800 changed lines or more, or three or more risky components), split the Risk lane: one subagent per risky component, each told which component it owns.

With no subagents available, run the lanes yourself one after another. The output is the same.

Done when every lane has returned.

## 3. Merge

1. **Check every critical yourself.** Open the `file:line` and read the evidence. Drop or downgrade what does not hold up.
2. **Merge duplicates.** Two lanes often find the same thing from two sides. Keep one finding with both pieces of evidence.
3. **Write a recommendation** for each finding: accept, reject, or defer, with one plain reason. Critical with evidence: accept. Code: accept when the fix is small next to the harm, defer when it is a real but separate piece of work. Trivial: accept. Unverified: name the check that settles it, then recommend based on how likely the harm is.
4. **Number the findings** in order: critical, then code, then trivial.
5. **Verdict.** Do not ship with any critical. Ship after changes with only code or trivial. Ship with none.
6. **Confidence**, from evidence only. High: every risky path ran and passed, the requirement is covered, rollback is clear. Medium: core paths ran, but some risk is only reasoned about, or no requirement was found. Low: key paths unverified. Say what would raise it one level.

Write `review.md` in the review folder from [templates/review.md](templates/review.md).

Done when every finding has a `Where`, evidence or an unverified note, a concrete `Change`, and a recommendation.

## 4. Ask the senior engineer

Each finding becomes one decision. First show the user the summary: verdict, confidence, and the numbered list of finding titles with their recommendation. Then offer a shortcut: take all recommendations, or go one by one.

Going one by one, ask in batches of up to four, critical first (with AskUserQuestion in Claude Code, or as a plain numbered list elsewhere). Each question must stand on its own, because the user may see only the question:

- **Question:** `#3 Add a 5 second timeout to the payment call (src/payments/client.ts:42). Apply it?`
- **Options:** the recommended one first, marked `(Recommended)`, then the rest of: Accept, Reject, Defer to a follow-up.
- **Option text:** what happens if they pick it, in one line. For Accept, show the change as a short before/after.

The user can always type their own answer ("accept, but use 10 seconds"). Record it as accepted with their change.

Write each answer into that finding's `Decision` line in `review.md`, with any note the user gave.

Done when every finding has a decision.

## 5. Write the spec

Write `spec.md` in the review folder from [templates/spec.md](templates/spec.md). It is the hand-off: another session or any implementation skill (tdd, a plain coding agent) must be able to run it without reading `review.md` or the diff.

- Each accepted finding is one task, with its exact change and a check that proves it is done.
- Rejected findings go under "Do not change", with the user's reason, so the implementer leaves them alone.
- Deferred findings go under "Follow-ups", one line each.

Then clean up: stop any containers and processes still running, and `git worktree remove` the worktree. Give the user the paths of `review.md` and `spec.md`.

Done when every finding appears in exactly one section of `spec.md`.

## Re-review

When the user asks for a re-review after the spec was applied, run the whole review again on the new head. In the new `review.md`, mark each task from the old spec as fixed (with fresh evidence that its check now passes), still open, or skipped, and add any new findings. New findings go through step 4 again.
