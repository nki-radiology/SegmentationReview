# Module 1 — Core Concepts

---

## The three areas of Git

```
Working directory  ──git add──►  Staging area  ──git commit──►  Local repository
```

| Area | What it is |
|---|---|
| **Working directory** | Your files as you see them on disk |
| **Staging area** (index) | A snapshot of what will go into the next commit |
| **Local repository** | The full history of all commits, stored in `.git/` |

---

## What is a commit?

A commit is a **snapshot**, not a diff. Git stores the full state of all tracked files at the moment you commit. The "diff" view you see in GitHub is computed on the fly by comparing two snapshots.

Each commit has:
- A unique SHA (e.g. `d6b9026`)
- A pointer to its parent commit(s)
- A tree of file snapshots
- Author, timestamp, and message

---

## Your first commands

```bash
# See what Git knows about your working directory
git status

# See what changed since the last commit
git diff

# Stage a specific file
git add SegmentationReview/SegmentationReview.py

# Stage only selected hunks within a file (very useful)
git add -p SegmentationReview/SegmentationReview.py

# Commit with a message
git commit -m "docs(review): add docstring to _is_valid_extension"

# See recent history
git log --oneline
```

---

## Reading `git log`

```bash
git log --oneline --graph --all
```

Example output:
```
* d6b9026 (HEAD -> feature/add-docstrings) docs(review): add docstring to joinpath
* 3a71bce docs(review): add docstring to _is_valid_extension
* b938cc8 (origin/develop, develop) Merge pull request #23 from zapaishchykova/revert
```

- `HEAD` points to the commit you currently have checked out
- `origin/develop` is what GitHub last saw on the `develop` branch
- `*` is a commit, lines show branching and merging

---

## What is tracked?

Git only tracks files you have explicitly added. New files are **untracked** until you `git add` them.

```bash
# See untracked files
git status

# See which files are tracked
git ls-files
```

`.gitignore` lists patterns Git should never track (temp files, credentials, large data).

---

## Undoing things safely

```bash
# Unstage a file (keeps your edits)
git restore --staged SegmentationReview/SegmentationReview.py

# Discard working-directory changes to a file (DESTRUCTIVE — edits are lost)
git restore SegmentationReview/SegmentationReview.py

# Undo the last commit but keep the changes staged
git reset --soft HEAD^

# See what your repo looked like 3 commits ago (read-only)
git checkout HEAD~3
git switch -  # go back to where you were
```

---

## Exercise

See [08_exercises.md — Exercise A](08_exercises.md#exercise-a-first-feature-branch).

---

Next → [02_branches.md](02_branches.md)
