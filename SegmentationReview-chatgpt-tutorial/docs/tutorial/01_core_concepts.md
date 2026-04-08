# Module 1 — Core Concepts

---

## The three areas of Git

```
┌─────────────────────┐    git add     ┌──────────────┐    git commit    ┌───────────────┐
│   Working directory │ ─────────────► │ Staging area │ ───────────────► │  Local repo   │
│  (your file system) │                │  (the index) │                  │  (.git folder)│
└─────────────────────┘                └──────────────┘                  └───────────────┘
```

- **Working directory** — your actual files on disk
- **Staging area** (index) — a draft of your next commit; lets you craft precise commits even if you changed many files
- **Local repo** — the permanent history stored in `.git/`

---

## Initialising and basic commands

```bash
# Start a new repo
git init

# Check what's staged / unstaged
git status

# Stage specific files
git add src/segmentation_review/loader.py

# Stage only part of a file (interactive hunk selection)
git add -p src/segmentation_review/loader.py

# Commit with a message
git commit -m "feat(loader): add NIfTI support"

# See the commit log
git log --oneline --graph --all
```

---

## Anatomy of a commit

Every commit stores:

| Field | Content |
|---|---|
| **SHA** | Unique 40-char hash (e.g. `a3f8c1d`) |
| **Author + timestamp** | Who and when |
| **Parent SHA(s)** | What came before (merge commits have 2) |
| **Tree** | Snapshot of the entire repo at that point |
| **Message** | Your explanation |

```bash
# Inspect a commit in full
git show a3f8c1d

# Show what changed in the last commit
git show HEAD
```

---

## The `.gitignore`

Files listed here are never tracked. For a Python/Slicer project:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.venv/
*.egg-info/

# Editor
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Data — never commit patient data
data/
*.nrrd
*.nii
*.nii.gz
```

> **Rule of thumb:** If it's generated, large, secret, or patient data — add it to `.gitignore`.

---

## Undoing things

```bash
# Unstage a file (keep changes in working dir)
git restore --staged src/segmentation_review/loader.py

# Discard working-dir changes (destructive!)
git restore src/segmentation_review/loader.py

# Amend the last commit message (before pushing)
git commit --amend -m "fix(loader): correct NIfTI axis orientation"

# Create a new commit that reverses a previous one (safe for shared branches)
git revert a3f8c1d
```

> Never use `git reset --hard` on commits that have already been pushed to a shared branch.

---

## Exercise

See [08_exercises.md — Exercise 1](08_exercises.md#exercise-1-your-first-structured-commit).

---

Next → [02_branches.md](02_branches.md)
