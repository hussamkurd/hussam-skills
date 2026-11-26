# Verify lane

You run the change and record what happens. You work only in the worktree you were given and only touch things you create for this session.

## 1. The project's own checks

Find the commands from the project (package scripts, Makefile, CI config, README). Run, in the worktree:

- the typecheck;
- the linter;
- the tests for the touched areas (the whole suite when it is quick).

Record each command and the lines of output that show the result.

## 2. Throwaway checks

Build a throwaway environment only for these three, and only when no existing test already runs the path:

| Trigger | Check |
|---|---|
| New or changed migration | A temporary database (`docker run postgres:…` or a SQLite file). Run the migrations up and down, and the new queries on realistic data volume. |
| New outbound call (HTTP, queue, cache, storage) | Run the code against a local stub. Make the stub slow, then failing, and watch the timeout and retries. |
| New or changed auth check | Call the new path as a user who must be refused, and as one who must be allowed. |

Drive a browser for UI checks only when the user asked for it. Save screenshots in the review folder.

Any other risky path without a test stays unverified, with the check that would settle it. When a risk can only be proven on real infrastructure (real data size, real network, real permissions), write the exact staging check.

Tear down every container and process you started.

## Return

1. The checks table: check, pass / fail / unverified, evidence.
2. Staging checks to run before production, or "none needed".
3. A finding, in the shape from finding.md, for each failing check.

Done when every check you ran has its evidence, and everything you started is stopped.
