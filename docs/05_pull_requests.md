# Module 5 — Pull Requests

A **Pull Request (PR)** is a proposal to merge one branch into another.
On GitHub it is also the home of code review — the conversation between author and reviewer.

---

## Opening a PR

### Via GitHub CLI (recommended)

```bash
# Push your branch first
git push -u origin feature/add-docstring-joinpath

# Open a PR interactively
gh pr create

# Or in one line, targeting develop
gh pr create \
  --base develop \
  --title "docs(review): add docstrings to helper methods" \
  --body "$(cat .github/PULL_REQUEST_TEMPLATE.md)"
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
- One PR per logical change. Don't bundle a docstring fix with a refactor.

### Description

- **What** changed (a one-liner)
- **Why** it was needed
- **How** to verify it (for code changes: steps to reproduce the old behaviour and confirm the fix)
- Link to the issue

### Checklist (from our PR template)

- [ ] Commits follow [Conventional Commits](04_commit_conventions.md)
- [ ] No patient data or large binaries committed
- [ ] PR is targeted at `develop`, not `main`

---

## Reviewing a PR

```bash
# Check out the PR branch locally to read or test it
gh pr checkout 42

# Leave a comment via CLI
gh pr review 42 --comment -b "Line 252: the method also accepts .nrrd — mention it in the docstring"

# Approve
gh pr review 42 --approve

# Request changes
gh pr review 42 --request-changes -b "Please update the docstring to list all accepted extensions"
```

### Review comment etiquette

| Prefix | Meaning |
|---|---|
| `[blocker]` | Must be fixed before merge |
| `[nit]` | Minor style preference, author can decide |
| `[question]` | Asking for clarification, not necessarily a change |
| `[suggestion]` | Optional improvement |

Example comment on `SegmentationReview.py`:
```
[blocker] `_is_valid_extension` (line 252) checks `.nii.gz` with `".nii.gz" in file`,
but `".nii" in file` would also match `.nii.gz`. The current order in the list
means `.nii.gz` files get matched by the `.nii` check first. Please add a test
or document the intended behaviour.

[nit] The method name `joinpath` shadows `pathlib.Path.joinpath`. Consider
renaming to `_join_path` to make the private convention explicit.
```

---

## Merging strategies

| Strategy | When to use | Effect on history |
|---|---|---|
| **Merge commit** | Long-lived branches, preserving full history | Creates a merge commit |
| **Squash and merge** | Feature branches — collapse all commits into one | Clean develop/main history |
| **Rebase and merge** | Commits are already clean and atomic | Linear history, no merge commit |

We use:
- **Squash and merge** for `feature/*` → `develop`
- **Rebase and merge** for `develop` → `main`

---

## Draft PRs

Open a **Draft PR** early to share progress and get early feedback without implying it's ready to merge.

```bash
gh pr create --draft --title "WIP: docs(review): improve helper method docstrings"
```

Mark ready when done:
```bash
gh pr ready 42
```

---

## Using LLMs to write PR descriptions

```
Write a GitHub Pull Request description for changes to the
SegmentationReview 3D Slicer extension.

Structure:
## Summary
1–2 sentences: what changed and why.

## How to verify
Numbered steps a reviewer can follow (e.g. "open the file, confirm
_is_valid_extension has a docstring listing .nii, .nii.gz, .nrrd").

## Checklist
- [ ] Commits follow Conventional Commits
- [ ] No patient data committed

--- COMMITS ---
<paste git log --oneline output>

--- DIFF SUMMARY ---
<paste diff or summary>
```

See [`AGENT_GUIDE.md`](../AGENT_GUIDE.md) for a worked example.

---

## Exercise

See [08_exercises.md — Exercise C](08_exercises.md#exercise-c-code-review).

---

Next → [06_rebase.md](06_rebase.md)
