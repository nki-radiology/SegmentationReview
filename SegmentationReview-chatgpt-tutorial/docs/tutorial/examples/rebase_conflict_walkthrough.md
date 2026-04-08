# Worked Example: Resolving a Rebase Conflict

This example walks through a real merge conflict scenario in the SegmentationReview codebase — exactly what you'd see when two people edit the same function.

---

## Setup

Two colleagues are working in parallel:

- **Fatima** is on `feature/loader-orientation-fix` — she changed the signature of `load_segmentation()` to accept an optional `orientation` parameter.
- **Joren** is on `feature/loader-logging` — he added structured logging to `load_segmentation()`.

Both branched off the same commit on `develop`. Their changes touch the same lines of `loader.py`.

Fatima's PR merges first. Now Joren needs to rebase.

---

## What Joren runs

```bash
git fetch origin
git rebase origin/develop
```

Git pauses:

```
Auto-merging src/segmentation_review/loader.py
CONFLICT (content): Merge conflict in src/segmentation_review/loader.py
error: could not apply b2d9f0a... feat(loader): add structured logging
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and return to the original state: run "git rebase --abort".
```

---

## What the conflict looks like

```python
def load_segmentation(path: str | Path) -> dict:
<<<<<<< HEAD
def load_segmentation(path: str | Path, orientation: str = "RAS") -> dict:
    """Load a segmentation file. Orientation defaults to RAS."""
=======
def load_segmentation(path: str | Path) -> dict:
    """Load a segmentation file and return a review-ready structure."""
    logger.info("Starting load for %s", path)
>>>>>>> b2d9f0a (feat(loader): add structured logging)
```

- `HEAD` = the current state of `develop` (Fatima's change — new `orientation` parameter)
- Below `=======` = Joren's commit being replayed (his logging addition)

---

## How to resolve it

The correct result should **include both changes**: the new parameter AND the logging. Joren edits the file:

```python
def load_segmentation(path: str | Path, orientation: str = "RAS") -> dict:
    """Load a segmentation file and return a review-ready structure.

    Args:
        path: Path to the segmentation file.
        orientation: Coordinate system to use. Defaults to ``RAS``.
    """
    logger.info("Starting load for %s (orientation=%s)", path, orientation)
```

Then:

```bash
# Mark as resolved
git add src/segmentation_review/loader.py

# Continue the rebase
git rebase --continue
```

Git will open the editor to confirm the commit message — Joren keeps it as-is and saves.

---

## After the rebase

```bash
git log --oneline
# b3e9f1c feat(loader): add structured logging     ← replayed on top of Fatima's commit
# 7a2d8e1 feat(loader): add orientation parameter  ← Fatima's commit (now in develop)
# 3a71bce feat(loader): initial NIfTI support
```

Push the updated branch:

```bash
git push --force-with-lease origin feature/loader-logging
```

---

## Key lessons

| Situation | Action |
|---|---|
| Conflict during rebase | Fix the file, `git add`, `git rebase --continue` |
| Want to bail out entirely | `git rebase --abort` — returns to state before rebase |
| Accidentally in a bad state | `git rebase --abort` is always safe to use |
| After resolving — CI fails | Your resolved code may have a bug; fix it, `git commit --fixup HEAD`, re-push |

---

## Tools that help

```bash
# See what the conflict looks like with more context
git diff

# Use VS Code's built-in conflict resolver
code src/segmentation_review/loader.py
# Look for the "Accept Current Change / Accept Incoming Change / Accept Both" inline buttons

# Use a proper merge tool
git mergetool
```
