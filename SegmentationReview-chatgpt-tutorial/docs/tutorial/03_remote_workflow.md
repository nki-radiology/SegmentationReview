# Module 3 — Remote Workflow

---

## Remotes

A **remote** is a named URL pointing to another copy of the repository (typically on GitHub).

```bash
# List remotes
git remote -v

# Add a remote
git remote add upstream https://github.com/your-org/SegmentationReview.git

# Remove a remote
git remote remove upstream
```

Convention:
- `origin` — your personal fork or the team's main repo
- `upstream` — the original repo (when you work from a fork)

---

## Clone, Fetch, Pull, Push

### `git clone`

Downloads a full copy of a remote repo and sets `origin` automatically.

```bash
git clone https://github.com/your-org/SegmentationReview.git
```

### `git fetch`

Downloads new commits / branches from the remote **without changing your working directory**.  
Safe to run at any time.

```bash
git fetch origin
git fetch --all          # fetch all remotes
```

### `git pull`

Fetch + merge (or fetch + rebase) in one step.

```bash
# Default: fetch + merge
git pull origin develop

# Preferred: fetch + rebase (keeps history linear)
git pull --rebase origin develop
```

> Configure rebase as the default to avoid noisy merge commits:
> ```bash
> git config --global pull.rebase true
> ```

### `git push`

Upload your local commits to the remote.

```bash
# First push of a new branch
git push -u origin feature/export-json-summary

# Subsequent pushes on the same branch
git push

# Force-push after a rebase (only on your own feature branch, never on main/develop)
git push --force-with-lease
```

> `--force-with-lease` is safer than `--force`: it refuses to overwrite if someone else has pushed.

---

## Keeping your branch up to date

```bash
# Fetch the latest from origin
git fetch origin

# Rebase your feature branch on top of updated develop
git switch feature/export-json-summary
git rebase origin/develop
```

This avoids "I need to merge develop into my feature branch" noise.

---

## Typical daily workflow

```bash
# Morning: sync with the team
git fetch origin
git switch develop
git pull --rebase origin develop

# Start a new task
git switch -c feature/add-hotkey-shortcuts

# ... work, work, work ...
git add -p
git commit -m "feat(ui): add A/R keyboard shortcuts for accept/reject"

# Push and open a PR
git push -u origin feature/add-hotkey-shortcuts
gh pr create --base develop --title "feat(ui): keyboard shortcuts" --body "Closes #12"
```

---

## Exercise

See [08_exercises.md — Exercise 3](08_exercises.md#exercise-3-remote-workflow).

---

Next → [04_commit_conventions.md](04_commit_conventions.md)
