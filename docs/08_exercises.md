# Module 8 — Exercises

Work through these in order. Each builds on the previous.
All changes are made to **`SegmentationReview/SegmentationReview.py`** in your fork.

---

## Exercise A — First feature branch

**Goal:** Practice branching, staging, and writing a good commit message.

### The change

`_is_valid_extension` (around line 251) has no docstring:

```python
def _is_valid_extension(self, path):
    return any(path.endswith(i) for i in [".nii", ".nii.gz", ".nrrd"])
```

Add a docstring that explains what it does, what argument it takes, and what it returns:

```python
def _is_valid_extension(self, path):
    """Return True if the file path ends with a supported segmentation format.

    Supported formats: .nii, .nii.gz, .nrrd

    Args:
        path: File path as a string.

    Returns:
        bool: True if the extension is supported, False otherwise.
    """
    return any(path.endswith(i) for i in [".nii", ".nii.gz", ".nrrd"])
```

### Steps

```bash
# 1. Start from an up-to-date develop
git switch develop
git pull --rebase upstream develop

# 2. Create your feature branch
git switch -c feature/add-docstring-is-valid-extension

# 3. Edit SegmentationReview/SegmentationReview.py — add the docstring above

# 4. Stage only the changed file
git add SegmentationReview/SegmentationReview.py

# 5. Write a commit message (try writing it yourself first, then use the LLM prompt)
git commit

# 6. Push to your fork
git push -u origin feature/add-docstring-is-valid-extension

# 7. Open a PR against develop
gh pr create --base develop
```

### LLM prompt for step 5

```
git diff --staged
```
Paste the output into your LLM with this prompt — see [04_commit_conventions.md](04_commit_conventions.md#using-llms-to-write-commit-messages).

**Checklist:** Does `git log --oneline` show a clean, conventional subject line?

---

## Exercise B — Second commit and CI

**Goal:** Add a second atomic commit; understand CI feedback.

### The change

`joinpath` (around line 248) also has no docstring and uses an unusual pattern:

```python
def joinpath(self, rootdir, targetdir):
    return os.path.join(os.sep, rootdir+os.sep, targetdir)
```

Add a docstring:

```python
def joinpath(self, rootdir, targetdir):
    """Join a root directory and a target path into an absolute path string.

    Args:
        rootdir: The base directory (absolute path string).
        targetdir: The relative path to append.

    Returns:
        str: The joined absolute path.
    """
    return os.path.join(os.sep, rootdir+os.sep, targetdir)
```

### Steps

```bash
# Stay on your existing feature branch
git switch feature/add-docstring-is-valid-extension

# Make the change, then commit it as a second commit
git add SegmentationReview/SegmentationReview.py
git commit -m "docs(review): add docstring to joinpath helper"

# Push the updated branch
git push origin feature/add-docstring-is-valid-extension
```

Watch the CI checks run on your open PR. If anything fails, click **Details** and fix it locally using `--fixup`.

**Reflection:** Should these two docstring changes be one commit or two? When would squashing make sense?

---

## Exercise C — Code review

**Goal:** Experience both sides of a code review.

### As a reviewer

Check out a colleague's PR:
```bash
gh pr checkout <pr-number>
```

Open `SegmentationReview/SegmentationReview.py` and look at their docstring changes. Leave at least one review comment using the format:

```
[nit] / [blocker] / [suggestion] <line reference>: <specific feedback>
```

Examples of things to look for:
- Is the type annotation (`path: str`) missing?
- Does the docstring mention all three supported formats?
- Is the return type documented?
- Does the wording match what the code actually does?

```bash
# Leave a comment via CLI
gh pr review <pr-number> --comment -b "[nit] The docstring doesn't mention that path must be a string, not a Path object. Consider adding a note or a type annotation."
```

### As the author

Respond to each comment:
- For valid points: push a fix commit (or `--fixup`) and resolve the thread
- For disagreements: reply with your reasoning before marking resolved

```bash
# Address feedback, stage, and create a fixup
git add SegmentationReview/SegmentationReview.py
git commit --fixup HEAD~1   # points to the commit being fixed

# Optionally squash before merge
git rebase -i --autosquash origin/develop
git push --force-with-lease origin feature/add-docstring-is-valid-extension
```

---

## Exercise D — Rebase and conflict resolution

**Goal:** Rebase your feature branch when `develop` has moved on.

### Setup

While your PR is open, the instructor (or a colleague) merges a change directly to `develop` that also touches `SegmentationReview.py`.

### Steps

```bash
# 1. Fetch the latest state of all remotes
git fetch upstream

# 2. Check what changed on develop
git log HEAD..upstream/develop --oneline

# 3. Rebase your branch onto the new develop
git switch feature/add-docstring-is-valid-extension
git rebase upstream/develop
```

If there is a conflict:

```bash
# Git pauses and shows the conflict markers in the file:
# <<<<<<< HEAD
# (your version)
# =======
# (their version)
# >>>>>>> upstream/develop

# Open the file, resolve the conflict by editing to the desired result.
# Remove the conflict markers.

git add SegmentationReview/SegmentationReview.py
git rebase --continue
```

```bash
# 4. Push the rebased branch (force-with-lease, NOT --force)
git push --force-with-lease origin feature/add-docstring-is-valid-extension
```

**Why `--force-with-lease`?** It checks that no one else pushed to your branch since you last fetched. If someone did, the push fails — protecting you from overwriting their work.

---

## Exercise E — Post-merge hygiene

**Goal:** Clean up after a merge and understand the history it leaves.

### After your PR is merged

```bash
# 1. Switch to develop and pull the merged result
git switch develop
git pull --rebase upstream develop

# 2. Delete your local feature branch
git branch -d feature/add-docstring-is-valid-extension

# 3. Delete the remote branch on your fork
git push origin --delete feature/add-docstring-is-valid-extension

# 4. Inspect the history
git log --oneline --graph develop
```

### Compare merge strategies

Look at the commit history of the merged PR:

| Strategy | What you see in `git log` |
|---|---|
| **Squash merge** | One clean commit per PR |
| **Rebase merge** | All individual commits, linear history |
| **Merge commit** | A merge commit joining the two branch tips |

We use **squash merge** for feature branches. Can you find the squashed commit in `git log`?

---

## Cheat sheet

```bash
# Branches
git switch -c feature/name     # create + switch
git switch develop             # switch
git branch -d feature/name     # delete local
git push origin --delete feature/name  # delete remote

# Commits
git add -p                          # stage interactively (hunk by hunk)
git commit -m "type(scope): msg"
git commit --fixup <sha>            # mark as fixup for a previous commit

# Remote
git fetch upstream
git pull --rebase upstream develop
git push -u origin feature/name
git push --force-with-lease         # after rebase

# Rebase
git rebase upstream/develop         # update branch
git rebase -i HEAD~N                # interactive (clean up N commits)
git rebase -i --autosquash HEAD~N   # auto-apply fixup commits

# Inspection
git log --oneline --graph --all
git show HEAD
git diff --staged
git status
```
