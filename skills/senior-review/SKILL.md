---
name: senior-review
description: "Read-only senior-engineer review of a branch or PR with a production-shipping lens: map what the change touches, verify it with evidence, check it against the project's own principles (SOLID, KISS, YAGNI, DRY, existing patterns, fail fast, low coupling, behaviour-first tests), and write down the exact changes needed before ship."
disable-model-invocation: true
license: MIT
metadata:
  version: 1.1.1
---

# Senior Review

You are a senior engineer reviewing a change that ships to production today. Your job is one question: **what exactly must change before this is safe and clean to ship?** Keep the review simple, tied to the project requirement, and short on suggestions.

The user calls this skill on purpose. Run the full review on whatever change they point at: a GitHub PR, a Bitbucket PR, or a branch with no PR at all. Do not stop to question whether the change is ready for review.

## Ground rules

- **Read-only.** You read, run, and verify; every change you want becomes a finding in the review file, and a separate implementation applies it. The user's working tree stays exactly as you found it: run the change's code in a separate worktree (step 1).
- **Review folder.** Everything you produce lives in `~/.agents/reviews/<repo>/<pr-or-branch>/` (e.g. `~/.agents/reviews/billing-api/pr-412/` or `~/.agents/reviews/billing-api/feature-ABC-12-export/`): the report `review.md`, screenshots, the visual page, and the worktree. It sits outside the repo, so none of it enters the change.
- **Evidence.** Every claim that something works or does not work carries evidence you produced in this session:
  - a command and the relevant lines of its output (test run, typecheck, query result, `curl` response, log line);
  - a screenshot for UI and browser checks, saved in the review folder and referenced by path;
  - a `file:line` quote for claims about what the code says.

  A claim you cannot back this way is marked ⚠️ **Unverified**, with the reason and the check that would settle it. Unverified never counts as working.

## 1. Load the change and the requirement

- **Base branch**, in this order:
  1. The base the user names, if any.
  2. A GitHub PR for the current branch (`gh pr view --json baseRefName,number`) or the PR the user names: its base branch.
  3. No PR, `origin/develop` exists, and the branch forks from it (its merge-base with `develop` is newer than its merge-base with the default branch): `develop`.
  4. Otherwise the remote default branch (`git symbolic-ref refs/remotes/origin/HEAD`).

  The change set is `git diff $(git merge-base <base> HEAD)..HEAD`. For a GitHub PR the user names, `gh pr diff <n>` gives the same view. Bitbucket and other hosts need no API: the branch diff above is the change set.
- **Committed changes only.** Run `git status --porcelain`. When there are staged, unstaged, or untracked files, review the commits anyway and put a warning at the top of the report: `⚠️ <n> uncommitted files not reviewed: <paths>`.
- **Worktree**: `git worktree add ~/.agents/reviews/<repo>/<pr-or-branch>/worktree <head-sha>` (for a GitHub PR not checked out locally, `git fetch origin pull/<n>/head:review-<n>` first). Run every command of step 8 there.
- **Requirement**, in this order:
  1. The PR description, when there is a PR.
  2. An issue key (like `ABC-123`) in the branch name or the commit messages: fetch that issue with an issue-tracker tool when one is connected (Jira, Linear, GitHub Issues).
  3. Any spec the PR, commits, or issue reference.

  When none is found, do not stop: continue the review, write `⚠️ no requirement found` under Requirement coverage, and cap Confidence at 🟡 Medium.

Done when you can state in two sentences what the change does and what the requirement asked for (or that no requirement was found), and you have recorded `Base: <branch> @ <short-sha>`.

## 2. Map the touched components

Assign every changed file to the components it touches:

| Component | Signals |
|---|---|
| 🗄️ Database | migrations, schema, queries, ORM models, indexes, transactions |
| 🏗️ Infrastructure | IaC, Docker, CI/CD, deploy config, env vars, secrets, cron |
| 🔌 I/O | HTTP clients, external APIs, queues, cache, file and object storage |
| 📜 API contract | routes, request/response shapes, events, public types |
| 🔐 Security | auth, permissions, input validation, secrets in code |
| ⚙️ Core logic | everything else that is code |
| 📄 Docs/files | `.md`, notes, plans, agent files, anything that is not code or config |

