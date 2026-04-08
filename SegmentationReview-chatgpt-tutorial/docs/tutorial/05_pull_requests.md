# Module 5 — Pull Requests

A **Pull Request (PR)** is a proposal to merge one branch into another.  
On GitHub it is also the home of code review — the conversation between author and reviewer.

---

## Opening a PR

### Via GitHub CLI (recommended)

```bash
# Push your branch first
git push -u origin feature/export-json-summary

# Open a PR interactively
gh pr create

# Or in one line
gh pr create \
  --base develop \
  --title "feat(exporter): add JSON export with inter-rater scores" \
  --body "$(cat .github/PULL_REQUEST_TEMPLATE/feature.md)"
```

### Via the GitHub web UI

1. Push your branch
2. GitHub shows a **"Compare & pull request"** banner — click it
3. Set the base branch to `develop`
4. Fill in the template

---

## What makes a good PR?

### Size

- **Small PRs get reviewed faster and more carefully.** Aim for < 400 lines changed.
- If your feature is large, break it into a stack of smaller PRs.

### Description

- **What** changed (a one-liner)
- **Why** it was needed
- **How** to test it locally
- Screenshots for UI changes
- Link to the issue

### Checklist

Our PR template (`.github/PULL_REQUEST_TEMPLATE/feature.md`) includes:

- [ ] Tests added / updated
- [ ] Docstrings updated
- [ ] CHANGELOG entry added
- [ ] No patient data committed
- [ ] CI passes

---

## Reviewing a PR

```bash
# Check out the PR branch locally to test it
gh pr checkout 42

# Leave comments on specific lines in the GitHub UI, or via CLI
gh pr review 42 --comment -b "This looks good but line 78 could raise on empty input"

# Approve
gh pr review 42 --approve

# Request changes
gh pr review 42 --request-changes -b "Please add a test for the empty segment case"
```

### Review comment etiquette

| Prefix | Meaning |
|---|---|
| `[blocker]` | Must be fixed before merge |
| `[nit]` | Minor style preference, author can decide |
| `[question]` | Asking for clarification, not necessarily a change |
| `[suggestion]` | Optional improvement |

Example:
```
[blocker] `export_json()` doesn't handle the case where `segments` is empty.
This will raise `IndexError` on line 78. Please add a guard + test.

[nit] Variable name `d` on line 92 could be more descriptive (`review_data`?).
```

---

## Merging strategies

| Strategy | When to use | Effect on history |
|---|---|---|
| **Merge commit** | Long-lived branches, preserving full history | Creates a merge commit |
| **Squash and merge** | Feature branches — collapse all commits into one | Clean main/develop history |
| **Rebase and merge** | When commits are already clean and atomic | Linear history, no merge commit |

We use:
- **Squash and merge** for `feature/*` → `develop`
- **Rebase and merge** for `develop` → `main`

---

## Using LLMs to write PR descriptions

```
Write a GitHub Pull Request description for the diff below.

Structure:
## Summary
One paragraph: what changed and why.

## How to test
Step-by-step instructions to verify the change.

## Checklist
- [ ] Tests added
- [ ] Docs updated
- [ ] No patient data committed

Keep it concise. Reference issue #XX if visible in the diff.

<paste diff or summary>
```

---

## Draft PRs

Open a **Draft PR** early to share progress and get early feedback without implying it's ready to merge.

```bash
gh pr create --draft --title "WIP: feat(exporter): JSON export"
```

Mark ready when done:
```bash
gh pr ready 42
```

---

## Exercise

See [08_exercises.md — Exercise 5](08_exercises.md#exercise-5-open-and-review-a-pr).

---

Next → [06_rebase.md](06_rebase.md)
