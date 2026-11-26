# senior-review

A read-only agent skill that reviews a branch or pull request the way a senior engineer would before a production deploy. It answers one question: **what exactly must change before this is safe and clean to ship?**

## What it does

- Works on a GitHub PR, a Bitbucket PR, or a branch with no PR (diffs against the PR base, `develop`, or the default branch).
- Maps the change to components (database, infrastructure, I/O, API contract, security, core logic, docs) and reviews each one.
- Learns the principles the project follows (SOLID, KISS, YAGNI, DRY, existing patterns, fail fast, low coupling, behaviour-first tests) and flags the violations with evidence.
- Checks the change against its requirement (PR description or linked issue).
- Answers four safety questions: rollback, feature gate, invariants, blast radius.
- Verifies claims by running typecheck, lint, and tests in a separate git worktree, plus throwaway environments for migrations, outbound calls, and auth changes.
- Writes `review.md` (and a `review.html` visual for non-trivial changes) to `~/.agents/reviews/<repo>/<branch>/`, outside the repo, with the exact diff for every finding.

It never edits your working tree. A separate implementation pass applies the findings.

## Install

Copy this folder into your agent's skills directory, for example:

```sh
npx skills add hussamkurd/hussam-skills -g -s senior-review
```

## Use

The skill runs only when you call it:

```
/senior-review            # current branch
/senior-review 412        # GitHub PR #412
/senior-review base=main  # force a base branch
```

## Requirements

- `git` (required)
- `gh` (optional, for GitHub PRs)
- `docker` (optional, for throwaway databases)
- An issue-tracker tool (optional, to fetch the linked ticket)
