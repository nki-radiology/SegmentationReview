# Module 4 — Commit Conventions & Writing Good Commits with LLMs

---

## Why commit messages matter

A good commit message is a **letter to your future colleague** (often yourself in six months).

```bash
# Bad history
git log --oneline
e7a1c3f fix stuff
b2d9f0a wip
9c44d81 update
3a71bce changes

# Good history
git log --oneline
e7a1c3f fix(review): replace bare except with specific exception handling
b2d9f0a docs(review): add docstring to _is_valid_extension
9c44d81 refactor(review): simplify joinpath using pathlib
3a71bce feat(review): add _get_reviewed_count helper method
```

---

## Conventional Commits

Format: `type(scope): short description`

| Type | When to use |
|---|---|
| `feat` | New feature visible to the user |
| `fix` | Bug fix |
| `refactor` | Restructuring without behaviour change |
| `test` | Adding or fixing tests |
| `docs` | Documentation only |
| `chore` | CI, build, deps — nothing end-user-visible |
| `perf` | Performance improvement |
| `style` | Formatting, whitespace — no logic change |

### Scopes for this repo

`review`, `loader`, `ui`, `ci`, `deps`, `tutorial`, `release`

### Full message structure

```
fix(review): replace bare except with specific exception handling

The bare `except:` in overwrite_mask_clicked silently swallowed all
errors including KeyboardInterrupt. Narrowing to `except Exception`
makes the intent explicit and avoids masking unexpected failures.

Closes #17
```

### Rules

1. Subject line ≤ 72 characters
2. Imperative mood: "add" not "added", "fix" not "fixed"
3. Blank line between subject and body
4. Body explains **why**, not *what* (the diff already shows what)
5. Reference issues with `Closes #42` or `Related to #17`

---

## Atomic commits

One commit = one logical change. Don't mix a docstring addition with a refactor.

```bash
# Stage only the docstring change
git add -p SegmentationReview/SegmentationReview.py
git commit -m "docs(review): add docstring to _is_valid_extension"

# Then commit the refactor separately
git add -p SegmentationReview/SegmentationReview.py
git commit -m "refactor(review): simplify _construct_full_path using pathlib"
```

**`git add -p`** lets you stage individual hunks within a file — essential for keeping commits clean.

---

## Using LLMs to write commit messages

LLMs are excellent first-draft generators. Workflow:

### Step 1 — Get the diff

```bash
git diff --staged
```

### Step 2 — Prompt your LLM

```
You are a senior software engineer. Write a Git commit message in
Conventional Commits format for the diff below.

Rules:
- Format: type(scope): description
- Types: feat | fix | refactor | test | docs | chore | perf | style
- Scope: one of: review | loader | ui | ci | deps | tutorial | release
- Subject line ≤ 72 chars, imperative mood ("add" not "added")
- Blank line, then body explaining WHY (not what — the diff shows that)
- If multiple logical changes are mixed in the diff, note that the author
  should consider splitting into separate commits

<paste diff here>
```

### Step 3 — Review and own it

The LLM output is a starting point. You must:
- Verify the type and scope are correct
- Add context the LLM couldn't know (linked issue, design decision)
- Delete hallucinated issue numbers

See [`AGENT_GUIDE.md`](../AGENT_GUIDE.md) for a worked example with real output from this codebase.

---

## Exercise

See [08_exercises.md — Exercise A, step 3](08_exercises.md#exercise-a-first-feature-branch).

---

Next → [05_pull_requests.md](05_pull_requests.md)
