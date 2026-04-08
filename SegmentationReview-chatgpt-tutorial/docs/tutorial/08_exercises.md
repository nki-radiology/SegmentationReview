# Module 8 — Practical Exercises

Work through these in order. Each builds on the previous.  
Use your fork of this repo as the sandbox.

---

## Exercise 1: Your first structured commit

**Goal:** Practice staging and writing a good commit message.

1. In your fork, open `src/segmentation_review/loader.py`
2. Add a docstring to the `load_nifti()` function explaining what it does and what it returns
3. Stage only that file:
   ```bash
   git add src/segmentation_review/loader.py
   ```
4. Write a commit message following Conventional Commits:
   ```bash
   git commit
   ```
   Use your editor to write a multi-line message. Subject line + blank line + body.
5. Inspect your commit:
   ```bash
   git show HEAD
   ```

**Checklist:** Does `git log --oneline` show a clean, conventional subject line?

---

## Exercise 2: Branching and merging

**Goal:** Create a feature branch, make changes, and merge it back.

1. Create a branch `feature/add-segment-count`:
   ```bash
   git switch -c feature/add-segment-count
   ```
2. In `src/segmentation_review/loader.py`, add a function:
   ```python
   def count_segments(segmentation_node) -> int:
       """Return the number of segments in a segmentation node."""
       return segmentation_node.GetSegmentation().GetNumberOfSegments()
   ```
3. Commit it with a conventional message
4. Switch back to `develop` and merge:
   ```bash
   git switch develop
   git merge feature/add-segment-count
   ```
5. Delete the feature branch:
   ```bash
   git branch -d feature/add-segment-count
   ```

---

## Exercise 3: Remote workflow

**Goal:** Push a branch and sync with upstream.

1. Push your current `develop` to your fork:
   ```bash
   git push -u origin develop
   ```
2. Add the team repo as `upstream`:
   ```bash
   git remote add upstream https://github.com/your-org/SegmentationReview.git
   ```
3. Fetch changes from upstream and rebase:
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```
4. Push the updated branch:
   ```bash
   git push --force-with-lease origin develop
   ```

---

## Exercise 4: Writing good commits

**Goal:** Use an LLM to draft a commit message, then improve it.

1. Make a small code change (add a type hint, fix a comment, add a log line)
2. Stage it: `git add -p`
3. Get the diff: `git diff --staged`
4. Paste the diff into your LLM with the prompt from [Module 4](04_commit_conventions.md#using-llms-to-write-commit-messages)
5. Review the LLM's output — does it follow all conventions?
6. Edit and commit

**Reflection:** What did the LLM get right? What did you have to change?

---

## Exercise 5: Open and review a PR

**Goal:** Experience the full PR lifecycle.

1. Create a branch `feature/your-name-test-pr`
2. Add a docstring to any undocumented function in `src/`
3. Push and open a PR against `develop`:
   ```bash
   gh pr create --base develop
   ```
4. Ask a colleague to review it and leave at least one comment
5. Address their comment, push the fix, re-request review
6. Once approved, merge using **Squash and merge**

---

## Exercise 6: Interactive rebase

**Goal:** Clean up messy commits before a PR.

1. Create a branch `feature/messy-commits`
2. Make 4 commits in sequence:
   - First commit: add a function stub
   - Second commit: "wip"
   - Third commit: "fix typo"
   - Fourth commit: complete the function + tests
3. Use interactive rebase to turn these 4 commits into 2 clean ones:
   ```bash
   git rebase -i HEAD~4
   ```
   - Squash "wip" and "fix typo" into the first commit
   - Keep the tests as a separate commit
4. Inspect the result: `git log --oneline`

**Bonus:** Use `git commit --fixup` + `--autosquash` instead.

---

## Exercise 7: Fix a CI failure

**Goal:** Understand the CI workflow and fix a failing check.

1. Intentionally introduce a linting error:
   ```python
   import os  # add this unused import somewhere
   ```
2. Commit and push to your branch
3. Open a PR — watch CI fail
4. Click **Details** on the failing check, find the error
5. Fix it locally:
   ```bash
   ruff check --fix src/
   git add .
   git commit --fixup HEAD
   git rebase -i --autosquash HEAD~2
   git push --force-with-lease
   ```
6. Watch CI go green ✅

---

## Exercise 8: Resolve a merge conflict

**Goal:** Handle a conflict confidently.

1. On `develop`, change line 1 of `src/segmentation_review/loader.py` (add a comment)
2. Commit to `develop`
3. Create a branch `feature/conflict-demo`, switch to it
4. Change the **same line** differently
5. Commit on the feature branch
6. Try to merge:
   ```bash
   git switch develop
   git merge feature/conflict-demo
   ```
7. Open the conflicted file, resolve it, stage, commit

---

## Cheat sheet

```bash
# Branches
git switch -c feature/name     # create + switch
git switch develop             # switch
git branch -d feature/name     # delete

# Commits
git add -p                     # stage interactively
git commit -m "type(scope): msg"
git commit --fixup <sha>       # mark as fixup

# Remote
git fetch origin
git pull --rebase origin develop
git push -u origin feature/name
git push --force-with-lease    # after rebase

# Rebase
git rebase origin/develop          # update branch
git rebase -i HEAD~N               # interactive
git rebase -i --autosquash HEAD~N  # with fixups

# Inspection
git log --oneline --graph --all
git show HEAD
git diff --staged
git status
```
