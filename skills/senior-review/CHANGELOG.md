# Changelog

## 2.3.0

- Every review writes `review.html`, a visual summary, with `scripts/render_html.py`: verdict, confidence meter, finding counts, component cards, safety answers, filterable finding cards with coloured diffs, requirement checklist and verification bar. Light and dark, one self-contained file.
- The page is built from `review.md` alone, so it can be made again at any time without a new review: `/senior-review html`, or run the script on a review folder.
- The page is rendered again after the decisions, so it shows them.
- The old hand-written `review.html` (made only on request) is replaced by the script.

## 2.2.0

- Step 4 asks on every review whether the implementer runs the Codex gate (codex-gate skill). The default is no.
- The answer goes into `review.md` under the verdict and into a new "Codex gate" section in `spec.md`.
- Re-review asks the Codex gate question again.

## 2.1.0

Fixes from a senior review of 2.0.0.

- The finding shape and evidence rule move to `finding.md`, so lanes read only what they need.
- New `Check` field on each finding; it becomes the spec's "Done when".
- The merge step matches Risk's risky paths with Verify's checks, and combines split Risk lanes into one safety table.
- Questions show today's behaviour, the reason for the recommendation, and what happens if skipped.
- The summary is grouped by component, with one recommendation per component.
- The run asks "ship or hold?" at the end and waits for every answer.
- A change the user types into an answer is written into the spec task itself.
- Only the Verify lane runs commands, and no lane connects to outside databases or services.
- The diff is built from the head SHA, so a PR review from another branch works.
- The worktree is removed right after the merge, and an old one is cleared at setup.
- A failed lane is run again, then by the main agent, else marked unverified with Low confidence.
- Re-review keeps the old files and skips findings already rejected or deferred.
- Risky components and their signals are defined in the component map.
- `review.html` is back, made only when the user asks.

## 2.0.0

- Split the review into four parallel subagent lanes (risk, design, scope, verify), each with its own brief in `lanes/`. The risk lane splits per component on big changes.
- One finding shape for every lane, with the title written as the change itself.
- The main agent checks every critical finding, merges duplicates, and adds a recommendation to each.
- New decision step: one standalone question per finding (accept, reject, defer, or the user's own change).
- New `spec.md` hand-off: accepted findings as tasks with a "done when" check, rejected ones as "do not change", deferred ones as follow-ups.
- The `review.md` template moved to `templates/`; new `templates/spec.md`.
- Shorter, plainer wording; no emoji.
- Breaking: the `### Decision` section is gone; the hand-off is `spec.md`, not `review.md`.
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
