# Senior Review: <PR title or branch name>

Base: <branch> @ <sha>    Head: <branch> @ <sha>
Project principles: <from the Design lane>
<uncommitted files not reviewed: paths   (only when there are any)>

## Summary

<Two to four plain sentences: what the change does, what was asked, why the verdict.>

Verdict: Ship | Ship after changes | Do not ship
Confidence: High | Medium | Low. <What it rests on. What would raise it.>
Decision: ship | hold. <n> accepted, <n> rejected, <n> deferred. <user's note>
Codex gate: no | yes. <user's note, scope or change>

## Components

| Component | Worst finding | Recommendation | What changed and what it touches |
|---|---|---|---|
| Database | critical #1 | apply #1 | ... |
| I/O | none | ship as is | ... |

## Safety answers

| Question | Answer | Evidence |
|---|---|---|
| Rollback | <exact undo; data loss yes/no> | ... |
| Feature gate | <flag and default, or none and whether one is needed> | ... |
| Must not change | <each invariant and how it holds> | ... |
| Blast radius | <scope; fails open or closed; cascades?> | ... |

## Requirement coverage

- covered: <point> (`file:line`)
- gap: <point> → #<n>

<or: no requirement found. The change appears to ...>

## Verification

| Check | Result | Evidence |
|---|---|---|
| <command> | pass / fail / unverified | <output lines or screenshot path> |

Staging checks before production: <exact checks, or none needed>

## Previous spec (re-review only)

| Task | fixed / still open / skipped | Evidence |
|---|---|---|

## Findings

### Critical

#### #1 <Title: the change, verb first>

- Where: `path:line`
- Today: <what the code does now>
- Change:
  ```diff
  - old
  + new
  ```
- Why: <the failure it prevents>
- Evidence: <output, quote, or screenshot path; or unverified + the check that settles it>
- Check: <command, test or grep that passes once the change is in>
- If skipped: <what happens>
- Recommendation: Accept | Reject | Defer. <one reason>
- Decision: <filled in at step 4, with the user's note>

### Code

#### #2 <Title>

<same fields>

### Trivial

#### #3 <Title>

- Where: `path:line`
- Change: <one-line diff, or "drop the file from the change">
- Recommendation: Accept
- Decision:

<Write "none" under an empty severity.>
