# Spec: review fixes for <PR title or branch name>

Repo: <repo path>    Branch: <branch>    Reviewed at: <head sha>
Source: <path to review.md>

## Goal

<One or two sentences: what the change is for, and that these tasks make it safe to ship.>

## Context the implementer needs

- <The project rules that apply: test command, lint command, error type, logger, etc.>
- <Anything from the review that every task relies on, said once.>

## Tasks

Do them in order. Each task is independent unless it says otherwise.

### 1. <Title: the change, verb first>   (from review #<n>, critical)

- File: `path:line`
- Change:
  ```diff
  - old
  + new
  ```
  <Or, for a larger change, the exact shape: which functions move where, what the new signature is.>
- User's note: <only when they edited the change; Change above already includes it>
- Done when: <the finding's Check>

### 2. ...

## Do not change

Findings the reviewer raised and the senior engineer rejected. Leave them as they are.

- <Title> (`path:line`): <the user's reason, else the recommendation's reason>

## Follow-ups

Accepted as real, but left for separate work.

- <Title> (`path:line`): <one line>

## Codex gate

<No: "Do not run codex-gate for this spec."  Yes: "Run codex-gate after the tasks, before you commit or report done." Add the user's scope or change, if any.>

## Finished when

- Every task's "Done when" check passes.
- <The project's typecheck, lint, and test commands> pass.
- Nothing under "Do not change" was touched.
- If "Codex gate" says yes, codex-gate approved the change.

<Write "none" under an empty section.>
