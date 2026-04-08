# Module 7 — GitHub Actions & CI

Every PR in this repo must pass automated checks before it can be merged.  
The checks are defined as **GitHub Actions workflows** in `.github/workflows/`.

---

## What runs on every PR?

| Check | Tool | What it catches |
|---|---|---|
| Linting | `ruff` | Style, unused imports, bad patterns |
| Formatting | `black` | Inconsistent formatting |
| Type checking | `mypy` | Type annotation violations |
| Unit tests | `pytest` | Regressions |
| Commit message | `commitlint` | Non-conventional commit messages |

---

## The CI workflow file

See `.github/workflows/ci.yml` in this repo. Key concepts:

```yaml
on:
  pull_request:
    branches: [develop, main]   # Run on PRs targeting these branches
  push:
    branches: [develop]         # Also run on direct pushes to develop
```

### Matrix builds

```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.11"]
```

This runs the job twice — once per Python version.

### Caching dependencies

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}
```

Speeds up builds by reusing previously installed packages.

---

## Branch protection rules

On GitHub, go to **Settings → Branches → Branch protection rules** and set for `develop`:

- ✅ Require a pull request before merging
- ✅ Require status checks to pass: `test`, `lint`, `commitlint`
- ✅ Require at least 1 approving review
- ✅ Dismiss stale reviews when new commits are pushed
- ✅ Require branches to be up to date before merging

This means you literally **cannot** merge a PR that fails CI or hasn't been reviewed.

---

## Running checks locally before pushing

Don't wait for CI — run checks locally first:

```bash
# Install dev deps
pip install -r requirements-dev.txt

# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Tests with coverage
pytest --cov=segmentation_review --cov-report=term-missing

# Check your last commit message
echo "$(git log -1 --pretty=%s)" | npx commitlint
```

Or run everything at once with our helper script:

```bash
./scripts/check.sh
```

---

## Reading CI failures

When CI fails on your PR:

1. Click **Details** next to the failing check
2. Expand the failed step to see the exact error
3. Fix locally, commit (use `--fixup` if appropriate), push
4. CI reruns automatically

Common fixes:

| Error | Fix |
|---|---|
| `black: would reformat` | Run `black src/ tests/` |
| `ruff: F401 unused import` | Remove the unused import |
| `mypy: error` | Fix the type annotation |
| `pytest: FAILED` | Fix the broken test or the code |
| `commitlint: subject may not be empty` | Follow Conventional Commits format |

---

## Exercise

See [08_exercises.md — Exercise 7](08_exercises.md#exercise-7-fix-a-ci-failure).

---

Next → [08_exercises.md](08_exercises.md)
