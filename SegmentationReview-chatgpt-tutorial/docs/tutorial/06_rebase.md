# Module 6 — Rebase

Rebase is one of Git's most powerful (and misunderstood) tools. This module explains what it does, when to use it, and when to avoid it.

---

## What is rebase?

`git merge` creates a new merge commit that joins two branch histories.  
`git rebase` **replays** your commits on top of another branch, producing a linear history.

```
Before rebase:

main:    A ── B ── C
                    \
feature:             D ── E

After: git rebase main (on feature branch)

main:    A ── B ── C
                    \
feature:             D' ── E'   (new commits, same changes, new SHAs)
```

---

## Basic rebase

```bash
git switch feature/export-json-summary

# Replay your commits on top of the latest develop
git rebase origin/develop
```

If there are conflicts:

```bash
# Git pauses at the conflicting commit. Fix the file, then:
git add src/segmentation_review/exporter.py
git rebase --continue

# To abort and return to the original state:
git rebase --abort
```

---

## Interactive rebase — `git rebase -i`

Interactive rebase lets you **rewrite history** before sharing it.  
Use it to clean up your local commits before opening a PR.

```bash
# Rewrite the last 4 commits
git rebase -i HEAD~4
```

This opens an editor:

```
pick a3f8c1d feat(exporter): stub JSON writer
pick b2d9f0a wip: add field loop
pick 9c44d81 fix typo
pick e7a1c3f add tests

# Commands:
# p, pick   = use commit as-is
# r, reword = use commit, but edit the message
# e, edit   = use commit, but stop to amend files
# s, squash = meld into previous commit, keep both messages
# f, fixup  = like squash, but discard this commit's message
# d, drop   = remove the commit entirely
```

### Common operations

#### Squash WIP commits into one clean commit

```
pick a3f8c1d feat(exporter): stub JSON writer
f    b2d9f0a wip: add field loop
f    9c44d81 fix typo
f    e7a1c3f add tests
```
Result: one commit `a3f8c1d` with a clean message.

#### Reorder commits

Change the order of lines in the editor.

#### Edit a commit message

Change `pick` to `reword` (or `r`). Git will open your editor for that commit's message.

#### Split a commit

Change `pick` to `edit`. Git pauses at that commit:

```bash
# Undo the commit but keep the changes staged
git reset HEAD^

# Stage and commit in separate atomic pieces
git add src/segmentation_review/exporter.py
git commit -m "feat(exporter): add JSON serialisation"
git add tests/test_exporter.py
git commit -m "test(exporter): add JSON export tests"

# Continue rebase
git rebase --continue
```

---

## `git commit --fixup` workflow

This is great for addressing review feedback without polluting history.

```bash
# You already have commit a3f8c1d "feat(exporter): add JSON writer"
# Reviewer asks you to fix a bug in the same file

# Make the fix, then:
git add src/segmentation_review/exporter.py
git commit --fixup a3f8c1d
# Creates: "fixup! feat(exporter): add JSON writer"

# Clean it all up before merging:
git rebase -i --autosquash origin/develop
# Git automatically moves and applies the fixup commit
```

---

## The golden rule of rebase

> **Never rebase commits that have already been pushed to a shared branch.**

Rebase creates new commits (new SHAs). If someone else based work on your old commits, rewriting them causes serious confusion.

Safe to rebase:
- Your local commits not yet pushed
- Your feature branch (only you are working on it)
- After `git pull --rebase` on your own branch

Never rebase:
- `main`, `develop`, or any branch others work on

---

## Rebase vs Merge — when to use what

| Situation | Use |
|---|---|
| Update feature branch with latest develop | `git rebase origin/develop` |
| Clean up WIP commits before PR | `git rebase -i HEAD~N` |
| Merge a PR on GitHub | Squash or rebase merge (not merge commit) |
| Undo a pushed merge | `git revert` — never rebase |

---

## Exercise

See [08_exercises.md — Exercise 6](08_exercises.md#exercise-6-interactive-rebase).

---

Next → [07_ci_github_actions.md](07_ci_github_actions.md)
