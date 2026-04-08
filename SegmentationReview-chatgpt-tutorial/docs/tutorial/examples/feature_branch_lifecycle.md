# Worked Example: `feature/export-json-summary`

This document shows what the full lifecycle of a feature branch looks like — from creation to merged PR. Use it as a reference when doing Exercise 5.

---

## The story

**Issue #34:** *"CSV export is insufficient for downstream ML pipelines — add JSON export with inter-rater scores."*

Assigned to: `j.devries`

---

## Step 1 — Branch off develop

```bash
git switch develop
git pull --rebase origin develop
git switch -c feature/export-json-summary
```

---

## Step 2 — Commits made on this branch

A realistic commit history (what `git log --oneline` would show):

```
e7a1c3f feat(exporter): add JSON export with inter-rater scores
9c44d81 test(exporter): add full test suite for JSON export
b2d9f0a feat(exporter): define ReviewSummary dataclass and stats
3a71bce refactor(exporter): extract SegmentVerdict into separate enum
```

Notice:
- Each commit is atomic — one logical change
- Commit messages follow Conventional Commits
- Tests are a separate commit, not mixed in with the feature code
- A refactor was identified mid-work and committed cleanly

---

## Step 3 — Keep branch up to date

While working, `develop` received a commit from a colleague:

```bash
git fetch origin
git rebase origin/develop
# No conflicts — continues cleanly
git push --force-with-lease origin feature/export-json-summary
```

---

## Step 4 — Open the PR

```bash
gh pr create \
  --base develop \
  --title "feat(exporter): add JSON export with inter-rater scores" \
  --body "$(cat .github/PULL_REQUEST_TEMPLATE/feature.md)"
```

**PR description (filled in):**

---

### Summary

Adds a `to_json()` method to `ReviewExporter` that outputs a structured JSON file following the SegReview schema discussed in #34.

CSV export is unchanged — this is fully backwards compatible. The JSON format includes per-segment verdicts plus aggregate stats (accepted/rejected/flagged counts).

Closes #34

### How to test

1. `pip install -r requirements-dev.txt`
2. `pytest src/tests/test_exporter.py -v`
3. Run the snippet in `docs/exporter_example.py` and inspect `review_case_001.json`

### Checklist

- [x] Tests added / updated
- [x] Docstrings updated
- [x] CHANGELOG entry added
- [x] No patient data committed
- [x] CI passes locally

---

## Step 5 — Review comments received

**Reviewer: `p.bakker`**

> `[blocker]` Line 78: `export_json()` will raise `IndexError` if `results` is an empty list. Please add a guard + a test.

> `[nit]` Variable `d` on line 92 could be `review_data` — easier to scan.

---

## Step 6 — Address feedback

```bash
# Fix the IndexError guard + rename variable
git add src/segmentation_review/exporter.py
git commit --fixup e7a1c3f
# → creates "fixup! feat(exporter): add JSON export with inter-rater scores"

# Add the missing test
git add src/tests/test_exporter.py
git commit --fixup 9c44d81
# → creates "fixup! test(exporter): add full test suite for JSON export"

# Clean up with autosquash
git rebase -i --autosquash origin/develop
git push --force-with-lease
```

The reviewer re-approves. CI is green.

---

## Step 7 — Merge

Merged via **Squash and merge** on GitHub.  
Result on `develop`:

```
* a1b2c3d (develop) feat(exporter): add JSON export with inter-rater scores (#38)
```

One clean commit summarising the whole feature.

---

## What to take from this example

| Practice | Why |
|---|---|
| Small, atomic commits | Easier to review, revert, and `git bisect` |
| `--fixup` + `--autosquash` | Keeps review feedback clean without polluting history |
| Force-push with `--force-with-lease` | Safe way to update a feature branch after rebase |
| Squash on merge | `develop` history stays readable — one commit per feature |
