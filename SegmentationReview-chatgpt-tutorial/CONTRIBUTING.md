# Contributing to SegmentationReview

Thank you for contributing! This document explains our workflow, branch strategy, and commit conventions.

---

## Table of Contents

1. [Branch strategy](#branch-strategy)
2. [Commit conventions](#commit-conventions)
3. [Pull Request process](#pull-request-process)
4. [Code review etiquette](#code-review-etiquette)
5. [Using LLMs for commits and PRs](#using-llms-for-commits-and-prs)

---

## Branch strategy

We use a lightweight **trunk-based** branching model:

```
main
 └── develop          ← integration branch
      ├── feature/short-description
      ├── fix/short-description
      ├── refactor/short-description
      └── docs/short-description
```

| Branch prefix | When to use |
|---|---|
| `feature/` | New functionality |
| `fix/` | Bug fixes |
| `refactor/` | Code restructuring without behaviour change |
| `docs/` | Documentation-only changes |
| `chore/` | CI, tooling, dependency updates |

### Rules

- **Never push directly to `main`** — always open a Pull Request
- Branch names use lowercase kebab-case: `feature/export-json-summary`
- Delete the branch after merge

---

## Commit conventions

We follow **Conventional Commits** (`type(scope): description`).

```
feat(review): add accept/reject keyboard shortcuts
fix(loader): handle missing NRRD metadata gracefully
docs(tutorial): add rebase section
refactor(exporter): split CSV and JSON into separate modules
test(loader): add unit tests for NIfTI edge cases
chore(ci): bump black to 24.x
```

### Rules

- **Subject line ≤ 72 characters**, imperative mood ("add" not "added")
- Leave a blank line between subject and body
- Body explains **why**, not just what
- Reference issues with `Closes #42` or `Related to #17`

#### Full commit example

```
feat(exporter): add JSON export with inter-rater scores

Previously only CSV export was available, which made it hard to
consume results in downstream Python pipelines.

JSON format follows the draft SegReview schema discussed in #34.
Backwards-compatible: CSV export unchanged.

Closes #34
```

---

## Pull Request process

1. Open PR against `develop` (not `main`)
2. Fill in the PR template completely
3. Assign at least one reviewer
4. Address all review comments before merging
5. Use **Squash and merge** for feature branches, **Rebase and merge** for hotfixes

---

## Code review etiquette

- Be specific: quote the line, explain the concern
- Distinguish blockers from suggestions: use `[blocker]` or `[nit]` prefixes
- Approve when you're genuinely happy, not just to unblock

---

## Using LLMs for commits and PRs

LLMs are great for drafting commit messages and PR descriptions. A good prompt:

```
Given this diff, write a Conventional Commit message.
- type: feat | fix | refactor | docs | test | chore
- subject line max 72 chars, imperative mood
- body: explain why, not what
- reference issue #XX if relevant

<paste diff here>
```

Always review and edit the LLM output — you own the commit message.
