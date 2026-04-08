# Module 7 — CI / GitHub Actions

GitHub Actions runs automated checks on every PR. This module explains what our CI does and how to work with it.

---

## What CI does for us

Every PR targeting `develop` or `main` triggers:

| Check | Tool | What it catches |
|---|---|---|
| **Commit message lint** | `commitlint` | Non-conventional commit messages |
| **Code formatting** | `black` | Style inconsistencies |
| **Linting** | `ruff` | Unused imports, undefined names, buggy patterns |
| **Type checking** | `mypy` | Type errors |
| **Tests** | `pytest` | Regressions |

CI runs on Python 3.9 and 3.11 to catch version-specific issues.

---

## The workflow file

Our CI lives in `.github/workflows/ci.yml`. Each job is independent — a lint failure doesn't block tests from running.

```yaml
on:
  pull_request:
    branches: [develop, main]
  push:
    branches: [develop]
```

This means CI runs on every PR and on every push directly to `develop`.

---

## Reading a CI failure

1. Go to your PR on GitHub
2. Scroll to the **Checks** section at the bottom
3. Click **Details** next to the failing job
4. Read the log — the error is almost always at the bottom

Common failures:

```
# commitlint failure
✖ type may not be empty [type-empty]
⧗ input: "added docstring"
→ Fix: git rebase -i HEAD~1, reword to "docs(review): add docstring to joinpath"

# ruff failure
SegmentationReview/SegmentationReview.py:3:8: F811 Redefinition of unused `logging`
→ Fix: remove the duplicate import on line 14
```

---

## Fixing a CI failure locally

```bash
# After pushing a commit that breaks CI:

# 1. Fix the issue locally
# (edit the file)

# 2. Create a fixup commit
git add SegmentationReview/SegmentationReview.py
git commit --fixup HEAD

# 3. Squash it into the previous commit
git rebase -i --autosquash HEAD~2

# 4. Force-push (safe version)
git push --force-with-lease origin feature/your-branch
```

---

## Commitlint in detail

Our `commitlint.config.js` enforces:
- Valid type (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `perf`)
- Valid scope (`review`, `loader`, `ui`, `ci`, `deps`, `tutorial`, `release`)
- Subject line ≤ 72 characters
- Lowercase subject

Commitlint only runs on PRs (it checks the commits between your branch head and the base).

---

## Running checks locally before pushing

```bash
# Run all checks at once
./scripts/check.sh
```

This runs the same checks as CI so you catch failures before the push.

---

## Exercise

See [08_exercises.md — Exercise B, step 2](08_exercises.md#exercise-b-second-commit-and-ci).

---

Next → [08_exercises.md](08_exercises.md)
