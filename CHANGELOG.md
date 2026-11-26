# Changelog

Repo version, as in `.claude-plugin/plugin.json`. Each skill also keeps its own `CHANGELOG.md`.

## 2.0.0

- senior-review 1.1.1 → 2.3.0: four parallel review lanes, one question per finding with a recommendation, and a `spec.md` hand-off. 2.1.0 fixes the gaps a review of 2.0.0 found.
- senior-review 2.2.0 asks whether to run the Codex gate; 2.3.0 writes a visual `review.html` on every review with `scripts/render_html.py`, and `/senior-review html` rebuilds it from `review.md` without a new review.
- senior-review 2.0.0 was pushed without this entry; this release covers both.

## 1.1.1

- Add the MIT license.
- Add `AGENTS.md` with the rule: every push bumps a version and its changelog.
- senior-review 1.1.0 → 1.1.1.

## 1.1.0

- senior-review 1.0.0 → 1.1.0: four new principles (existing patterns, fail fast, low coupling, behaviour-first tests).

## 1.0.0

- First release with senior-review 1.0.0.
