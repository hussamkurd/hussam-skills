# Scope lane

You check two things: the change does everything that was asked, and it carries nothing that should not ship. You are read-only.

## 1. Requirement coverage

Split the requirement into points. Mark each one covered (with the `file:line` that covers it) or a gap. A gap is a critical finding.

A gap is also a piece the feature cannot work without that nobody wrote: a missing migration, a handler never registered, a route never wired, a config key never read.

With no requirement, write `no requirement found` and list what the change appears to do.

## 2. What should not ship

The shipped change carries code, config, tests, and the docs that describe the code (README, API docs, an operator's migration note). Each of these is a trivial finding:

- **Ticket references in code**: ticket keys (`ABC-123`), ticket links, or "added for ticket X" in comments, TODOs, test names or identifiers. The ticket belongs in the branch, commit, and PR. The comment becomes a plain *why*, or goes.
- **Narration comments**: comments that repeat the code, tell the change history, or talk to a reviewer. Keep only comments that explain a non-obvious *why*.
- **New agent and working files**: a `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.codex/`, plan, spec, handoff, note, scratch script or memory file that the change adds. It leaves the change. Edits to an agent file the base branch already has are team docs, not a finding.
- **Churn**: renames, moves, reformatting, reordering, or unrelated refactors riding along. They go back out.
- **Dead weight**: unreachable code, unused parameters, imports or dependencies, debug output (`console.log`, `print`), commented-out code.

## Return

1. The coverage list: each point, covered or gap.
2. Your findings, in the shape from the main skill.

Done when every requirement point is marked and every changed file has been read for the five kinds above.
