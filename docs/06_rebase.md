# Module 6 — Rebase

Rebase is one of Git's most powerful (and most misunderstood) tools. This module explains what it does, when to use it, and when to avoid it.

---

## What is rebase?

`git merge` creates a new merge commit that joins two branch histories.
`git rebase` **replays** your commits on top of another branch, producing a linear history.

```
Before rebase:

develop: A ── B ── C
                    \
feature:             D ── E

After: git rebase develop (from feature branch)

develop: A ── B ── C
                    \
feature:             D' ── E'   (new commits, same changes, new SHAs)
```

---

## Basic rebase

```bash
git switch feature/add-docstring-joinpath

# Replay your commits on top of the latest develop
git rebase origin/develop
```

If there are conflicts:

```bash
# Git pauses at the conflicting commit. Fix the file, then:
git add SegmentationReview/SegmentationReview.py
git rebase --continue

# To abort and return to the original state:
git rebase --abort
```

After rebasing a pushed branch:
```bash
# --force-with-lease is safer than --force: it fails if someone else pushed
git push --force-with-lease origin feature/add-docstring-joinpath
```

---

## Interactive rebase — `git rebase -i`

Interactive rebase lets you **rewrite history** before sharing it.
Use it to clean up messy local commits before opening a PR.

```bash
# Rewrite the last 4 commits
git rebase -i HEAD~4
```

This opens an editor:

```
pick a3f8c1d docs(review): add docstring to joinpath
pick b2d9f0a wip
pick 9c44d81 fix typo in docstring
pick e7a1c3f docs(review): add docstring to _is_valid_extension

# Commands:
# p, pick   = use commit as-is
# r, reword = use commit, but edit the message
# s, squash = meld into previous commit, keep both messages
# f, fixup  = like squash, but discard this commit's message
# d, drop   = remove the commit entirely
```

### Squash WIP commits into one clean commit

```
pick a3f8c1d docs(review): add docstring to joinpath
f    b2d9f0a wip
f    9c44d81 fix typo in docstring
pick e7a1c3f docs(review): add docstring to _is_valid_extension
```

Result: two clean commits, no WIP traces.

---

## `git commit --fixup` workflow

Great for addressing review feedback without polluting history:

```bash
# You have commit a3f8c1d "docs(review): add docstring to joinpath"
# Reviewer asks you to improve the wording

# Make the change, then:
git add SegmentationReview/SegmentationReview.py
git commit --fixup a3f8c1d
# Creates: "fixup! docs(review): add docstring to joinpath"

# Clean it all up before merging:
git rebase -i --autosquash origin/develop
# Git automatically moves and applies the fixup
```

---

## The golden rule of rebase

> **Never rebase commits that have already been pushed to a shared branch.**

Rebase creates new commits (new SHAs). If someone else based work on your old commits, rewriting them causes serious confusion.

**Safe to rebase:**
- Local commits not yet pushed
- Your own feature branch (only you are working on it)
- After pulling with `--rebase` on your own branch

**Never rebase:**
- `main`, `develop`, or any branch others actively work on

---

## Rebase vs Merge — when to use what

| Situation | Use |
|---|---|
| Update feature branch with latest develop | `git rebase origin/develop` |
| Clean up WIP commits before PR | `git rebase -i HEAD~N` |
| Merge a PR on GitHub | Squash merge (feature) or rebase merge (develop→main) |
| Undo a pushed merge | `git revert` — never rebase |

---

## Exercise

See [08_exercises.md — Exercise D](08_exercises.md#exercise-d-rebase-and-conflict-resolution).

---

Next → [07_ci_github_actions.md](07_ci_github_actions.md)
