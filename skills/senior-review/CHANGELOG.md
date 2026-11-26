# Changelog

## 2.0.0

- Split the review into four parallel subagent lanes (risk, design, scope, verify), each with its own brief in `lanes/`. The risk lane splits per component on big changes.
- One finding shape for every lane, with the title written as the change itself.
- The main agent checks every critical finding, merges duplicates, and adds a recommendation to each.
- New decision step: one standalone question per finding (accept, reject, defer, or the user's own change).
- New `spec.md` hand-off: accepted findings as tasks with a "done when" check, rejected ones as "do not change", deferred ones as follow-ups.
- Templates for `review.md` and `spec.md` moved to `templates/`.
- Shorter, plainer wording; fewer emoji.
- Removed the default `review.html` visual page.

## 1.1.1

- Add the MIT license to the skill metadata.

## 1.1.0

- Add four principles to step 4: follow existing patterns, fail fast with no silent failure, low coupling and high cohesion, test behaviour not implementation.
- Each comes with an example of the harm a finding must show.

## 1.0.0

- First public version.
- Reviews a GitHub PR, a Bitbucket PR, or a plain branch; picks the base branch (named base, PR base, `develop`, or the default branch) and prints it.
- Reviews committed changes only and warns about uncommitted files.
- Finds the requirement from the PR description or an issue key in the branch name or commits; continues with a warning when none is found.
- Learns which principles the project follows (SOLID, KISS, YAGNI, DRY) and flags every violation with `file:line` evidence; KISS and YAGNI win over SOLID.
- Builds throwaway environments only for migrations, new outbound calls, and auth changes.
- Confidence is a band (High / Medium / Low), not a percentage.
- Writes its own self-contained `review.html`; no dependency on other skills.
