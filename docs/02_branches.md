# Module 2 — Branches

---

## What is a branch?

A branch is a **lightweight movable pointer** to a commit. Creating a branch costs almost nothing — Git just writes a new pointer.

```
main:    A ── B ── C
                    \
feature:             D ── E   ← HEAD
```

When you commit on `feature`, the pointer moves forward. `main` stays where it was.

---

## Creating and switching branches

```bash
# Create a new branch and switch to it (preferred modern syntax)
git switch -c feature/add-docstring-joinpath

# List all local branches
git branch

# List all branches including remote-tracking ones
git branch -a

# Switch to an existing branch
git switch develop

# Switch back to where you were
git switch -
```

---

## Branch naming convention

We use lowercase kebab-case with a type prefix:

| Prefix | When to use |
|---|---|
| `feature/` | New functionality or improvement |
| `fix/` | Bug fixes |
| `refactor/` | Restructuring without behaviour change |
| `docs/` | Documentation-only changes |
| `chore/` | CI, tooling, dependency updates |

Examples:
- `feature/add-docstring-joinpath`
- `fix/handle-missing-nrrd-extension`
- `docs/improve-module-helptext`

---

## Merging

```bash
# Merge a feature branch into develop
git switch develop
git merge feature/add-docstring-joinpath

# Delete the branch after merge
git branch -d feature/add-docstring-joinpath
```

### Merge strategies

| Strategy | What it does |
|---|---|
| **Fast-forward** | No new commits on target — just moves the pointer forward |
| **Merge commit** | Creates a new commit joining both histories |
| **Squash merge** | Collapses all branch commits into one on target |

We use **squash merge** via GitHub PRs for feature branches.  
See [05_pull_requests.md](05_pull_requests.md) for the full PR workflow.

---

## Viewing differences between branches

```bash
# What commits are on feature but not on develop?
git log develop..feature/add-docstring-joinpath --oneline

# Full diff between branches
git diff develop...feature/add-docstring-joinpath
```

---

## Stashing work in progress

If you need to switch branches but aren't ready to commit:

```bash
# Save your uncommitted changes temporarily
git stash

# Switch branches, do your thing, come back
git switch develop
git switch feature/add-docstring-joinpath

# Restore your stashed changes
git stash pop
```

---

## Exercise

See [08_exercises.md — Exercise A](08_exercises.md#exercise-a-first-feature-branch).

---

Next → [03_remote_workflow.md](03_remote_workflow.md)
