# hussam-skills

Public skills repo. Skills live in `skills/<name>/SKILL.md`.

## Versioning rule (every push)

Every push that changes anything must update a version and its changelog in the same push. Never push without both.

- **Changed a skill** (any file in `skills/<name>/`): bump `metadata.version` in its `SKILL.md` and add an entry at the top of `skills/<name>/CHANGELOG.md`.
- **Every push**: bump `version` in `.claude-plugin/plugin.json` and add an entry at the top of the root `CHANGELOG.md`, listing what changed and which skill versions moved.
- **New skill**: start at `1.0.0` with its own `CHANGELOG.md`, and add a row to the skill table in `README.md`.
- Use semver: patch `x.y.Z` for fixes and wording, minor `x.Y.0` for new checks or features, major `X.0.0` when a skill's behaviour or output format changes in a way users must adapt to.
- Changelog entries: `## <version>` then short bullets in plain English.

Before pushing, check: `git diff origin/main --stat` shows a changed `CHANGELOG.md` and `plugin.json`, and `claude plugin validate .` passes.

## Commits

`SKILLS: short lowercase summary`, 5 lines max, no agent or model information.
