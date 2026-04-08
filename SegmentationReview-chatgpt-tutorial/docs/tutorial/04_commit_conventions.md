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
e7a1c3f feat(exporter): add JSON export with inter-rater scores
b2d9f0a test(exporter): add edge-case tests for empty segment list
9c44d81 fix(loader): handle missing orientation matrix in NIfTI headers
3a71bce feat(loader): initial NIfTI support via SimpleITK
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

### Full message structure

```
feat(exporter): add JSON export with inter-rater scores

Previously the only export format was CSV. Downstream Python pipelines
require JSON, and the inter-rater agreement score was not included at all.

The new format follows the draft SegReview schema discussed in #34.
CSV export is unchanged — this is fully backwards compatible.

Closes #34
Co-authored-by: Jan de Vries <j.devries@example.com>
```

### Rules

1. Subject line ≤ 72 characters
2. Imperative mood: "add" not "added", "fix" not "fixed"
3. Blank line between subject and body
4. Body explains *why*, not *what* (the diff already shows what)
5. Reference issues with `Closes #42` or `Related to #17`

---

## Atomic commits

One commit = one logical change. Don't mix a bug fix with a refactor.

```bash
# Stage only the bugfix file
git add src/segmentation_review/loader.py
git commit -m "fix(loader): handle missing orientation matrix"

# Then commit the refactor separately
git add src/segmentation_review/exporter.py
git commit -m "refactor(exporter): extract format logic into strategy classes"
```

**`git add -p`** is your friend — it lets you stage individual hunks within a file.

---

## Using LLMs to write commit messages

LLMs are excellent first-draft generators for commit messages. Here's a workflow:

### Step 1 — Get the diff

```bash
# Diff of staged changes
git diff --staged

# Or pipe into clipboard (macOS)
git diff --staged | pbcopy
```

### Step 2 — Prompt your LLM

```
You are a senior software engineer. Write a Git commit message in
Conventional Commits format for the diff below.

Rules:
- Format: type(scope): description
- Types: feat | fix | refactor | test | docs | chore | perf | style
- Subject line ≤ 72 chars, imperative mood ("add" not "added")
- Blank line, then a body explaining WHY (not what — the diff shows that)
- Reference issue numbers if you see them in the diff context
- If multiple logical changes are in the diff, note that the author
  should consider splitting into separate commits

<paste diff here>
```

### Step 3 — Review and own it

The LLM output is a starting point. You must:
- Verify the type and scope are correct
- Adjust the subject line to match your team's conventions
- Add any context the LLM couldn't know (linked issue, design decision)

### Example LLM output (good)

```
feat(exporter): add JSON export format for review summaries

The CSV format is insufficient for downstream ML pipelines that expect
structured nested data. JSON allows embedding per-segment comments
directly in the output object rather than flattening them.

Closes #34
```

### Example LLM output (needs editing)

```
fix: Updated the loader to not crash when the file is missing
```
Problems: no scope, past tense, too vague. Edit to:
```
fix(loader): prevent crash on missing NIfTI orientation matrix

SimpleITK raises KeyError when GetDirection() is called on files
exported without the standard orientation metadata. Added a fallback
to identity matrix with a warning log.

Closes #41
```

---

## Commit message linting with commitlint

We use `commitlint` in CI to enforce conventions automatically.  
See [07_ci_github_actions.md](07_ci_github_actions.md) for the config.

---

## Exercise

See [08_exercises.md — Exercise 4](08_exercises.md#exercise-4-writing-good-commits).

---

Next → [05_pull_requests.md](05_pull_requests.md)
