# senior-review

A read-only agent skill that reviews a branch or pull request the way a senior engineer would before a production deploy. It answers one question: what must change before this is safe and clean to ship? Then it lets you decide on each finding, and turns your decisions into a spec.

## How it works

1. **Set up.** Finds the base branch (the one you name, the PR base, `develop`, or the default branch), the diff, and the requirement (PR description or linked issue). Checks out the head in a separate git worktree.
2. **Review in parallel.** Four subagents run at once:
   - Risk: database, infrastructure, I/O, API, security and core logic, plus rollback, feature gate, invariants and blast radius.
   - Design: the principles the project actually follows (SOLID, KISS, YAGNI, DRY, existing patterns, fail fast, low coupling, behaviour tests), and the smaller version of the change.
   - Scope: requirement coverage, and what should not ship (ticket keys in code, narration comments, agent files, churn, dead code).
   - Verify: typecheck, lint, tests, and throwaway checks for migrations, outbound calls and auth.
3. **Merge.** Checks every critical finding, merges duplicates, and adds a recommendation to each.
4. **You decide.** A summary grouped by component, then one clear question per finding: what changes, where, what the code does today, and what happens if you skip it. Accept, reject, defer, or change it. Last: ship or hold.
5. **Spec.** Accepted findings become tasks with a "done when" check. Rejected ones are listed as "do not change", deferred ones as follow-ups. Any implementation skill or agent can run it.

Output goes to `~/.agents/reviews/<repo>/<pr-or-branch>/`, outside the repo: `review.html` (a visual summary to open in a browser), `review.md` and `spec.md`. Your working tree is never touched.

## Install

```sh
npx skills add hussamkurd/hussam-skills -g -s senior-review
```

## Use

The skill runs only when you call it:

```
/senior-review            # current branch
/senior-review 412        # GitHub PR #412
/senior-review base=main  # force a base branch
/senior-review html       # rebuild review.html from the last review.md, no new review
```

You can also render the page yourself from any finished review:

```sh
python3 scripts/render_html.py ~/.agents/reviews/billing-api/pr-412
```

Then hand the spec to an implementation pass, for example: "implement `~/.agents/reviews/billing-api/pr-412/spec.md`".

## Files

- `SKILL.md`: the steps.
- `finding.md`: the finding shape, severities and evidence rule.
- `lanes/`: the brief for each parallel reviewer.
- `templates/`: the shape of `review.md` and `spec.md`.
- `scripts/render_html.py`: turns `review.md` into `review.html` (Python 3.8+, standard library only).

## Requirements

- `git` (required)
- `python3` (for `review.html`)
- `gh` (optional, for GitHub PRs)
- `docker` (optional, for throwaway databases)
- An issue-tracker tool (optional, to fetch the linked ticket)
- Subagent support (optional; without it the lanes run one after another)
