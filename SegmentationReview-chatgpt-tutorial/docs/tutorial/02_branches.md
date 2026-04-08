# Module 2 — Branches

Branches are lightweight pointers to commits. Creating one is instant and costs almost nothing.

---

## Creating and switching branches

```bash
# List all branches (* = current)
git branch

# Create a new branch and switch to it (modern syntax)
git switch -c feature/export-json-summary

# Older equivalent (still works)
git checkout -b feature/export-json-summary

# Switch to an existing branch
git switch develop

# Delete a branch (after merging)
git branch -d feature/export-json-summary
```

---

## Visualising the branch graph

```bash
git log --oneline --graph --all --decorate
```

Example output for this repo:

```
* e7a1c3f (HEAD -> feature/export-json-summary) feat(exporter): add JSON writer
* b2d9f0a feat(exporter): define ReviewSummary dataclass
| * 9c44d81 (develop) fix(loader): handle missing orientation matrix
|/
* 3a71bce feat(loader): initial NIfTI support
* 1e9f002 (main) chore: initial project scaffold
```

---

## Merging strategies

### Fast-forward merge (no divergence)

```bash
git switch develop
git merge feature/add-keyboard-shortcuts
# Result: develop pointer simply moves forward — no merge commit
```

### Three-way merge (branches diverged)

```bash
git switch develop
git merge feature/export-json-summary
# Git creates a merge commit with two parents
```

### Merge conflicts

When the same lines are changed on both branches:

```bash
# Git pauses and marks conflicts in the file:
<<<<<<< HEAD
    def export(self, path: str) -> None:
=======
    def export(self, path: str, format: str = "csv") -> None:
>>>>>>> feature/export-json-summary

# 1. Edit the file to the desired result
# 2. Stage it
git add src/segmentation_review/exporter.py
# 3. Finish the merge
git commit
```

---

## Branch workflow for this repo

```
main ──────────────────────────────────────────────────────►
        │                                          ▲
        ▼                                          │ (release PR)
      develop ──────────────────────────────────►  │
          │                          ▲             │
          ▼                          │ (feature PR) │
        feature/export-json-summary ─┘
```

1. Branch off `develop`
2. Work in small commits
3. Open a PR back into `develop`
4. Periodically `develop` is merged into `main` as a release

---

## Stashing — save work without committing

```bash
# Stash your current dirty state
git stash push -m "WIP: halfway through CSV refactor"

# List stashes
git stash list

# Apply the most recent stash (keeps it in list)
git stash apply

# Apply and remove from list
git stash pop

# Apply a specific stash
git stash apply stash@{2}
```

---

## Exercise

See [08_exercises.md — Exercise 2](08_exercises.md#exercise-2-branching-and-merging).

---

Next → [03_remote_workflow.md](03_remote_workflow.md)
