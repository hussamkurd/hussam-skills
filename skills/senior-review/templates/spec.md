# Spec: review fixes for <PR title or branch name>

Repo: <repo path>    Branch: <branch>    Reviewed at: <head sha>
Source: <path to review.md>

## Goal

<One or two sentences: what the change is for, and that these tasks make it safe to ship.>

## Context the implementer needs

- <The project rules that apply: test command, lint command, error type, logger, etc.>
- <Anything from the review that every task relies on, said once.>

## Tasks

Do them in order. Critical first. Each task is independent unless it says otherwise.

### 1. <Title: the change, verb first>   (from review #<n>, critical)

- File: `path:line`
- Change:
  ```diff
  - old
  + new
  ```
  <Or, for a larger change, the exact shape: which functions move where, what the new signature is.>
- User's note: <only when they changed the recommendation>
- Done when: <a check anyone can run: a test name that now passes, a command and its expected output, a grep that returns nothing>

### 2. ...

## Do not change

Findings the reviewer raised and the senior engineer rejected. Leave them as they are.

- <Title> (`path:line`): <the user's reason>

## Follow-ups

Accepted as real but out of this change. Not part of this work.

- <Title> (`path:line`): <one line>

## Finished when

- Every task's "Done when" check passes.
- <The project's typecheck, lint, and test commands> pass.
- Nothing under "Do not change" was touched.
