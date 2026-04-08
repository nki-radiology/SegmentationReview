# Module 3 — Remote Workflow

---

## Remotes

A **remote** is a named reference to a repository hosted elsewhere (usually GitHub).

```bash
# See all configured remotes
git remote -v

# Typical setup for this workshop
origin    https://github.com/<your-username>/SegmentationReview.git (fetch)
origin    https://github.com/<your-username>/SegmentationReview.git (push)
upstream  https://github.com/NKIRadiology/SegmentationReview.git (fetch)
upstream  https://github.com/NKIRadiology/SegmentationReview.git (push)
```

- `origin` = your fork (you control it — push freely)
- `upstream` = the shared team repo (you pull from it, never push directly)

---

## Clone

```bash
# Clone your fork
git clone https://github.com/<your-username>/SegmentationReview.git
cd SegmentationReview

# Add the team repo as upstream
git remote add upstream https://github.com/NKIRadiology/SegmentationReview.git
```

---

## Fetch, Pull, Push

| Command | What it does |
|---|---|
| `git fetch` | Downloads changes from remote, does NOT update your working directory |
| `git pull` | `fetch` + `merge` (or `rebase` if configured) |
| `git push` | Upload local commits to the remote |

```bash
# Get latest from upstream without changing anything locally
git fetch upstream

# Update your local develop to match upstream
git switch develop
git rebase upstream/develop

# Push your feature branch to your fork
git push -u origin feature/add-docstring-joinpath

# After a rebase, force-push safely
git push --force-with-lease origin feature/add-docstring-joinpath
```

---

## `pull --rebase` vs `pull` (merge)

```bash
# Preferred: rebase keeps history linear
git pull --rebase origin develop

# Default: creates merge commits
git pull origin develop
```

Set rebase as default:
```bash
git config --global pull.rebase true
```

---

## Keeping your fork up to date

```bash
# Get latest from the team repo
git fetch upstream

# Update develop
git switch develop
git rebase upstream/develop

# Push the updated develop to your fork
git push origin develop
```

---

## Typical day-to-day flow

```bash
# 1. Start from an up-to-date develop
git switch develop
git pull --rebase upstream develop

# 2. Create a feature branch
git switch -c feature/fix-bare-except

# 3. Make changes, commit
git add SegmentationReview/SegmentationReview.py
git commit -m "fix(review): replace bare except with specific exception type"

# 4. Push to your fork
git push -u origin feature/fix-bare-except

# 5. Open a PR on GitHub (or via gh CLI)
gh pr create --base develop
```

---

## Exercise

See [08_exercises.md — Exercise A](08_exercises.md#exercise-a-first-feature-branch) (step 4: push your branch).

---

Next → [04_commit_conventions.md](04_commit_conventions.md)
