# Contributing

The full standard is [skills-framework.md](skills-framework.md). Read it before opening a PR. This page is the short version.

## The bar

A skill is merged only if it passes all five tests. Four out of five is a rejection, not a compromise.

| # | Test | What you must show |
| --- | --- | --- |
| 1 | Procedure, not documentation | Name one thing in the skill that is not in the vendor's docs and that cost real time to learn. |
| 2 | Done three times in production | Name the three projects. The same codebase at two points in time counts as one. |
| 3 | The failure is silent or expensive | Describe how the mistake reaches a customer. If the answer is "the build fails", the skill is not needed. |
| 4 | Narrow enough to name in three words | `<vendor>-<noun>-<qualifier>`. If the name could title a whole documentation site, it is too broad. |
| 5 | It ends in verification | The last section says what to run, what result counts as pass, and what to report. |

Put the evidence for tests 1 to 3 in the PR description. Reviewers do not guess at it.

## Closed on sight

Doc-wrapper skills get closed. A restatement of a vendor's getting-started guide, a "best practices" skill that competes with an official pack, a personality or style skill, or a procedure for work that has not shipped yet: all closed, politely, with a link here.

## Mechanics

- One skill per directory under `skills/`. Directory name and frontmatter `name` match exactly, lowercase kebab-case.
- `SKILL.md` under 500 lines, aiming for 150 to 250. Detail goes in `references/`.
- The `description` is the whole triggering mechanism. List the concrete nouns a user would type: table names, error codes, product names, file names. Write it pushy.
- Run `python3 scripts/validate.py` before pushing. CI runs the same script and blocks the merge if it fails.
- No secrets, project refs, real customer names or personal email addresses anywhere, including in examples. Use `example.test`.
- Add a line to `CHANGELOG.md` under Unreleased.

## Reporting a problem with an existing skill

If a vendor changed something a skill assumed, open an issue with the error text and the vendor changelog link. A stale procedure is worse than none, so these get priority over new skills.