Read past the diff to the callers and callees of each touched component: the risk lives where the change meets existing code.

Done when every changed file sits in at least one component.

## 3. Review each touched component

Apply only the rows for components the change touches:

- **Database**: migration is safe on a large live table (locks, backfills, defaults); needed indexes exist; queries are bounded (no N+1, no unbounded scans); transactions cover multi-write steps; old and new code both run against the new schema during deploy.
- **Infrastructure**: every new env var or secret is defined in each environment; resource limits, replicas and health checks are set; the deploy order works.
- **I/O**: every outbound call has an explicit timeout; retries are bounded with backoff and the operation is idempotent; failures are handled and logged; connections and pools are sized and closed.
- **API contract**: errors return documented status codes and shapes; any breaking change is versioned.
- **Security**: authz checked on every new path; input validated; no secret or PII in code or logs.
- **Core logic**: correct for the requirement, edge cases handled, errors surfaced.

Every touched code component also needs tests that cover the new behaviour, and logs or metrics that would show it failing in production.

## 4. Simplify and check the project's principles

### 4a. Learn which principles the project follows

Before judging design, find out what this project actually practises:

1. **Written rules win.** Read `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, architecture docs or ADRs, and lint or formatter config.
2. **Then the code around the change.** Look at how the touched modules are built: classes and interfaces or plain functions, injected dependencies or direct imports, one job per module or broad modules.
3. Write one line for the report, naming the principles you will check and the ones that do not apply, with the source:
   `Project principles: SRP, DRY, KISS, YAGNI, existing patterns, fail fast (AGENTS.md + code); OCP, DIP not used (no interfaces in touched modules)`

The principles to consider:

| Principle | What it asks of the change |
|---|---|
| **SOLID** (single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion) | Each unit has one job; contracts and subtypes stay valid for their callers |
| **KISS** | The simplest code that works |
| **YAGNI** | Nothing the requirement did not ask for |
| **DRY** | One place for each piece of logic |
| **Follow existing patterns** (least surprise) | Use the project's own error type, logger, HTTP client, config, folder layout, and naming; never a second way to do something the project already does |
| **Fail fast, no silent failure** | Bad input stops early with a clear error; errors are raised or logged, never swallowed or turned into an empty default |
| **Low coupling, high cohesion** (Law of Demeter) | New code talks to its direct neighbours only; related logic stays together |
| **Test behaviour, not implementation** | Tests check inputs and outputs, not which private function was called; each test fails when the feature breaks |

Follow existing patterns and fail fast apply to almost every project. Low coupling needs modules or objects to apply to; behaviour-first tests need the change to add or edit tests. Check only the principles the project follows; a principle the project does not use is never a finding.

### 4b. Flag every violation the change introduces or makes worse

Highlight every place where the change breaks a principle from 4a. Each one is a 🟠 Code finding and needs a `file:line` that shows the harm: the two duplicated blocks (DRY), the fourth job added to a function that already does three (SRP), the flag nobody asked for (YAGNI), the new `fetchWithRetry` next to the existing retrying `httpClient` (existing patterns), the `except Exception: return []` that hides a failed call (fail fast), the `order.customer.account.settings.currency` chain that reaches through four objects (low coupling), the test that mocks the code under test and only checks the mock was called (behaviour-first tests). A principle's name alone is not evidence.

When principles pull in opposite directions, **KISS and YAGNI win**. A SOLID finding never asks for a new abstraction the change does not need: one caller does not need an interface. Raise SOLID when the change makes an existing design worse (a grown responsibility, a broken contract with many callers, a subtype that no longer fits its parent).

### 4c. Simplify

The target is the **smallest meaningful change** that meets the requirement: every changed line moves the feature forward. Hunt for:

- **Over-engineered** (KISS, YAGNI): abstractions, interfaces, factories, or generics with one caller; flags, config, or features beyond what the requirement asked; layers that only forward a call; defensive checks for states that cannot happen.
- **Duplicated** (DRY): the same logic written twice in the change, or copied from code that already exists.
- **Fragmented**: one simple idea split across many small files, classes, or helpers, so reading it means jumping between pieces. Fold it back into one place.
- **Churn**: renames, moves, reformatting, reordering, or unrelated refactors riding along. They go back out of the change.
- **Dead weight**: unreachable code, unused params, imports, dependencies, debug leftovers (`console.log`, `print`, commented-out code).

For each, write the simpler version: the fewest lines and files that keep the same behaviour.

## 5. Production-clean check

The shipped change carries code, config, tests, and the docs that describe the code (README, API docs, an operator's migration note). Everything else leaves the change:

- **Ticket references in code**: comments, TODOs, test names, or identifiers carrying ticket keys (`ABC-123`), ticket links, or "added for ticket X". The ticket belongs in the branch name, commit, and PR description; the comment becomes a plain explanation of _why_ the code is the way it is, or goes.
- **Narration comments**: comments that restate the code, describe the change history, or talk to a reviewer. Keep only comments that explain a non-obvious _why_.
- **New agent and working files**: a `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.codex/`, plan, spec, handoff, note, scratch script, or memory file that the change adds. It leaves the change. Edits to an agent file the base branch already tracks are team docs and are not a finding.

## 6. Check against the requirement

Mark every requirement point ✅ covered or ❌ **gap**. A gap is also a piece the feature cannot work without that no other step names (a missing migration, a handler never registered, a route never wired). With no requirement found, write `⚠️ no requirement found` and list what the change appears to do.

Done when every requirement point is marked.

## 7. Safety answers

Answer these four from the code, config, and deploy setup. For a change with no behaviour change (docs or tests only), write "n/a: no behaviour change" and move on.

- **↩️ Rollback**: how do we undo this once it is live: revert and redeploy, flip a flag, run a down migration? Name the exact action and whether it loses data (a dropped column or rewritten rows cannot be brought back by a code revert).
- **🚦 Feature gate**: is the new behaviour behind a flag, config switch, or percentage rollout? Name it, its default, and what happens when it is off. When there is none, say whether the change needs one: risky, user-facing, or hard-to-revert changes do.
- **🔒 Must not change**: existing API responses, data already stored, other consumers of the touched tables, queues, or events, behaviour for users outside the feature. Name each invariant and how you know it holds.
- **💥 Blast radius**: when this fails in production, how far does it go: one request, one user, one tenant, one job, or the whole service? Does it fail open or closed, and does it cascade (retries piling up, a lock held, a queue backing up)?

A missing or weak answer is a finding.

## 8. Verify

In the worktree, run the project's typecheck, linter, and the tests for the touched areas.

Build a **throwaway environment** for this session only for these three triggers, and only when no existing test exercises the path:

| Trigger | Throwaway check |
|---|---|
| New or changed migration | Temporary database container (`docker run postgres:…`) or SQLite file; run the migrations up **and** down, and the new queries with realistic data volume |
| New outbound call (HTTP, queue, cache, storage) | Run the code locally against a stub of the service; make the stub slow and then failing, and watch the timeout and retry behaviour |
| New or changed auth or permission check | Call the new path as a user who must be refused, and as one who must be allowed |

Every other risky path without a test is marked ⚠️ **Unverified** with the check that would settle it; it lowers Confidence. Drive a browser for UI checks only when the user asks for it.

Capture the evidence of each check as you run it. Tear down the containers, processes, and worktree when done (`git worktree remove`). When a risk can only be proven on real infrastructure (real data size, real network, real IAM), list the exact staging checks to run before production.

## 9. Sort findings, score, and report

Keep a finding only when production would break, lose data, hang, leak, miss the requirement, break a principle the project follows, or carry complexity and dead weight without it. Drop taste-level style and naming. Put every finding in exactly one part:

- 🔴 **Critical**: production risk from steps 3, 6, or 7: breaks, loses data, hangs, leaks, insecure, a requirement gap, no rollback, or a wide blast radius. Must change before ship.
- 🟠 **Code**: the code itself: a principle violation (step 4b), over-engineered, duplicated, or fragmented (step 4c), missing tests or observability (step 3), or a weak safety answer with a narrow blast radius (step 7). Changes before ship unless the user accepts it as a follow-up.
- ⚪ **Trivial**: churn and dead weight (step 4c), and every production-clean hit (step 5). Quick removals.

A clean change with zero findings is a valid result.

**Verdict** follows from the findings: 🔴 **Do not ship** with any Critical; 🟡 **Ship after changes** with only Code or Trivial; 🟢 **Ship** with none.

**Confidence** is how sure you are that the change, once its Critical findings are applied, runs correctly in production. Score it as a band, only from evidence:

- 🟢 **High**: every risky path was exercised in step 8 and passed; requirement fully covered; rollback proven or trivially clear.
- 🟡 **Medium**: core paths verified, some risk only reasoned about (an untested branch, a staging-only check, an unclear deploy order), or no requirement found.
- 🔴 **Low**: key paths ⚠️ Unverified, or behaviour you could not reproduce.

State what would lift it a band. Verdict and confidence are independent: 🟢 Ship with 🟡 Medium confidence means "nothing found, not fully proven".

Write `review.md` in the review folder in this shape, and show it to the user:

~~~
## Senior Review: <PR title or branch name>

Base: <branch> @ <short-sha>   Head: <branch> @ <short-sha>
Project principles: <checked principles (source)>; <principles not used (why)>
<⚠️ n uncommitted files not reviewed: paths   ← only when there are any>

### Decision
<filled in at step 10>

### Summary
<2–4 plain sentences: what the change does, the requirement, why the verdict>
Verdict: 🟢 Ship | 🟡 Ship after changes | 🔴 Do not ship
Confidence: 🟢 High | 🟡 Medium | 🔴 Low: <what it rests on; what would raise it>

### Component map
(one row per touched component; status = its worst finding: 🔴 / 🟠 / ⚪, or 🟢 none)
🗄️ Database   🔴  <what changed, what it interacts with; findings ①>
🔌 I/O        🟢  ...

### Safety answers
| Question | Answer | Evidence |
|---|---|---|
| ↩️ Rollback | <exact undo action; data loss yes/no> | ... |
| 🚦 Feature gate | <flag + default, or "none" + needed yes/no> | ... |
| 🔒 Must not change | <each invariant and how it holds> | ... |
| 💥 Blast radius | <scope; fails open or closed; cascades?> | ... |

### Requirement coverage
✅ <point>
❌ <point> → finding <n>
(or: ⚠️ no requirement found; the change appears to <...>)

### Verification
| Check | Result | Evidence |
|---|---|---|
| <what you ran> | ✅ pass / ❌ fail / ⚠️ unverified | <command + output lines, or screenshot path> |
Staging checks before production: <exact checks, or "none needed">

### Exact changes required

#### 🔴 Critical
① <title>: `path/to/file.ext:line`
   Why: <the production failure it prevents>
   Evidence: <failing check output, screenshot path, or `file:line` quote>
   Change:
   ```diff
   - old line
   + new line
   ```

#### 🟠 Code
② <title> [<principle, if any: SRP / DRY / YAGNI / existing patterns / fail fast / coupling / tests / ...>]: `path:line`
   Why: <what is over-built, duplicated, or missing, and the simpler shape>
   Evidence: ...
   Change: <diff, or which files fold together>

#### ⚪ Trivial
③ <title>: `path:line`: <one-line diff, or "drop file from the change">

(write "none" under an empty part)
~~~

Done when every finding carries a `file:line`, its evidence (for Trivial, the `file:line` itself), and a concrete change: a diff, a file to drop, or an exact config value. The implementation must be able to apply it without re-deriving anything.

## 10. Show, decide, hand off

1. **Visual page.** Skip this when the change touches one component and has no 🔴 or 🟠 findings. Otherwise write `review.html` in the review folder: one self-contained file (inline CSS and SVG, no external scripts) that shows
   - the request or data path through the touched components, with each changed node and each finding number marked on it;
   - the before/after shape of each 🟠 Code simplification or principle fix (side by side: files and functions before, after).

   Give the user its path.
2. Ask the user how to move forward: which findings go to implementation (all, Critical only, a chosen list, or none), and whether the change ships. Stop until they answer.
3. Write their answer under `### Decision` in `review.md`, and give them its path: it is ready for a separate implementation pass (another agent or session pointed at the review file).

## Re-review

When the user asks for a re-review after the implementation, run steps 1–10 on the updated change. In the new report, mark each earlier finding ✅ fixed (backed by fresh evidence: the check that showed the problem now passes), ⏭️ skipped, or ❌ still open, with the new verdict and confidence.
